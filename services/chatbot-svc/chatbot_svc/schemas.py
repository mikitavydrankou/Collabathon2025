"""
Pydantic schemas for chatbot state and API requests/responses.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatbotStage(str, Enum):
    """Stages of the chatbot workflow."""

    INITIAL = "initial"  # Want suggestion? yes/no
    FIRST_SUGGESTION = "first_suggestion"  # Showing first suggestion
    COLLECTING_FIELD_1 = "collecting_field_1"  # Collecting recipient account
    COLLECTING_FIELD_2 = "collecting_field_2"  # Collecting full name
    COLLECTING_FIELD_3 = "collecting_field_3"  # Collecting amount
    COLLECTING_FIELD_4 = "collecting_field_4"  # Collecting transaction text
    FILTER_SUGGESTION = "filter_suggestion"  # Showing filter suggestion
    FINAL_CHECK = "final_check"  # Validation problems
    COMPLETED = "completed"  # Ready for payment


class TransactionData(BaseModel):
    """Collected transaction data."""

    recipient_account: Optional[str] = None
    recipient_name: Optional[str] = None
    amount: Optional[Decimal] = None
    transaction_text: Optional[str] = None


class ChatbotState(BaseModel):
    """State of a chatbot conversation session."""

    session_id: str = Field(..., description="Unique session identifier")
    user_id: int = Field(..., description="User ID")
    stage: ChatbotStage = Field(default=ChatbotStage.INITIAL)
    transaction_data: TransactionData = Field(default_factory=TransactionData)
    first_suggestion: Optional["SuggestionInfo"] = Field(default=None, description="First suggestion shown to user (to avoid duplicates)")
    current_filter_suggestion: Optional["SuggestionInfo"] = Field(default=None, description="Current filter suggestion (for change_to_suggested action)")
    filter_suggestion_shown: bool = Field(default=False, description="Whether filter suggestion was already shown")
    awaiting_problem_response: bool = Field(default=False, description="Whether waiting for user to respond to validation problems")
    validation_problems: List[str] = Field(default_factory=list, description="Current validation problems")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChatbotMessageRequest(BaseModel):
    """Request for chatbot message."""

    session_id: Optional[str] = Field(None, description="Session ID (optional for first message)")
    user_id: int = Field(..., description="User ID")
    message: Optional[str] = Field(None, description="User's text message")
    action: Optional[str] = Field(None, description="Button action (yes/no/accept/decline)")


class SuggestionInfo(BaseModel):
    """Information about a transaction suggestion."""

    recipient_name: str
    bank_account: str
    amount: float
    title: str
    confidence: Optional[float] = None
    reason: Optional[str] = None


class ChatbotMessageResponse(BaseModel):
    """Response from chatbot."""

    session_id: str
    stage: ChatbotStage
    message: str = Field(..., description="Message to display to user")
    buttons: Optional[List[str]] = Field(None, description="Button options (e.g., ['show_me', 'not_now'])")
    button_helper_text: Optional[str] = Field(None, description="Helper text to show under buttons")
    suggestion: Optional[SuggestionInfo] = Field(None, description="Transaction suggestion if any")
    transaction_data: Optional[TransactionData] = Field(None, description="Current collected data")
    show_confirm_payment: bool = Field(default=False, description="Whether to show confirm payment button")
    validation_problems: Optional[List[str]] = Field(None, description="Validation problems if any")


class StartChatRequest(BaseModel):
    """Request to start a new chat session."""

    user_id: int = Field(..., description="User ID")


class StartChatResponse(BaseModel):
    """Response for starting a new chat session."""

    session_id: str
    message: str
    buttons: List[str]
    button_helper_text: Optional[str] = None
