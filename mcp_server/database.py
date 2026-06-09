"""DB session factory for mcp_server + re-exports of shared query helpers."""

from sqlalchemy.orm import Session

from shared.models import SessionLocal
from shared.queries import (  # noqa: F401 — re-exported for tools.py
    filter_transactions,
    get_account_patterns,
    get_recent_transactions,
    get_recipient_patterns,
    get_time_based_transactions,
    get_user_balance,
)


def get_db() -> Session:
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise
