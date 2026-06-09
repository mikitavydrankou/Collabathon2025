"""Shared test fixtures and environment setup.

Sets dummy env vars *before* any `shared.*` import so module-level code that
reads them (e.g. `shared.security` requires `JWT_SECRET`, `shared.models`
builds a DATABASE_URL) doesn't blow up. The DB URL is never connected to: the
DB-backed tests use their own in-memory SQLite engine via the `db_session`
fixture.
"""

import os

os.environ.setdefault("JWT_SECRET", "test-secret-key")
os.environ.setdefault("DATABASE_USERNAME", "test")
os.environ.setdefault("DATABASE_PASSWORD", "test")
os.environ.setdefault("DATABASE_NAME", "test")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from shared.models import Base


@pytest.fixture
def db_session():
    """Fresh in-memory SQLite DB with all tables created, torn down per test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
