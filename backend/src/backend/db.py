import os

from dotenv import load_dotenv
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = f"postgresql://{os.getenv('DATABASE_USERNAME')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DATABASE_NAME')}"

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)


def init_db():
    Base.metadata.create_all(bind=engine)


def test_db():
    """Test database operations"""
    init_db()
    session = SessionLocal()

    try:
        existing = session.query(User).filter_by(email="test@example.com").first()

        if not existing:
            user = User(name="Test User", email="test@example.com")
            session.add(user)
            session.commit()
            print(f"✓ Created user: {user.name} ({user.email})")
        else:
            print(f"✓ User already exists: {existing.name} ({existing.email})")

        count = session.query(User).count()
        print(f"✓ Total users: {count}")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        session.rollback()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    test_db()
