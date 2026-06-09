"""Alembic migration runner.

Kept out of app startup on purpose: schema changes run once via a dedicated
migration Job (compose one-shot / K8s Job), never concurrently across N service
replicas. See ``migrate/migrate_job.py``.
"""

from pathlib import Path

import shared


def run_migrations() -> None:
    """Apply Alembic migrations to head. Idempotent."""
    from alembic import command
    from alembic.config import Config

    base = Path(shared.__file__).resolve().parent.parent
    cfg = Config(str(base / "alembic.ini"))
    cfg.set_main_option("script_location", str(base / "alembic"))
    command.upgrade(cfg, "head")
