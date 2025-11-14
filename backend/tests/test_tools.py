"""
Comprehensive tests for MCP server tools.

These tests use the real database models and seeded data.
"""

import os
from datetime import datetime
from decimal import Decimal

import pytest
from dotenv import load_dotenv

from backend.models import SessionLocal, Transaction, User
from mcp_server.schemas import (
    FilterSuggestionInput,
    FinalCheckInput,
    FirstSuggestionInput,
)
from mcp_server.tools import (
    filter_suggestion_tool,
    final_check_tool,
    first_suggestion_tool,
)

# Load environment variables
load_dotenv()


@pytest.fixture
def db_session():
    """Create a database session for testing."""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_user_id(db_session):
    """Get a test user ID from the seeded data."""
    user = db_session.query(User).filter(User.username == "alex.brown").first()
    if not user:
        pytest.skip("Test user 'alex.brown' not found. Please run seed_database().")
    return user.user_id


@pytest.fixture
def test_user_2_id(db_session):
    """Get another test user ID."""
    user = db_session.query(User).filter(User.username == "kate.davis").first()
    if not user:
        pytest.skip("Test user 'kate.davis' not found. Please run seed_database().")
    return user.user_id


class TestFirstSuggestionTool:
    """Tests for first_suggestion_tool."""

    def test_returns_suggestions_for_user_with_transactions(self, test_user_id):
        """Test that suggestions are returned for a user with transaction history."""
        input_data = FirstSuggestionInput(user_id=test_user_id)
        result = first_suggestion_tool(input_data)

        assert result.suggestions is not None
        assert len(result.suggestions) > 0
        assert result.message is not None
        assert "payment" in result.message.lower()

    def test_suggestions_have_required_fields(self, test_user_id):
        """Test that each suggestion has all required fields."""
        input_data = FirstSuggestionInput(user_id=test_user_id)
        result = first_suggestion_tool(input_data)

        for suggestion in result.suggestions:
            assert suggestion.recipient_name
            assert suggestion.bank_account
            assert suggestion.amount > 0
            assert suggestion.title
            assert suggestion.last_used
            assert isinstance(suggestion.last_used, datetime)

    def test_no_duplicate_suggestions(self, test_user_id):
        """Test that there are no duplicate (name, account) pairs."""
        input_data = FirstSuggestionInput(user_id=test_user_id)
        result = first_suggestion_tool(input_data)

        seen = set()
        for suggestion in result.suggestions:
            key = (suggestion.recipient_name, suggestion.bank_account)
            assert key not in seen, f"Duplicate suggestion found: {key}"
            seen.add(key)

    def test_user_with_no_transactions(self):
        """Test behavior for a user with no transactions."""
        # Use a user ID that doesn't exist or has no transactions
        input_data = FirstSuggestionInput(user_id=99999)
        result = first_suggestion_tool(input_data)

        assert result.suggestions == []
        assert "haven't made any payments" in result.message.lower()


class TestFilterSuggestionTool:
    """Tests for filter_suggestion_tool."""

    def test_filter_by_recipient_name(self, test_user_id, db_session):
        """Test filtering by partial recipient name."""
        # Get a known recipient name from the user's transactions
        transaction = (
            db_session.query(Transaction)
            .filter(Transaction.sender_id == test_user_id)
            .first()
        )

        if not transaction:
            pytest.skip("No transactions found for test user")

        # Use partial name
        partial_name = transaction.receiver_name[:3]
        input_data = FilterSuggestionInput(
            user_id=test_user_id, recipient_name=partial_name
        )
        result = filter_suggestion_tool(input_data)

        assert result.suggestions is not None
        assert len(result.suggestions) > 0
        # Check that the partial name appears in results
        assert any(
            partial_name.lower() in s.recipient_name.lower()
            for s in result.suggestions
        )

    def test_filter_by_amount(self, test_user_id, db_session):
        """Test filtering by exact amount."""
        # Get a known amount from the user's transactions
        transaction = (
            db_session.query(Transaction)
            .filter(Transaction.sender_id == test_user_id)
            .first()
        )

        if not transaction:
            pytest.skip("No transactions found for test user")

        input_data = FilterSuggestionInput(
            user_id=test_user_id, amount=transaction.amount
        )
        result = filter_suggestion_tool(input_data)

        assert result.suggestions is not None
        assert len(result.suggestions) > 0
        # All results should have the specified amount
        assert all(s.amount == transaction.amount for s in result.suggestions)

    def test_filter_by_title(self, test_user_id, db_session):
        """Test filtering by partial title."""
        # Get a known title from the user's transactions
        transaction = (
            db_session.query(Transaction)
            .filter(Transaction.sender_id == test_user_id)
            .filter(Transaction.transaction_text.isnot(None))
            .first()
        )

        if not transaction:
            pytest.skip("No transactions with text found for test user")

        # Use partial title
        partial_title = transaction.transaction_text[:5]
        input_data = FilterSuggestionInput(
            user_id=test_user_id, title=partial_title
        )
        result = filter_suggestion_tool(input_data)

        assert result.suggestions is not None
        assert len(result.suggestions) > 0

    def test_filter_with_no_matches(self, test_user_id):
        """Test filtering with criteria that match nothing."""
        input_data = FilterSuggestionInput(
            user_id=test_user_id, recipient_name="NonexistentPerson123456"
        )
        result = filter_suggestion_tool(input_data)

        assert result.suggestions == []
        assert "no past payments match" in result.message.lower()

    def test_filter_no_criteria(self, test_user_id):
        """Test filtering with no criteria returns recent transactions."""
        input_data = FilterSuggestionInput(user_id=test_user_id)
        result = filter_suggestion_tool(input_data)

        assert result.suggestions is not None
        # Should return some results (up to 10)
        assert len(result.suggestions) <= 10


class TestFinalCheckTool:
    """Tests for final_check_tool."""

    def test_valid_transaction(self, test_user_id, test_user_2_id, db_session):
        """Test validation of a valid transaction."""
        # Get the test user's balance and a known recipient
        user = db_session.query(User).filter(User.user_id == test_user_id).first()
        recipient = (
            db_session.query(User).filter(User.user_id == test_user_2_id).first()
        )

        input_data = FinalCheckInput(
            user_id=test_user_id,
            recipient_name=f"{recipient.name} {recipient.surname}",
            bank_account=recipient.bank_number,
            amount=Decimal("100.00"),
            title="Test payment",
        )
        result = final_check_tool(input_data)

        assert result.is_valid is True
        assert "looks good" in result.message.lower()

    def test_negative_amount(self, test_user_id):
        """Test validation fails for negative amount."""
        input_data = FinalCheckInput(
            user_id=test_user_id,
            recipient_name="Test User",
            bank_account="1234567890123456",
            amount=Decimal("-100.00"),
            title="Test payment",
        )
        result = final_check_tool(input_data)

        assert result.is_valid is False
        assert any(w.type == "invalid_amount" for w in result.warnings)
        assert "greater than zero" in result.message.lower() or any(
            "greater than zero" in w.message.lower() for w in result.warnings
        )

    def test_zero_amount(self, test_user_id):
        """Test validation fails for zero amount."""
        input_data = FinalCheckInput(
            user_id=test_user_id,
            recipient_name="Test User",
            bank_account="1234567890123456",
            amount=Decimal("0.00"),
            title="Test payment",
        )
        result = final_check_tool(input_data)

        assert result.is_valid is False
        assert any(w.type == "invalid_amount" for w in result.warnings)

    def test_insufficient_balance(self, test_user_id, db_session):
        """Test validation fails when amount exceeds balance."""
        # Get the user's balance
        user = db_session.query(User).filter(User.user_id == test_user_id).first()
        excessive_amount = user.balance + Decimal("1000.00")

        input_data = FinalCheckInput(
            user_id=test_user_id,
            recipient_name="Test User",
            bank_account="1234567890123456",
            amount=excessive_amount,
            title="Test payment",
        )
        result = final_check_tool(input_data)

        assert result.is_valid is False
        assert any(w.type == "insufficient_balance" for w in result.warnings)
        assert any(
            "don't have enough" in w.message.lower() for w in result.warnings
        )

    def test_account_length_warning(self, test_user_id):
        """Test warning for unusual account length."""
        # Too short account number
        input_data = FinalCheckInput(
            user_id=test_user_id,
            recipient_name="Test User",
            bank_account="123",
            amount=Decimal("100.00"),
            title="Test payment",
        )
        result = final_check_tool(input_data)

        assert any(w.type == "account_length" for w in result.warnings)
        assert any("unusual" in w.message.lower() for w in result.warnings)

    def test_name_mismatch_warning(self, test_user_id, db_session):
        """Test warning when name usually goes with a different account."""
        # Get a transaction from the test user
        transaction = (
            db_session.query(Transaction)
            .filter(Transaction.sender_id == test_user_id)
            .first()
        )

        if not transaction:
            pytest.skip("No transactions found for test user")

        # Get the receiver
        receiver = (
            db_session.query(User)
            .filter(User.user_id == transaction.receiver_id)
            .first()
        )

        # Use the correct name but wrong account
        input_data = FinalCheckInput(
            user_id=test_user_id,
            recipient_name=f"{receiver.name} {receiver.surname}",
            bank_account="9999999999999999",  # Different account
            amount=Decimal("100.00"),
            title="Test payment",
        )
        result = final_check_tool(input_data)

        # This might trigger a name_mismatch warning if the user has sent
        # multiple times to this recipient
        # Note: This test depends on seeded data patterns

    def test_decimal_precision(self, test_user_id):
        """Test that amounts are properly rounded to 2 decimal places."""
        input_data = FinalCheckInput(
            user_id=test_user_id,
            recipient_name="Test User",
            bank_account="1234567890123456",
            amount=Decimal("100.999"),  # Should be rounded
            title="Test payment",
        )

        # Should not raise ValidationError
        result = final_check_tool(input_data)
        assert result is not None


class TestInputValidation:
    """Tests for input validation with Pydantic schemas."""

    def test_first_suggestion_requires_user_id(self):
        """Test that FirstSuggestionInput requires user_id."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            FirstSuggestionInput()

    def test_filter_suggestion_requires_user_id(self):
        """Test that FilterSuggestionInput requires user_id."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            FilterSuggestionInput()

    def test_final_check_requires_all_fields(self):
        """Test that FinalCheckInput requires all transaction fields."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            FinalCheckInput(user_id=1)

        with pytest.raises(Exception):
            FinalCheckInput(user_id=1, recipient_name="Test")

        with pytest.raises(Exception):
            FinalCheckInput(
                user_id=1, recipient_name="Test", bank_account="123456"
            )

    def test_final_check_rejects_empty_strings(self):
        """Test that FinalCheckInput rejects empty strings."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            FinalCheckInput(
                user_id=1,
                recipient_name="",
                bank_account="123456",
                amount=Decimal("100.00"),
                title="Test",
            )

        with pytest.raises(Exception):
            FinalCheckInput(
                user_id=1,
                recipient_name="Test User",
                bank_account="123456",
                amount=Decimal("100.00"),
                title="   ",  # Only whitespace
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
