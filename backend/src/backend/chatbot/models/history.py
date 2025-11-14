from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from .transfer import FinalRecipient, MoneyTransferForm


class TransactionRecord(BaseModel):
    """
    Single historical transaction record returned by MCP.
    """

    date: date = Field(..., description="Execution date of the transaction.")
    recipient_name: str
    recipient_iban: str
    amount: float
    currency: str
    title: str

    def to_transfer_form(self) -> MoneyTransferForm:
        """
        Convenience helper: convert this historical transaction
        into a pre-filled MoneyTransferForm candidate.
        """
        recipient = FinalRecipient(name=self.recipient_name, iban=self.recipient_iban)
        return MoneyTransferForm(
            recipient=recipient,
            amount=self.amount,
            currency=self.currency,
            reference_text=self.title,
        )