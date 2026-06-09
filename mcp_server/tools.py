"""
MCP tool implementations for money transfer assistance and QA chatbot.

These tools provide structured data and insights for LLM agents to analyze and make decisions.
All outputs are designed for LLM consumption, not direct UI display.
"""

import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Add backend to path for imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "backend" / "src"))

from shared.models import Transaction, User

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
    RAGQueryInput,
    RAGQueryOutput,
    SQLQueryInput,
    SQLQueryOutput,
    TransactionContext,
)

load_dotenv()

# Initialize RAG retriever (lazy loading)
_rag_retriever = None

def get_rag_retriever():
    """Get or initialize RAG retriever instance with auto-initialization."""
    global _rag_retriever
    if _rag_retriever is None:
        try:
            # Import and initialize the retriever
            backend_qa_path = project_root / "backend" / "src" / "backend" / "qa"
            sys.path.insert(0, str(backend_qa_path))
            
            from rag.retriever import TransactionRetriever
            chroma_path = backend_qa_path / "rag" / "chroma_store"
            
            # Initialize with auto_initialize=True to create embeddings if needed
            logger.info("Initializing RAG retriever from %s", chroma_path)
            _rag_retriever = TransactionRetriever(
                chroma_db_path=str(chroma_path),
                auto_initialize=True  # Will create embeddings if they don't exist
            )
            logger.info("RAG retriever initialized")
        except Exception as e:
            logger.error("Could not initialize RAG retriever: %s", e, exc_info=True)
            _rag_retriever = None
    return _rag_retriever


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
        seen_transaction_ids = set()

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
            transactions.append(context)
            seen_transaction_ids.add(transaction.transaction_id)

        # Get the 2 most recent transactions (including unposted), excluding those already added
        recent = (
            db.query(Transaction)
            .filter(Transaction.sender_id == input_data.user_id)
            .order_by(Transaction.transaction_date_and_time.desc())
            .limit(10)
            .all()
        )
        recent_count = 0
        for transaction in recent:
            if transaction.transaction_id not in seen_transaction_ids:
                context = _transaction_to_context(transaction, db, "recent")
                transactions.append(context)
                seen_transaction_ids.add(transaction.transaction_id)
                recent_count += 1
                if recent_count >= 2:
                    break

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
        if input_data.recipient_bank_account:
            filters_applied["recipient_bank_account"] = input_data.recipient_bank_account
        if input_data.amount is not None:
            filters_applied["amount"] = float(input_data.amount)
        if input_data.title:
            filters_applied["title"] = input_data.title
        if input_data.max_number:
            filters_applied["max_number"] = input_data.max_number

        # Filter transactions
        filtered = filter_transactions(
            db,
            input_data.user_id,
            recipient_name=input_data.recipient_name,
            recipient_bank_account=input_data.recipient_bank_account,
            amount=input_data.amount,
            title=input_data.title,
            limit=input_data.max_number or 10,
        )

        # Convert to contexts (include all matching transactions, not deduplicated)
        matched_transactions: List[TransactionContext] = []

        for transaction in filtered:
            context = _transaction_to_context(transaction, db)
            matched_transactions.append(context)

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


def sql_query_tool(input_data: SQLQueryInput) -> SQLQueryOutput:
    """
    Execute SQL queries for transaction analysis.
    
    Supports functions:
    - get_recent_transactions: Get recent transactions for user
    - filter_transactions: Filter transactions by criteria
    - get_time_based_transactions: Get transactions from specific time periods
    - get_recipient_patterns: Analyze recipient patterns
    - get_user_balance: Get current user balance
    
    Args:
        input_data: Contains user_id, function_name, and parameters
    
    Returns:
        SQLQueryOutput with success status and query results
    """
    db = get_db()
    try:
        function_name = input_data.function_name
        params = input_data.parameters.copy()
        params["user_id"] = input_data.user_id
        
        result_data = None
        
        if function_name == "get_recent_transactions":
            limit = params.get("limit", 10)
            transactions = get_recent_transactions(db, input_data.user_id, limit)
            result_data = [
                {
                    "transaction_id": t.transaction_id,
                    "receiver_name": f"{t.receiver_name} {t.receiver_surname}",
                    "amount": float(t.amount),
                    "transaction_text": t.transaction_text or "",
                    "transaction_date": t.transaction_date_and_time.isoformat(),
                    "transaction_posted": t.transaction_posted,
                }
                for t in transactions
            ]
            
        elif function_name == "filter_transactions":
            recipient_name = params.get("recipient_name")
            amount = Decimal(str(params["amount"])) if "amount" in params else None
            title = params.get("title")
            limit = params.get("limit", 10)
            
            transactions = filter_transactions(
                db, input_data.user_id, recipient_name, None, amount, title, limit
            )
            result_data = [
                {
                    "transaction_id": t.transaction_id,
                    "receiver_name": f"{t.receiver_name} {t.receiver_surname}",
                    "amount": float(t.amount),
                    "transaction_text": t.transaction_text or "",
                    "transaction_date": t.transaction_date_and_time.isoformat(),
                    "transaction_posted": t.transaction_posted,
                }
                for t in transactions
            ]
            
        elif function_name == "get_time_based_transactions":
            time_transactions = get_time_based_transactions(db, input_data.user_id)
            result_data = [
                {
                    "transaction_id": t.transaction_id,
                    "receiver_name": f"{t.receiver_name} {t.receiver_surname}",
                    "amount": float(t.amount),
                    "transaction_text": t.transaction_text or "",
                    "transaction_date": t.transaction_date_and_time.isoformat(),
                    "time_label": label,
                }
                for t, label in time_transactions
            ]
            
        elif function_name == "get_recipient_patterns":
            patterns = get_recipient_patterns(db, input_data.user_id)
            result_data = patterns
            
        elif function_name == "get_user_balance":
            balance = get_user_balance(db, input_data.user_id)
            result_data = {
                "balance": float(balance) if balance else 0.0,
                "currency": "UAH"
            }
            
        else:
            return SQLQueryOutput(
                success=False,
                data=None,
                error=f"Unknown function: {function_name}",
                function_used=function_name,
            )
        
        return SQLQueryOutput(
            success=True,
            data=result_data,
            error=None,
            function_used=function_name,
        )
        
    except Exception as e:
        return SQLQueryOutput(
            success=False,
            data=None,
            error=str(e),
            function_used=input_data.function_name,
        )
    finally:
        db.close()


def rag_query_tool(input_data: RAGQueryInput) -> RAGQueryOutput:
    """
    Search for similar transactions using RAG (semantic search).
    
    Uses ChromaDB with OpenAI embeddings to find transactions similar
    to the query text.
    
    Args:
        input_data: Contains user_id, query text, and top_k
    
    Returns:
        RAGQueryOutput with success status and similar transactions
    """
    try:
        retriever = get_rag_retriever()
        if retriever is None:
            return RAGQueryOutput(
                success=False,
                data=[],
                count=0,
                query=input_data.query,
                error="RAG retriever not initialized. Please check ChromaDB setup."
            )
        
        # Perform similarity search
        results = retriever.retrieve(input_data.query, k=input_data.top_k)
        
        # Format results for agents
        formatted_results = [
            {
                "transaction_id": r["transaction_id"],
                "receiver_name": r["recipient_name"],
                "amount": r["amount"],
                "transaction_text": r["transaction_text"],
                "transaction_date": r["date"],
                "similarity_score": r["similarity"],
                "rank": r["rank"],
            }
            for r in results
        ]
        
        return RAGQueryOutput(
            success=True,
            data=formatted_results,
            count=len(formatted_results),
            query=input_data.query,
            error=None,
        )
        
    except Exception as e:
        return RAGQueryOutput(
            success=False,
            data=[],
            count=0,
            query=input_data.query,
            error=str(e),
        )


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
    "sql_query_tool": {
        "function": sql_query_tool,
        "input_schema": SQLQueryInput,
        "output_schema": SQLQueryOutput,
        "description": "Execute SQL queries for transaction analysis (recent transactions, filters, time-based, patterns, balance)",
    },
    "rag_query_tool": {
        "function": rag_query_tool,
        "input_schema": RAGQueryInput,
        "output_schema": RAGQueryOutput,
        "description": "Search for similar transactions using semantic search (RAG with ChromaDB embeddings)",
    },
}
