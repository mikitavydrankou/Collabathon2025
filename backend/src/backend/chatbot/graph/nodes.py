from __future__ import annotations

from typing import List

from langchain_core.language_models import BaseChatModel

from .state import ConversationState, Intent, Step
from ..models import ChatMessage, TransactionRecord
from ..mcp.mock_client import get_transaction_history
from ..services import validate_transfer_form
from ..agents import (
    MainAgentAction,
    MainAgentOutput,
    SuggestionAgentOutput,
    FormatterAgentOutput,
)
from ..agents.main_agent import run_main_agent
from ..agents.suggestion_agent import run_suggestion_agent
from ..agents.formatter_agent import run_formatter_agent


# -------------------------
# Helper: get latest user msg
# -------------------------


def _get_latest_user_message(state: ConversationState) -> str:
    """
    Assumption:
      - FastAPI / caller appends the latest user message to state.chat_history
        BEFORE invoking the graph.
      - The last message in chat_history is therefore from the user.

    If this isn't true (e.g. empty history), we fallback to empty string.
    """
    if not state.chat_history:
        return ""
    last = state.chat_history[-1]
    if last.role != "user":
        # In edge cases, scan backwards for the last user message.
        for msg in reversed(state.chat_history):
            if msg.role == "user":
                return msg.content
        return ""
    return last.content


# -------------------------
# Node: Main Agent
# -------------------------


def main_agent_node(
    state: ConversationState,
    llm_main: BaseChatModel,
) -> ConversationState:
    """
    Node that calls the MainAgent.

    Responsibilities:
    - Understand the latest user message in context.
    - Decide high-level action (set intent, confirm suggestion, edit, cancel).
    - Generate a neurodivergent-friendly assistant message.
    - Update state.current_intent and state.step at a high level.
    - Store the assistant message in chat_history and meta["last_assistant_text"].

    Routing based on MainAgentAction will be done in the graph builder
    using `state.step` and possibly `state.meta["last_main_action"]`.
    """

    latest_user_message = _get_latest_user_message(state)

    main_output: MainAgentOutput = run_main_agent(
        llm=llm_main,
        state=state,
        latest_user_message=latest_user_message,
    )

    # Update intent
    if main_output.intent == Intent.MONEY_TRANSFER:
        state.current_intent = Intent.MONEY_TRANSFER

    # Update step based on action
    action = main_output.action
    state.meta["last_main_action"] = action.value

    if action == MainAgentAction.SET_INTENT:
        if state.current_intent == Intent.MONEY_TRANSFER:
            state.step = Step.INTENT_DETECTED

    elif action == MainAgentAction.CONFIRM_SUGGESTION:
        # User says "everything correct" → go to validation
        state.step = Step.VALIDATING

    elif action == MainAgentAction.EDIT_FIELD:
        # Mark that we are in an editing phase.
        # The exact new values will be collected in subsequent turns.
        state.step = Step.EDITING
        if main_output.field_to_edit:
            state.meta["field_to_edit"] = main_output.field_to_edit

    elif action == MainAgentAction.CANCEL:
        state.step = Step.CANCELLED

    elif action == MainAgentAction.ASK_CLARIFICATION:
        # Stay on current step; we just asked a clarifying question.
        pass

    # Append assistant message to history
    assistant_msg = ChatMessage(role="assistant", content=main_output.assistant_text)
    state.chat_history.append(assistant_msg)

    # Remember last user-visible message for the API layer
    state.meta["last_assistant_text"] = main_output.assistant_text

    # Optionally, store a short summary for future prompts
    state.last_system_summary = state.short_summary_for_prompt()

    return state


# -------------------------
# Node: Fetch history (MCP mock)
# -------------------------


def fetch_history_node(state: ConversationState) -> ConversationState:
    """
    Node that fetches past transactions from MCP (here: mock client).

    - Uses state.user_id.
    - Stores list[TransactionRecord] in state.meta["tx_history"].
    - Sets step to SUGGESTING.
    """

    tx_history: List[TransactionRecord] = get_transaction_history(state.user_id)
    state.meta["tx_history"] = [tx.model_dump() for tx in tx_history]

    state.step = Step.SUGGESTING
    state.last_system_summary = state.short_summary_for_prompt()
    return state


# -------------------------
# Node: Suggestion Agent
# -------------------------


def suggestion_node(
    state: ConversationState,
    llm_suggestion: BaseChatModel,
) -> ConversationState:
    """
    Node that calls SuggestionAgent to build a proposed MoneyTransferForm.

    - Reads tx_history from state.meta["tx_history"].
    - Writes the proposed form to state.form_data.
    - Writes suggestion_source to state.suggestion_source.
    - Sets step to CONFIRMING.
    """

    raw_history = state.meta.get("tx_history", [])
    tx_history: List[TransactionRecord] = [
        TransactionRecord.model_validate(h) for h in raw_history
    ]

    if not tx_history:
        # Defensive: if for some reason we have no history, we just stay as-is.
        # In a real system we might fall back to manual data collection.
        state.meta["suggestion_error"] = "no_history_available"
        return state

    suggestion_output: SuggestionAgentOutput = run_suggestion_agent(
        llm=llm_suggestion,
        state=state,
        history=tx_history,
    )

    state.form_data = suggestion_output.form
    state.suggestion_source = suggestion_output.suggestion_source
    state.step = Step.CONFIRMING

    state.last_system_summary = state.short_summary_for_prompt()
    return state


# -------------------------
# Node: Formatter Agent
# -------------------------


def formatter_node(
    state: ConversationState,
    llm_formatter: BaseChatModel,
) -> ConversationState:
    """
    Node that calls FormatterAgent to produce a user-visible confirmation message
    based on the suggested MoneyTransferForm.
    """

    if state.form_data is None:
        # Nothing to format – leave state unchanged.
        state.meta["formatter_error"] = "no_form_data"
        return state

    formatter_output: FormatterAgentOutput = run_formatter_agent(
        llm=llm_formatter,
        form=state.form_data,
        suggestion_source=state.suggestion_source,
    )

    assistant_text = formatter_output.assistant_text

    # Append to chat history
    assistant_msg = ChatMessage(role="assistant", content=assistant_text)
    state.chat_history.append(assistant_msg)

    # Remember last message for API layer
    state.meta["last_assistant_text"] = assistant_text

    # Step remains CONFIRMING – we are waiting for user to say OK or change something
    state.step = Step.CONFIRMING
    state.last_system_summary = state.short_summary_for_prompt()

    return state


# -------------------------
# Node: Validation
# -------------------------


def validation_node(state: ConversationState) -> ConversationState:
    """
    Node that validates the current MoneyTransferForm.

    - Uses Pydantic via validate_transfer_form.
    - On success: clears pending_fields, sets step = COMPLETED.
    - On failure: fills pending_fields, sets step = EDITING,
      and stores raw error messages in state.meta["validation_errors"].
    """

    if state.form_data is None:
        # No form to validate – treat as error and stay in current step.
        state.meta["validation_error"] = "no_form_data"
        return state

    is_valid, pending_fields, error_messages = validate_transfer_form(state.form_data)

    if is_valid:
        state.pending_fields = []
        state.meta["validation_errors"] = []
        state.step = Step.COMPLETED
    else:
        state.pending_fields = pending_fields
        state.meta["validation_errors"] = error_messages
        # We will ask the user to correct specific fields.
        state.step = Step.EDITING

    state.last_system_summary = state.short_summary_for_prompt()
    return state


# -------------------------
# Node: Completion (summary for the user)
# -------------------------


def completion_node(state: ConversationState) -> ConversationState:
    """
    Node that generates a final deterministic summary for the user
    after a successful validation.

    For the hackathon PoC we don't actually execute the transfer,
    we just explain what *would* be done in a real app.
    """

    if state.form_data is None:
        # Nothing to summarize.
        state.meta["completion_error"] = "no_form_data"
        return state

    recipient_name = state.form_data.recipient.name
    recipient_iban = state.form_data.recipient.iban or "<saved account>"
    amount = state.form_data.amount
    currency = state.form_data.currency
    reference_text = state.form_data.reference_text

    summary_text = f"""🔍 What we have prepared

📋 Details of your transfer:
👤 **Recipient**: {recipient_name}
🏦 **Account number (IBAN)**: {recipient_iban}
💰 **Amount**: {amount} {currency}
📝 **Reference**: "{reference_text}"

👉 In a real banking app, the next step would be a strong confirmation,
   for example using photoTAN or another secure method.
   In this demo, we stop here and treat this transfer as 'simulated'.

If you want, you can start another transfer or ask me to explain any detail again.
"""

    assistant_msg = ChatMessage(role="assistant", content=summary_text)
    state.chat_history.append(assistant_msg)
    state.meta["last_assistant_text"] = summary_text

    state.step = Step.COMPLETED
    state.last_system_summary = state.short_summary_for_prompt()

    return state