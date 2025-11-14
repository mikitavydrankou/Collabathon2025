"""
Database utilities for backend service.

Re-exports from shared.models for backward compatibility.
"""

from shared.models import Base, SessionLocal, engine


def init_db():
    """Initialize database by creating all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session for FastAPI dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection():
    """Test database connectivity."""
    try:
        connection = engine.connect()
        connection.close()
        return True
    except Exception:
        return False


__all__ = ["Base", "SessionLocal", "engine", "init_db", "get_db", "test_connection"]
