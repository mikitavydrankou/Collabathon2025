"""
MCP tool implementations for money transfer assistance.

These tools provide structured data and insights for LLM agents to analyze and make decisions.
All outputs are designed for LLM consumption, not direct UI display.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from backend.models import Transaction, User

from .database import (
    filter_transactions,
    get_account_patterns,
    get_db,
    get_recent_transactions,
    get_recipient_patterns,
    get_time_based_transactions,
    get_user_balance,
)
from .schemas import (
    FilterSuggestionInput,
    FilterSuggestionOutput,
    FinalCheckInput,
    FinalCheckOutput,
    FirstSuggestionInput,
    FirstSuggestionOutput,
    TransactionContext,
)


def _transaction_to_context(
    transaction: Transaction, db: Session, temporal_label: Optional[str] = None
) -> TransactionContext:
    """
    Convert a Transaction model to TransactionContext.

    Args:
        transaction: Transaction database model
        db: Database session to look up receiver details
        temporal_label: Optional temporal label

    Returns:
        TransactionContext with all required fields
    """
    # Get receiver's bank account
    receiver = db.query(User).filter(User.user_id == transaction.receiver_id).first()
    bank_account = receiver.bank_number if receiver else "Unknown"

    return TransactionContext(
        recipient_name=f"{transaction.receiver_name} {transaction.receiver_surname}",
        bank_account=bank_account,
        amount=transaction.amount,
        title=transaction.transaction_text or "No description",
        transaction_date=transaction.transaction_date_and_time,
        temporal_label=temporal_label,
    )


def first_suggestion_tool(input_data: FirstSuggestionInput) -> FirstSuggestionOutput:
    """
    Provide up to 5 transactions with temporal context for LLM analysis.

    Returns:
    - 1 random transaction from ~1 year ago (if exists)
    - 1 random transaction from ~1 month ago (if exists)
    - 1 random transaction from ~1 week ago (if exists)
    - Last 2 recent transactions

    LLM agent will analyze this data and decide which transaction to suggest
    based on temporal patterns (e.g., "1 month ago + electricity bill").

    Args:
        input_data: Contains user_id

    Returns:
        FirstSuggestionOutput with transactions, balance, and transaction count
    """
    db = get_db()
    try:
        transactions: List[TransactionContext] = []
        seen_combinations = set()  # Track unique (name, account) pairs

        # Get time-based transactions (year, month, week ago)
        time_based = get_time_based_transactions(db, input_data.user_id)
        temporal_map = {
            "about a year ago": "1_year_ago",
            "about a month ago": "1_month_ago",
            "about a week ago": "1_week_ago",
        }

        for transaction, time_label in time_based:
            context = _transaction_to_context(
                transaction, db, temporal_map.get(time_label, time_label)
            )
            key = (context.recipient_name, context.bank_account)
            if key not in seen_combinations:
                transactions.append(context)
                seen_combinations.add(key)

        # Get the 2 most recent transactions
        recent = get_recent_transactions(db, input_data.user_id, limit=2)
        for transaction in recent:
            context = _transaction_to_context(transaction, db, "recent")
            key = (context.recipient_name, context.bank_account)
            if key not in seen_combinations:
                transactions.append(context)
                seen_combinations.add(key)

        # Get user balance
        balance = get_user_balance(db, input_data.user_id) or Decimal("0.00")

        # Get total transaction count
        total_count = (
            db.query(Transaction)
            .filter(Transaction.sender_id == input_data.user_id)
            .filter(Transaction.transaction_posted == True)
            .count()
        )

        return FirstSuggestionOutput(
            transactions=transactions, user_balance=balance, total_transactions_count=total_count
        )

    finally:
        db.close()


def filter_suggestion_tool(
    input_data: FilterSuggestionInput,
) -> FilterSuggestionOutput:
    """
    Filter past transactions based on partial user input and return matches for LLM ranking.

    LLM agent will analyze matched transactions and decide which ones to present
    and in what order based on relevance to the user's partial input.

    Args:
        input_data: Contains user_id and optional filter criteria

    Returns:
        FilterSuggestionOutput with matched transactions and filter context
    """
    db = get_db()
    try:
        # Build filters_applied context for LLM
        filters_applied = {}
        if input_data.recipient_name:
            filters_applied["recipient_name"] = input_data.recipient_name
        if input_data.amount is not None:
            filters_applied["amount"] = float(input_data.amount)
        if input_data.title:
            filters_applied["title"] = input_data.title

        # Filter transactions
        filtered = filter_transactions(
            db,
            input_data.user_id,
            recipient_name=input_data.recipient_name,
            amount=input_data.amount,
            title=input_data.title,
            limit=10,
        )

        # Convert to contexts
        matched_transactions: List[TransactionContext] = []
        seen_combinations = set()

        for transaction in filtered:
            context = _transaction_to_context(transaction, db)
            key = (context.recipient_name, context.bank_account)
            if key not in seen_combinations:
                matched_transactions.append(context)
                seen_combinations.add(key)

        return FilterSuggestionOutput(
            matched_transactions=matched_transactions,
            filters_applied=filters_applied,
            match_count=len(matched_transactions),
        )

    finally:
        db.close()


def final_check_tool(input_data: FinalCheckInput) -> FinalCheckOutput:
    """
    Simple validation check: OK or list of problems.

    Checks:
    1. All required fields present (handled by Pydantic)
    2. Amount is positive
    3. Amount doesn't exceed user balance
    4. Bank account length looks reasonable (10-34 chars)
    5. Name-account consistency with past transactions

    Args:
        input_data: Complete transaction draft

    Returns:
        FinalCheckOutput with is_ok flag and list of problems (if any)
    """
    db = get_db()
    try:
        problems: List[str] = []

        # Get user balance
        balance = get_user_balance(db, input_data.user_id) or Decimal("0.00")

        # Check 1: Amount is positive
        if input_data.amount <= 0:
            problems.append(f"Amount must be positive (got {input_data.amount})")

        # Check 2: Amount doesn't exceed balance
        if input_data.amount > balance:
            problems.append(
                f"Insufficient balance: trying to send {input_data.amount} but only have {balance}"
            )

        # Check 3: Account length
        account_length = len(input_data.bank_account)
        if account_length < 10 or account_length > 34:
            problems.append(
                f"Bank account length unusual: {account_length} characters (expected 10-34)"
            )

        # Check 4: Historical consistency
        recipient_patterns = get_recipient_patterns(db, input_data.user_id)
        account_patterns = get_account_patterns(db, input_data.user_id)

        # Check if name usually goes with a different account
        if input_data.recipient_name in recipient_patterns:
            accounts = recipient_patterns[input_data.recipient_name]
            most_common_account = max(accounts, key=accounts.get)
            count = accounts[most_common_account]

            if most_common_account != input_data.bank_account and count > 1:
                problems.append(
                    f"Warning: '{input_data.recipient_name}' usually uses account {most_common_account} (used {count} times before)"
                )

        # Check if account usually goes with a different name
        if input_data.bank_account in account_patterns:
            names = account_patterns[input_data.bank_account]
            most_common_name = max(names, key=names.get)
            count = names[most_common_name]

            if most_common_name != input_data.recipient_name and count > 1:
                problems.append(
                    f"Warning: Account {input_data.bank_account} usually belongs to '{most_common_name}' (used {count} times before)"
                )

        is_ok = len(problems) == 0

        return FinalCheckOutput(
            is_ok=is_ok,
            problems=problems,
            user_balance=balance,
            amount_to_send=input_data.amount,
        )

    finally:
        db.close()


# Tool registry for MCP server
TOOLS = {
    "first_suggestion_tool": {
        "function": first_suggestion_tool,
        "input_schema": FirstSuggestionInput,
        "output_schema": FirstSuggestionOutput,
        "description": "Get up to 5 transactions with temporal context (1 year/month/week ago + 2 recent) for LLM to analyze and suggest",
    },
    "filter_suggestion_tool": {
        "function": filter_suggestion_tool,
        "input_schema": FilterSuggestionInput,
        "output_schema": FilterSuggestionOutput,
        "description": "Filter past transactions by partial name/amount/title and return matches for LLM to rank by relevance",
    },
    "final_check_tool": {
        "function": final_check_tool,
        "input_schema": FinalCheckInput,
        "output_schema": FinalCheckOutput,
        "description": "Validate transaction: returns is_ok (true/false) and list of problems if any",
    },
}
