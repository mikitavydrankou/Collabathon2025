from __future__ import annotations

import json
from typing import List

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

from ..graph import ConversationState
from ..models import TransactionRecord, MoneyTransferForm
from . import SuggestionAgentOutput


def run_suggestion_agent(
    llm: BaseChatModel,
    state: ConversationState,
    history: List[TransactionRecord],
) -> SuggestionAgentOutput:
    """
    Build a suggested MoneyTransferForm based on the user's past transactions.
    This agent is INTERNAL ONLY (no user-facing tone needed).
    """

    # Prepare compact description of history for the LLM
    tx_lines = []
    for tx in history:
        tx_lines.append(
            f"- date: {tx.date}, recipient: {tx.recipient_name}, "
            f"iban: {tx.recipient_iban}, amount: {tx.amount} {tx.currency}, "
            f"title: {tx.title}"
        )
    history_text = "\n".join(tx_lines)

    state_summary = state.short_summary_for_prompt()

    system_prompt = f"""
You are an internal reasoning assistant for a banking app.
You do NOT talk to the user directly.

Your task:
- Look at the user's past transactions.
- Choose the single most relevant transaction as a template for a NEW transfer.
- Create a JSON object describing a proposed MoneyTransferForm and an explanation.

CURRENT INTERNAL STATE (for context):
{state_summary}

Past transactions:
{history_text}

You MUST respond with a single JSON object, like:

{{
  "recipient_name": "string",
  "recipient_iban": "string",
  "amount": 123.45,
  "currency": "EUR",
  "reference_text": "string",
  "suggestion_source": "short explanation why you chose this"
}}

Rules:
- Prefer recent recurring-like payments (e.g., rent, utilities) if the user's intent sounds similar.
- If unsure, pick the most recent transaction.
"""

    # You could optionally pass last few user messages too
    user_prompt = "Build the best suggestion according to the rules above."

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    raw_response = llm.invoke(messages).content

    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError:
        # Fallback: if parsing fails, just use the most recent transaction
        base_tx = history[0]
        form = base_tx.to_transfer_form()
        return SuggestionAgentOutput(
            form=form,
            suggestion_source="fallback_to_most_recent_transaction",
        )

    recipient_name = data.get("recipient_name")
    recipient_iban = data.get("recipient_iban")
    amount = float(data.get("amount"))
    currency = data.get("currency", "EUR")
    reference_text = data.get("reference_text", "")

    form = MoneyTransferForm(
        recipient={"name": recipient_name, "iban": recipient_iban},
        amount=amount,
        currency=currency,
        reference_text=reference_text,
    )

    suggestion_source = data.get(
        "suggestion_source",
        "suggestion_based_on_past_transactions",
    )

    return SuggestionAgentOutput(form=form, suggestion_source=suggestion_source)