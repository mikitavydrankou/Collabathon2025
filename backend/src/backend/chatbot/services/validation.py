from __future__ import annotations

from typing import List, Tuple

from pydantic import ValidationError

from ..models import MoneyTransferForm


def validate_transfer_form(
    form: MoneyTransferForm,
) -> Tuple[bool, List[str], List[str]]:
    """
    Run Pydantic validation on the MoneyTransferForm and translate
    errors into:
      - list of field names that need attention (pending_fields),
      - list of human-readable error messages (for the agent to rephrase).

    Returns:
      (is_valid, pending_fields, error_messages)
    """
    try:
        # Re-validate by round-tripping through model_dump.
        MoneyTransferForm.model_validate(form.model_dump())
        return True, [], []
    except ValidationError as exc:
        pending_fields: List[str] = []
        messages: List[str] = []

        for err in exc.errors():
            # err example: {"loc": ("recipient", "iban"), "msg": "...", "type": "..."}
            loc = err.get("loc", ())
            msg = err.get("msg", "Invalid value.")

            # We convert nested locations into dot notation, e.g. "recipient.iban"
            if isinstance(loc, (list, tuple)):
                field_path = ".".join(str(part) for part in loc)
            else:
                field_path = str(loc)

            pending_fields.append(field_path)
            messages.append(f"{field_path}: {msg}")

        # Deduplicate but keep order
        seen = set()
        unique_pending = []
        for f in pending_fields:
            if f not in seen:
                seen.add(f)
                unique_pending.append(f)

        return False, unique_pending, messages