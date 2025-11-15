"""
AI Agents for chatbot workflow using LangChain LLM.
"""

import json
from decimal import Decimal
from typing import List, Optional, Tuple

from .llm import call_llm, call_llm_with_json
from .mcp_client import MCPClient, TransactionContext
from .schemas import SuggestionInfo


class SuggestionAgent:
    """
    Agent that uses LLM to analyze transaction data and generate user-friendly suggestions.
    Takes raw transaction data from MCP tools and uses AI to pick the best suggestion.
    """

    @staticmethod
    def pick_best_first_suggestion(transactions: List[TransactionContext], user_balance: Decimal) -> Optional[SuggestionInfo]:
        """
        Use LLM to pick the best transaction from first suggestions.

        Args:
            transactions: List of transactions with temporal labels
            user_balance: User's current balance

        Returns:
            SuggestionInfo or None if no good suggestion
        """
        if not transactions:
            return None

        # Prepare transaction data for LLM
        transactions_data = []
        for i, txn in enumerate(transactions):
            transactions_data.append({
                "index": i,
                "recipient_name": txn.recipient_name,
                "bank_account": txn.bank_account,
                "amount": float(txn.amount),
                "title": txn.title,
                "temporal_label": txn.temporal_label,
                "date": str(txn.transaction_date),
            })

        system_prompt = """You are an AI assistant helping neurodivergent users with money transfers.
Your task is to analyze past transactions and pick the BEST ONE to suggest to the user.

Consider:
1. Temporal patterns (monthly bills are very likely - prefer 1_month_ago)
2. Recurring payments (electricity, rent, subscriptions)
3. Recent transactions may indicate ongoing needs
4. User's current balance

Be helpful but not pushy. Pick the transaction that seems most likely to be needed now.

Respond in JSON format:
{
  "selected_index": <index of best transaction>,
  "confidence": <0.0-1.0>,
  "reason": "<simple, friendly 1-sentence explanation>"
}"""

        user_prompt = f"""User's current balance: €{user_balance}

Available transactions to suggest:
{json.dumps(transactions_data, indent=2)}

Pick the BEST transaction to suggest. Consider what the user likely needs to pay now."""

        response = call_llm_with_json(system_prompt, user_prompt, temperature=0.3)
        result = json.loads(response)

        selected_index = result.get("selected_index", 0)
        if selected_index >= len(transactions):
            selected_index = 0

        txn = transactions[selected_index]

        return SuggestionInfo(
            recipient_name=txn.recipient_name,
            bank_account=txn.bank_account,
            amount=float(txn.amount),
            title=txn.title,
            confidence=float(result.get("confidence", 0.8)),
            reason=result.get("reason", f"Based on your past payment to {txn.recipient_name}."),
        )

    @staticmethod
    def format_filter_suggestion(
        matched_transactions: List[TransactionContext],
        filters_applied: dict,
        exclude_suggestion: Optional["SuggestionInfo"] = None,
    ) -> Optional[SuggestionInfo]:
        """
        Use LLM to pick the best match from filtered transactions.

        Args:
            matched_transactions: Filtered transactions
            filters_applied: Which filters were used
            exclude_suggestion: Optional suggestion to exclude (first suggestion)

        Returns:
            SuggestionInfo or None if confidence too low (< 90%)
        """
        if not matched_transactions:
            return None

        # Filter out the excluded suggestion (if provided)
        filtered_transactions = []
        for txn in matched_transactions:
            # Skip if this matches the excluded suggestion
            if exclude_suggestion and (
                txn.recipient_name == exclude_suggestion.recipient_name
                and txn.bank_account == exclude_suggestion.bank_account
                and float(txn.amount) == exclude_suggestion.amount
                and txn.title == exclude_suggestion.title
            ):
                continue
            filtered_transactions.append(txn)

        # If no transactions left after filtering, return None
        if not filtered_transactions:
            return None

        # Prepare data for LLM
        transactions_data = []
        for i, txn in enumerate(filtered_transactions[:5]):  # Limit to top 5
            transactions_data.append({
                "index": i,
                "recipient_name": txn.recipient_name,
                "bank_account": txn.bank_account,
                "amount": float(txn.amount),
                "title": txn.title,
                "date": str(txn.transaction_date),
            })

        system_prompt = """You are an AI assistant helping neurodivergent users with money transfers.
The user has partially filled in payment details. Your task is to find the BEST matching past transaction.

Analyze the matched transactions and user's partial input:
- How well does each transaction match what the user entered?
- Which transaction is most likely what the user wants to pay?

IMPORTANT: Only suggest if confidence is 90% or higher. If uncertain, return null.

Respond in JSON format:
{
  "selected_index": <index of best match, or null if confidence < 90%>,
  "confidence": <0.0-1.0>,
  "reason": "<simple 1-sentence explanation>"
}"""

        user_prompt = f"""User's partial input:
{json.dumps(filters_applied, indent=2)}

Matching past transactions:
{json.dumps(transactions_data, indent=2)}

Which transaction best matches the user's input? Only suggest if confidence >= 90%."""

        response = call_llm_with_json(system_prompt, user_prompt, temperature=0.2)
        result = json.loads(response)

        selected_index = result.get("selected_index")
        confidence = float(result.get("confidence", 0.0))

        # Only return if confidence >= 90%
        if selected_index is None or confidence < 0.90:
            return None

        if selected_index >= len(filtered_transactions):
            return None

        txn = filtered_transactions[selected_index]

        return SuggestionInfo(
            recipient_name=txn.recipient_name,
            bank_account=txn.bank_account,
            amount=float(txn.amount),
            title=txn.title,
            confidence=confidence,
            reason=result.get("reason", "Matches your input."),
        )


class SuggestionVerifierAgent:
    """
    Agent that calls filter_suggestion_tool during field collection
    and decides if suggestion is confident enough (90%+).
    """

    @staticmethod
    def check_for_suggestion(
        user_id: int,
        recipient_account: Optional[str] = None,
        recipient_name: Optional[str] = None,
        amount: Optional[Decimal] = None,
        transaction_text: Optional[str] = None,
        exclude_suggestion: Optional["SuggestionInfo"] = None,
    ) -> Optional[SuggestionInfo]:
        """
        Check if there's a confident suggestion based on collected fields.

        Only returns suggestion if confidence >= 90%.

        Args:
            user_id: User ID
            recipient_account: Optional collected account
            recipient_name: Optional collected name
            amount: Optional collected amount
            transaction_text: Optional collected text
            exclude_suggestion: Optional first suggestion to exclude (avoid duplicates)

        Returns:
            SuggestionInfo or None
        """
        # Need at least 2 fields to make a suggestion
        fields_provided = sum(
            1 for f in [recipient_account, recipient_name, amount, transaction_text] if f is not None
        )
        if fields_provided < 2:
            return None

        # Call filter tool
        result = MCPClient.filter_suggestions(
            user_id=user_id,
            recipient_name=recipient_name,
            recipient_bank_account=recipient_account,
            amount=amount,
            title=transaction_text,
            max_number=5,
        )

        # Use SuggestionAgent to analyze results
        return SuggestionAgent.format_filter_suggestion(
            result.matched_transactions, result.filters_applied, exclude_suggestion
        )


class MainAgent:
    """
    Agent that collects 4 fields one by one and validates the final transaction.
    Uses simple, clear language for neurodivergent users.
    """

    FIELD_PROMPTS = {
        1: "Please enter the recipient's account number.",
        2: "Please enter the recipient's full name.",
        3: "Please enter the amount to transfer.",
        4: "Please enter a description for this transaction.",
    }

    FIELD_NAMES = {
        1: "recipient_account",
        2: "recipient_name",
        3: "amount",
        4: "transaction_text",
    }

    @staticmethod
    def get_field_prompt(field_number: int) -> str:
        """Get the prompt for a specific field."""
        return MainAgent.FIELD_PROMPTS.get(field_number, "Please provide information.")

    @staticmethod
    def validate_and_store_field(
        field_number: int, value: str
    ) -> Tuple[bool, Optional[str], Optional[any]]:
        """
        Validate a field value using basic rules and LLM for parsing/correction.

        Args:
            field_number: Which field (1-4)
            value: User input

        Returns:
            (is_valid, error_message, processed_value)
        """
        if not value or not value.strip():
            return False, "This field cannot be empty.", None

        value = value.strip()

        if field_number == 1:  # Account number
            # Basic validation
            if len(value) < 10 or len(value) > 34:
                return False, "Account number should be between 10 and 34 characters.", None
            return True, None, value

        elif field_number == 2:  # Full name
            # Use LLM to validate and format name properly
            if len(value) < 2:
                return False, "Name is too short.", None

            system_prompt = """You are validating a recipient's full name for a bank transfer.
Check if the name looks valid and properly formatted.

Return JSON:
{
  "is_valid": true/false,
  "formatted_name": "<properly formatted name>",
  "error": "<error message if invalid, null otherwise>"
}"""

            user_prompt = f"Validate this name: {value}"

            response = call_llm_with_json(system_prompt, user_prompt, temperature=0.1)
            result = json.loads(response)

            if result.get("is_valid"):
                return True, None, result.get("formatted_name", value)
            else:
                return False, result.get("error", "Name format doesn't look right."), None

        elif field_number == 3:  # Amount
            # Use LLM to parse various amount formats
            system_prompt = """You are parsing a money amount for a bank transfer.
Users may enter amounts in various formats like:
- "100"
- "100.50"
- "100,50" (European format)
- "€100"
- "100 euros"

Parse the amount and return JSON:
{
  "is_valid": true/false,
  "amount": <numeric value>,
  "error": "<error message if invalid, null otherwise>"
}"""

            user_prompt = f"Parse this amount: {value}"

            response = call_llm_with_json(system_prompt, user_prompt, temperature=0.1)
            result = json.loads(response)

            if result.get("is_valid"):
                amount = Decimal(str(result.get("amount")))
                if amount <= 0:
                    return False, "Amount must be greater than zero.", None
                return True, None, amount
            else:
                return False, result.get("error", "Please enter a valid amount."), None

        elif field_number == 4:  # Transaction text
            if len(value) > 500:
                return False, "Description is too long (max 500 characters).", None
            return True, None, value

        return False, "Invalid field.", None

    @staticmethod
    def validate_complete_transaction(
        user_id: int,
        recipient_account: str,
        recipient_name: str,
        amount: Decimal,
        transaction_text: str,
    ) -> Tuple[bool, List[str]]:
        """
        Validate complete transaction using final_check_tool.

        Args:
            user_id: User ID
            recipient_account: Account number
            recipient_name: Full name
            amount: Amount
            transaction_text: Description

        Returns:
            (is_ok, problems_list)
        """
        result = MCPClient.final_check(
            user_id=user_id,
            recipient_name=recipient_name,
            bank_account=recipient_account,
            amount=amount,
            title=transaction_text,
        )

        return result.is_ok, result.problems

    @staticmethod
    def format_problems_message(problems: List[str]) -> str:
        """
        Use LLM to format validation problems in simple, neurodivergent-friendly language.

        Args:
            problems: List of problem strings

        Returns:
            Formatted message
        """
        if not problems:
            return "Everything looks good!"

        system_prompt = """You are an AI assistant helping neurodivergent users with money transfers.
Your task is to explain validation problems in SIMPLE, CLEAR, and FRIENDLY language.

Guidelines:
- Use short sentences
- Avoid technical jargon
- Be supportive and non-judgmental
- Make it easy to understand
- End by asking if they want to continue anyway

Keep the message brief (2-4 sentences max)."""

        user_prompt = f"""Validation problems found:
{json.dumps(problems, indent=2)}

Explain these problems to the user in simple, friendly language."""

        response = call_llm(system_prompt, user_prompt, temperature=0.5)
        return response + "\n\nDo you want to continue anyway?"
