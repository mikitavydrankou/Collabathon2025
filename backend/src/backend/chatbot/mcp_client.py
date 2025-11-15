"""
Client for calling MCP server tools via HTTP API.
"""

import os
from decimal import Decimal
from typing import Optional

import httpx
from pydantic import BaseModel, Field


# MCP Server URL from environment or default
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001")


# Response schemas matching mcp_server/schemas.py
class TransactionContext(BaseModel):
    recipient_name: str
    bank_account: str
    amount: Decimal
    title: str
    transaction_date: str
    temporal_label: Optional[str] = None


class FirstSuggestionOutput(BaseModel):
    transactions: list[TransactionContext]
    user_balance: Decimal
    total_transactions_count: int


class FilterSuggestionOutput(BaseModel):
    matched_transactions: list[TransactionContext]
    filters_applied: dict
    match_count: int


class FinalCheckOutput(BaseModel):
    is_ok: bool
    problems: list[str] = Field(default_factory=list)
    user_balance: Decimal
    amount_to_send: Decimal


class MCPClient:
    """Client for interacting with MCP server tools via HTTP API on port 8001."""

    def __init__(self, base_url: str = MCP_SERVER_URL):
        """
        Initialize MCP client.

        Args:
            base_url: Base URL of MCP server (default: http://localhost:8001)
        """
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)

    def __del__(self):
        """Close HTTP client on cleanup."""
        if hasattr(self, "client"):
            self.client.close()

    @staticmethod
    def get_first_suggestions(user_id: int) -> FirstSuggestionOutput:
        """
        Get initial transaction suggestions.

        Args:
            user_id: User ID

        Returns:
            FirstSuggestionOutput with up to 5 transactions
        """
        client = MCPClient()
        try:
            response = client.client.post(
                f"{client.base_url}/tools/first-suggestion",
                json={"user_id": user_id},
            )
            response.raise_for_status()
            return FirstSuggestionOutput(**response.json())
        except httpx.HTTPError as e:
            raise Exception(f"MCP API error in first_suggestion: {str(e)}")

    @staticmethod
    def filter_suggestions(
        user_id: int,
        recipient_name: Optional[str] = None,
        recipient_bank_account: Optional[str] = None,
        amount: Optional[Decimal] = None,
        title: Optional[str] = None,
        max_number: int = 10,
    ) -> FilterSuggestionOutput:
        """
        Filter past transactions based on partial input.

        Args:
            user_id: User ID
            recipient_name: Optional partial recipient name
            recipient_bank_account: Optional bank account
            amount: Optional amount
            title: Optional title
            max_number: Maximum number of results

        Returns:
            FilterSuggestionOutput with matched transactions
        """
        client = MCPClient()
        try:
            payload = {
                "user_id": user_id,
                "max_number": max_number,
            }
            if recipient_name:
                payload["recipient_name"] = recipient_name
            if recipient_bank_account:
                payload["recipient_bank_account"] = recipient_bank_account
            if amount is not None:
                payload["amount"] = float(amount)
            if title:
                payload["title"] = title

            response = client.client.post(
                f"{client.base_url}/tools/filter-suggestion",
                json=payload,
            )
            response.raise_for_status()
            return FilterSuggestionOutput(**response.json())
        except httpx.HTTPError as e:
            raise Exception(f"MCP API error in filter_suggestion: {str(e)}")

    @staticmethod
    def final_check(
        user_id: int,
        recipient_name: str,
        bank_account: str,
        amount: Decimal,
        title: str,
    ) -> FinalCheckOutput:
        """
        Validate complete transaction data.

        Args:
            user_id: User ID
            recipient_name: Full recipient name
            bank_account: Bank account number
            amount: Transaction amount
            title: Transaction description

        Returns:
            FinalCheckOutput with validation results
        """
        client = MCPClient()
        try:
            response = client.client.post(
                f"{client.base_url}/tools/final-check",
                json={
                    "user_id": user_id,
                    "recipient_name": recipient_name,
                    "bank_account": bank_account,
                    "amount": float(amount),
                    "title": title,
                },
            )
            response.raise_for_status()
            return FinalCheckOutput(**response.json())
        except httpx.HTTPError as e:
            raise Exception(f"MCP API error in final_check: {str(e)}")
