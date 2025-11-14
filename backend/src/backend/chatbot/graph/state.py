from __future__ import annotations

from enum import Enum
from typing import List, Optional, Any

from pydantic import BaseModel, Field

from ..models import MoneyTransferForm, ChatMessage


class Intent(str, Enum):
    """High-level user intent detected by the MainAgent."""

    NONE = "none"
    MONEY_TRANSFER = "money_transfer"


class Step(str, Enum):
    """
    Current step of the flow.
    LangGraph nodes will branch based on this value.
    """

    IDLE = "idle"  # no active flow yet
    INTENT_DETECTED = "intent_detected"  # user wants money transfer
    FETCHING_HISTORY = "fetching_history"  # calling MCP / mock
    SUGGESTING = "suggesting"  # SuggestionAgent building proposal
    CONFIRMING = "confirming"  # user checks pre-filled form
    EDITING = "editing"  # user modifies fields
    VALIDATING = "validating"  # Pydantic validation in progress
    COMPLETED = "completed"  # flow finished successfully
    CANCELLED = "cancelled"  # user cancelled the flow


class ConversationState(BaseModel):
    """
    Shared state object for the whole LangGraph.
    Every node receives and returns this structure.
    """

    # identity
    user_id: str = Field(..., description="Logical user identifier.")
    session_id: Optional[str] = Field(
        default=None, description="Optional session / chat id."
    )

    # dialogue context
    chat_history: List[ChatMessage] = Field(
        default_factory=list,
        description="Full chronologic list of chat messages.",
    )

    # flow status
    current_intent: Intent = Field(
        default=Intent.NONE,
        description="Current intent inferred for this conversation.",
    )
    step: Step = Field(
        default=Step.IDLE,
        description="Current step of the money-transfer flow.",
    )

    # transfer data being built
    form_data: Optional[MoneyTransferForm] = Field(
        default=None,
        description="Current state of the money-transfer form (may be partial).",
    )
    suggestion_source: Optional[str] = Field(
        default=None,
        description="Short note how the suggestion was derived (for logs / UX).",
    )

    # validation / editing
    pending_fields: List[str] = Field(
        default_factory=list,
        description="Field names that still need fixing / filling after validation.",
    )

    # optional helpers
    last_system_summary: Optional[str] = Field(
        default=None,
        description="Short textual summary of state used as context for agents.",
    )
    meta: dict[str, Any] = Field(
        default_factory=dict,
        description="Extra debug / tracing info (not user-visible).",
    )

    def short_summary_for_prompt(self) -> str:
        """
        Build a compact textual summary of the current state
        to embed into prompts instead of dumping raw JSON.
        """
        intent = self.current_intent.value
        step = self.step.value

        if self.form_data:
            recipient = self.form_data.recipient.name
            amount = self.form_data.amount
            currency = self.form_data.currency
            ref = self.form_data.reference_text
            form_part = (
                f"Current form → recipient: {recipient}, "
                f"amount: {amount} {currency}, reference: '{ref}'."
            )
        else:
            form_part = "No transfer form has been filled yet."

        pending = (
            f"Pending fields: {', '.join(self.pending_fields)}."
            if self.pending_fields
            else "No pending fields."
        )

        return f"Intent: {intent}, step: {step}. {form_part} {pending}"
