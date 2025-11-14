from __future__ import annotations

from pathlib import Path
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

from ..models import MoneyTransferForm
from ..agents import FormatterAgentOutput


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


def run_formatter_agent(
    llm: BaseChatModel,
    form: MoneyTransferForm,
    suggestion_source: Optional[str] = None,
) -> FormatterAgentOutput:
    """
    Turn a MoneyTransferForm into a neurodivergent-friendly confirmation
    message that the frontend will show to the user.
    """

    style_guide = _load_style_guide()

    recipient_name = form.recipient.name
    recipient_iban = form.recipient.iban or "<saved account>"
    amount = form.amount
    currency = form.currency
    reference_text = form.reference_text

    system_prompt = f"""
You are a digital banking assistant preparing a confirmation message
for a neurodivergent user. Follow the NEURODIVERGENT STYLE GUIDE.

NEURODIVERGENT STYLE GUIDE:
{style_guide}

You will receive the finalized form fields for a money transfer and you should:
- Present them clearly and calmly.
- Use headings with emojis.
- List each field on its own line with an appropriate icon.
- Ask ONE main question: whether everything is correct or the user wants to change something.
"""

    source_note = (
        f"This suggestion is based on: {suggestion_source}."
        if suggestion_source
        else "This suggestion is based on your past transfers."
    )

    user_prompt = f"""
Here are the form fields for the proposed transfer:

- recipient_name: {recipient_name}
- recipient_iban: {recipient_iban}
- amount: {amount} {currency}
- reference_text: {reference_text}

Additional internal note (you MAY paraphrase for the user if helpful):
{source_note}

Now write the confirmation message for the user.
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    assistant_text = llm.invoke(messages).content

    return FormatterAgentOutput(assistant_text=assistant_text)
