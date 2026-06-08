"""Database session helpers built on the shared engine."""

from shared.models import Base, SessionLocal, engine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection() -> bool:
    try:
        connection = engine.connect()
        connection.close()
        return True
    except Exception:
        return False
