"""
RAG (Retrieval Augmented Generation) system for transaction similarity search.

Provides tools for:
- Parsing transactions from database
- Creating embeddings with OpenAI
- Storing in ChromaDB vector database
- Retrieving similar transactions for RAG
"""

from .retriever import (
    TransactionRetriever,
    get_retriever,
    search_transactions,
)

__all__ = [
    "TransactionRetriever",
    "get_retriever", 
    "search_transactions",
]
