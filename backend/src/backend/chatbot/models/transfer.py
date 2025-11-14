from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, validator


class ConfirmationStatus(str, Enum):
    """Final yes/no confirmation from the user."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class FinalRecipient(BaseModel):
    """
    Recipient of the transfer.

    - If it's an already known recipient, `iban` can be omitted
      (the bank backend would fill it in).
    - For a new recipient, `iban` must be provided.
    """

    name: str = Field(..., description="Display name of the recipient")
    iban: Optional[str] = Field(
        None,
        description="IBAN of the recipient. Required for new recipients.",
    )

    @validator("name")
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Recipient name must not be empty.")
        return v.strip()

    @validator("iban")
    def iban_basic_checks(cls, v: Optional[str]) -> Optional[str]:
        """Very lightweight IBAN sanity check (length + alnum)."""
        if v is None:
            return v
        stripped = v.replace(" ", "")
        if len(stripped) < 15 or len(stripped) > 34:
            raise ValueError("IBAN length looks incorrect.")
        if not stripped.isalnum():
            raise ValueError("IBAN must contain only letters and digits.")
        return stripped.upper()


class MoneyTransferForm(BaseModel):
    """
    Data required to perform a money transfer in our PoC.
    This is what the agents collaborate to build and validate.
    """

    recipient: FinalRecipient
    amount: float = Field(..., gt=0, description="Amount of money to send.")
    currency: str = Field(
        "EUR",
        description="Currency code, e.g. EUR. For PoC we mostly use EUR.",
    )
    reference_text: str = Field(
        ...,
        description="Transfer title / reference shown to sender & recipient.",
    )
    confirmation_status: ConfirmationStatus = Field(
        default=ConfirmationStatus.PENDING,
        description="Has the user finally confirmed/cancelled the transfer?",
    )

    @validator("currency")
    def currency_upper(cls, v: str) -> str:
        v = v.strip().upper()
        if len(v) != 3:
            raise ValueError("Currency must be a 3-letter code, e.g. EUR.")
        return v

    @validator("reference_text")
    def reference_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Reference text must not be empty.")
        return v.strip()
