"""
Pydantic schemas for MCP tool inputs and outputs.

All outputs are designed for LLM consumption - structured data with context.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class TransactionContext(BaseModel):
    """Transaction data with temporal context for LLM analysis."""

    recipient_name: str = Field(..., description="Full name of the recipient")
    bank_account: str = Field(..., description="Bank account number")
    amount: Decimal = Field(..., description="Transaction amount")
    title: str = Field(..., description="Payment description/title")
    transaction_date: datetime = Field(..., description="When this transaction occurred")
    temporal_label: Optional[str] = Field(
        None, description="Temporal context: '1_year_ago', '1_month_ago', '1_week_ago', 'recent'"
    )

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Ensure amount has at most 2 decimal places."""
        return round(v, 2)

    class Config:
        json_encoders = {Decimal: lambda v: float(v), datetime: lambda v: v.isoformat()}


class FirstSuggestionInput(BaseModel):
    """Input for first_suggestion_tool."""

    user_id: int = Field(..., description="ID of the user requesting suggestions")


class FirstSuggestionOutput(BaseModel):
    """
    Output for first_suggestion_tool.

    Returns up to 5 transactions with temporal context for LLM to analyze.
    LLM agent will decide which transaction to suggest based on this context.
    """

    transactions: List[TransactionContext] = Field(
        ..., description="List of transactions with temporal labels (max 5)"
    )
    user_balance: Decimal = Field(..., description="Current user balance")
    total_transactions_count: int = Field(
        ..., description="Total number of transactions user has made"
    )


class FilterSuggestionInput(BaseModel):
    """Input for filter_suggestion_tool."""

    user_id: int = Field(..., description="ID of the user requesting suggestions")
    recipient_name: Optional[str] = Field(
        None, description="Partial or full recipient name"
    )
    amount: Optional[Decimal] = Field(None, description="Transaction amount to match")
    title: Optional[str] = Field(None, description="Partial or full payment title")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Ensure amount has at most 2 decimal places if provided."""
        if v is not None:
            return round(v, 2)
        return v


class FilterSuggestionOutput(BaseModel):
    """
    Output for filter_suggestion_tool.

    Returns matching transactions with frequency data for LLM to rank/suggest.
    """

    matched_transactions: List[TransactionContext] = Field(
        ..., description="Transactions matching the filter criteria"
    )
    filters_applied: dict = Field(
        ..., description="Which filters were used (for LLM context)"
    )
    match_count: int = Field(..., description="Total number of matches found")


class FinalCheckInput(BaseModel):
    """Input for final_check_tool."""

    user_id: int = Field(..., description="ID of the user making the payment")
    recipient_name: str = Field(..., description="Full name of the recipient")
    bank_account: str = Field(..., description="Bank account number")
    amount: Decimal = Field(..., description="Transaction amount")
    title: str = Field(..., description="Payment description/title")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Ensure amount has at most 2 decimal places."""
        return round(v, 2)

    @field_validator("recipient_name", "title")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class FinalCheckOutput(BaseModel):
    """
    Output for final_check_tool.

    Simple validation output: OK or list of problems.
    """

    is_ok: bool = Field(..., description="True if transaction can proceed, False if there are problems")
    problems: List[str] = Field(
        default_factory=list, description="List of problems (empty if is_ok=True)"
    )
    user_balance: Decimal = Field(..., description="Current user balance for context")
    amount_to_send: Decimal = Field(..., description="Amount being validated")
