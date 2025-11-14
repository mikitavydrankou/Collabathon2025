"""
Backend models package.

Re-exports models and database objects from shared package for backward compatibility.
"""

from shared.models import Base, PersonToContact, SessionLocal, Transaction, User, engine

__all__ = ["Base", "engine", "SessionLocal", "User", "PersonToContact", "Transaction"]
