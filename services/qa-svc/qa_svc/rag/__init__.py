"""
RAG (Retrieval Augmented Generation) system for transaction similarity search.

Provides tools for:
- Parsing transactions from database
- Creating embeddings with OpenAI
- Storing in ChromaDB vector database
- Retrieving similar transactions for RAG
"""

from .retriever import TransactionRetriever
from .parse_transactions import parse_transactions

__all__ = [
    "TransactionRetriever",
    "parse_transactions",
]
