from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel

from ..graph import ConversationState, Intent
from ..models import MoneyTransferForm, TransactionRecord


class MainAgentAction(str, Enum):
    """High-level actions that MainAgent can request."""

    NONE = "none"
    SET_INTENT = "set_intent"
    CONFIRM_SUGGESTION = "confirm_suggestion"
    EDIT_FIELD = "edit_field"
    CANCEL = "cancel"
    ASK_CLARIFICATION = "ask_clarification"


class MainAgentOutput(BaseModel):
    """
    Parsed, structured output from MainAgent.
    Used by graph nodes to decide what to do next.
    """

    assistant_text: str
    action: MainAgentAction = MainAgentAction.NONE
    intent: Intent = Intent.NONE
    field_to_edit: Optional[str] = None


class SuggestionAgentOutput(BaseModel):
    """
    Output of SuggestionAgent: suggested transfer form + explanation
    (explanation for logs / UX, not directly user-facing).
    """

    form: MoneyTransferForm
    suggestion_source: str


class FormatterAgentOutput(BaseModel):
    """Output of FormatterAgent: final user-visible message."""

    assistant_text: str


__all__ = [
    "MainAgentAction",
    "MainAgentOutput",
    "SuggestionAgentOutput",
    "FormatterAgentOutput",
    "ConversationState",
    "Intent",
    "MoneyTransferForm",
    "TransactionRecord",
]