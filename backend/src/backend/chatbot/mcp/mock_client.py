from __future__ import annotations

from datetime import date, timedelta
from typing import List

from ..models import TransactionRecord


def get_transaction_history(user_id: str) -> List[TransactionRecord]:
    """
    Mock of MCP client.

    In the real system this function will call the MCP server to fetch
    historical transactions for the given user_id.

    For the PoC we return a small, fixed set of example transactions that
    simulate:
    - a rent payment made a week ago,
    - a utility bill paid 3 months ago,
    - a one-off transfer from about a year ago.

    The agents will use these records to build a suggested MoneyTransferForm.
    """

    today = date.today()

    # 1 week ago – typical recurring rent payment
    rent_payment = TransactionRecord(
        date=today - timedelta(days=7),
        recipient_name="Anna Kowalska (Landlord)",
        recipient_iban="DE89 3704 0044 0532 0130 00",
        amount=850.00,
        currency="EUR",
        title="Rent for November",
    )

    # 3 months ago – electricity bill
    electricity_bill = TransactionRecord(
        date=today - timedelta(days=90),
        recipient_name="Stadtwerke Berlin",
        recipient_iban="DE12 3456 7890 1234 5678 90",
        amount=120.50,
        currency="EUR",
        title="Electricity bill Q3",
    )

    # 11 months ago – one-off transfer to a friend
    friend_transfer = TransactionRecord(
        date=today - timedelta(days=330),
        recipient_name="Max Mustermann",
        recipient_iban="DE44 5001 0517 5407 3249 31",
        amount=50.00,
        currency="EUR",
        title="Birthday gift",
    )

    # For now we ignore user_id and always return the same examples.
    # Later you can branch on user_id to simulate different profiles.
    return [rent_payment, electricity_bill, friend_transfer]