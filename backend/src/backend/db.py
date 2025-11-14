from backend.models import Base, SessionLocal, engine


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection():
    try:
        connection = engine.connect()
        connection.close()
        return True
    except Exception:
        return False
