"""One-shot schema runner.

Creates any missing tables and applies Alembic migrations to head, then exits.
Run as a compose one-shot service / K8s Job before the app services start, so
schema changes happen exactly once instead of racing across N replicas.
"""

from shared.db import init_db
from shared.migrations import run_migrations

if __name__ == "__main__":
    init_db()
    run_migrations()
    print("migrations applied")
