"""
SQLAlchemy models for the banking application.

All database models are defined here and shared across services.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = f"postgresql://{os.getenv('DATABASE_USERNAME')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5433')}/{os.getenv('DATABASE_NAME')}"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Import all models here to ensure they're registered with Base
from .person_to_contact import PersonToContact
from .transaction import Transaction
from .user import User

__all__ = ["Base", "engine", "SessionLocal", "User", "PersonToContact", "Transaction"]
