from __future__ import annotations

import json
from pathlib import Path
from typing import List

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

from ..graph import ConversationState, Intent, Step
from ..models import ChatMessage
from . import MainAgentAction, MainAgentOutput


STYLE_PATH = (
    Path(__file__).resolve().parent.parent / "style" / "neurodiv_style.md"
)


def _load_style_guide() -> str:
    try:
        return STYLE_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return (
            "Use clear headings with emojis, bullet lists, simple language, "
            "and one main question per message. Be calm, patient, and reassuring."
        )


def _build_history_snippet(
    history: List[ChatMessage],
    max_messages: int = 10,
) -> str:
    """
    Convert last N chat messages into a compact text snippet
    for the LLM prompt. We don't dump full JSON to keep prompt light.
    """
    recent = history[-max_messages:]
    lines = []
    for msg in recent:
        who = msg.role.upper()
        lines.append(f"{who}: {msg.content}")
    return "\n".join(lines)


def run_main_agent(
    llm: BaseChatModel,
    state: ConversationState,
    latest_user_message: str,
) -> MainAgentOutput:
    """
    Call the LLM to:
    - understand what the user wants,
    - decide next action (set intent / confirm / edit / cancel),
    - generate a neurodivergent-friendly response text.
    """

    style_guide = _load_style_guide()
    history_snippet = _build_history_snippet(state.chat_history)
    state_summary = state.short_summary_for_prompt()

    system_prompt = f"""
You are a calm, patient digital banking assistant helping a neurodivergent user.
Your job is to:
1) Understand if the user wants to perform a money transfer and at which step they are.
2) Decide a high-level action for the orchestration graph.
3) Generate a short, structured reply that follows the NEURODIVERGENT STYLE GUIDE below.

NEURODIVERGENT STYLE GUIDE:
{style_guide}

CURRENT INTERNAL STATE (for your reasoning, not to repeat verbatim):
{state_summary}

You MUST respond with a single JSON object only, no extra text, in the following format:

{{
  "assistant_text": "string - what I should show to the user",
  "action": "SET_INTENT | CONFIRM_SUGGESTION | EDIT_FIELD | CANCEL | ASK_CLARIFICATION | NONE",
  "intent": "none | money_transfer",
  "field_to_edit": "name_of_field_or_null"
}}

Rules:
- If the user clearly wants to start or continue a money transfer, set intent = "money_transfer".
- If the user says everything is correct with the suggested details, use action = "CONFIRM_SUGGESTION".
- If the user wants to change some detail (e.g. amount, recipient, IBAN, reference), use action = "EDIT_FIELD" and set field_to_edit to a simple name like "amount" or "recipient.iban".
- If the user cancels, use action = "CANCEL".
- Otherwise, ask for clarification with action = "ASK_CLARIFICATION".
"""

    user_prompt = f"""
Here is the recent chat history:

{history_snippet}

The user just wrote:
{latest_user_message}

Remember: only output the JSON object, nothing else.
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    raw_response = llm.invoke(messages).content

    # Try to parse JSON from model response
    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError:
        # Fallback: wrap the raw response as assistant_text
        return MainAgentOutput(
            assistant_text=raw_response,
            action=MainAgentAction.NONE,
            intent=state.current_intent,
        )

    # Map string fields to enums, with safe defaults
    action_str = data.get("action", "NONE")
    try:
        action = MainAgentAction(action_str)
    except ValueError:
        action = MainAgentAction.NONE

    intent_str = data.get("intent", "none")
    intent = Intent.MONEY_TRANSFER if intent_str == "money_transfer" else Intent.NONE

    assistant_text = data.get(
        "assistant_text",
        "I had trouble generating a response. Please try again.",
    )
    field_to_edit = data.get("field_to_edit")

    return MainAgentOutput(
        assistant_text=assistant_text,
        action=action,
        intent=intent,
        field_to_edit=field_to_edit,
    )
