"""
Pydantic schemas for MCP tool inputs and outputs.

All outputs are designed for LLM consumption - structured data with context.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

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
    recipient_bank_account: Optional[str] = Field(
        None, description="Recipient bank account number"
    )
    amount: Optional[Decimal] = Field(None, description="Transaction amount to match")
    title: Optional[str] = Field(None, description="Partial or full payment title")
    max_number: Optional[int] = Field(
        10, description="Maximum number of transactions to return (default: 10)"
    )

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Ensure amount has at most 2 decimal places if provided."""
        if v is not None:
            return round(v, 2)
        return v

    @field_validator("max_number")
    @classmethod
    def validate_max_number(cls, v: Optional[int]) -> int:
        """Ensure max_number is positive and reasonable."""
        if v is None:
            return 10
        if v < 1:
            raise ValueError("max_number must be at least 1")
        if v > 100:
            raise ValueError("max_number cannot exceed 100")
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


class SQLQueryInput(BaseModel):
    """Input for sql_query_tool."""

    user_id: int = Field(..., description="ID of the user making the query")
    function_name: str = Field(
        ...,
        description="Name of the SQL function to execute: get_recent_transactions, filter_transactions, get_time_based_transactions, get_recipient_patterns, or get_user_balance",
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Parameters for the SQL function"
    )


class SQLQueryOutput(BaseModel):
    """
    Output for sql_query_tool.

    Returns query results with success status and error information.
    """

    success: bool = Field(..., description="True if query executed successfully")
    data: Optional[Any] = Field(
        None, description="Query results (list of transactions, dict, or other data structure)"
    )
    error: Optional[str] = Field(None, description="Error message if success=False")
    function_used: str = Field(..., description="Name of the function that was executed")


class RAGQueryInput(BaseModel):
    """Input for rag_query_tool."""

    user_id: int = Field(..., description="ID of the user making the query")
    query: str = Field(..., description="Search query text for semantic similarity search")
    top_k: int = Field(
        default=3, description="Number of similar transactions to return (default: 3)"
    )

    @field_validator("top_k")
    @classmethod
    def validate_top_k(cls, v: int) -> int:
        """Ensure top_k is positive and reasonable."""
        if v < 1:
            raise ValueError("top_k must be at least 1")
        if v > 20:
            raise ValueError("top_k cannot exceed 20")
        return v


class RAGQueryOutput(BaseModel):
    """
    Output for rag_query_tool.

    Returns similar transactions with similarity scores.
    """

    success: bool = Field(..., description="True if search executed successfully")
    data: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of similar transactions with similarity scores",
    )
    count: int = Field(..., description="Number of results returned")
    query: str = Field(..., description="Original search query")
    error: Optional[str] = Field(None, description="Error message if success=False")