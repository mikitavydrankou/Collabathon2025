"""
Transaction Retriever - searching for similar transactions using embeddings with ChromaDB.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from chromadb.config import Settings

load_dotenv()


class TransactionRetriever:
    """
    Retriever for searching similar transactions based on natural language queries.
    Uses ChromaDB for vector search.
    """
    
    def __init__(
        self,
        chroma_db_path: Optional[str] = None,
        collection_name: str = "transactions",
        auto_initialize: bool = True,
    ):
        """
        Initialize the retriever.
        
        Args:
            chroma_db_path: Path to ChromaDB database
            collection_name: Collection name in ChromaDB
            auto_initialize: If True, automatically create embeddings if they don't exist
        """
        # OpenAI client for creating query embeddings
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            raise RuntimeError("Missing OPENAI_API_KEY environment variable")
        
        self.oa_client = OpenAI(api_key=openai_api_key)
        self.model = "text-embedding-3-small"
        
        # Setup paths
        script_dir = Path(__file__).parent
        
        if chroma_db_path is None:
            chroma_db_path = str(script_dir / "chroma_store")
        
        self.chroma_db_path = chroma_db_path
        self.collection_name = collection_name
        
        # Check if ChromaDB exists, create if not and auto_initialize is True
        if auto_initialize and not Path(chroma_db_path).exists():
            print(f"⚠️  ChromaDB not found at {chroma_db_path}")
            print("🔄 Auto-initializing ChromaDB with embeddings...")
            self._initialize_chromadb()
        
        # ChromaDB setup
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=chroma_db_path,
                settings=Settings(anonymized_telemetry=False)
            )
            self.collection = self.chroma_client.get_collection(name=collection_name)
            print(f"✅ ChromaDB loaded from: {chroma_db_path}")
            print(f"✅ Collection '{collection_name}' contains {self.collection.count()} transactions")
        except Exception as e:
            if auto_initialize:
                print(f"⚠️  Error loading collection: {e}")
                print("🔄 Creating new collection...")
                self._initialize_chromadb()
                self.collection = self.chroma_client.get_collection(name=collection_name)
            else:
                raise
    
    def _initialize_chromadb(self):
        """
        Initialize ChromaDB by parsing transactions and creating embeddings.
        """
        try:
            # Import here to avoid circular imports
            from .parse_transactions import parse_transactions
            
            script_dir = Path(__file__).parent
            transactions_json = script_dir / "transactions.json"
            
            # Step 1: Parse transactions from database
            print("  1/3 Parsing transactions from database...")
            transactions = parse_transactions(
                output_file=str(transactions_json),
                filter_posted=True,
                limit=None
            )
            
            if not transactions:
                print("  ❌ No transactions found in database!")
                return
            
            # Step 2: Create embeddings
            print(f"  2/3 Creating embeddings for {len(transactions)} transactions...")
            documents = [tx["enhanced_text"] for tx in transactions]
            embeddings = self._embed_texts(documents)
            
            # Step 3: Create ChromaDB and add data
            print("  3/3 Creating ChromaDB collection...")
            Path(self.chroma_db_path).mkdir(parents=True, exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(
                path=self.chroma_db_path,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Create collection
            collection = self.chroma_client.get_or_create_collection(name=self.collection_name)
            
            # Add transactions
            ids = [str(tx["transaction_id"]) for tx in transactions]
            metadatas = [
                {
                    "transaction_id": tx["transaction_id"],
                    "transaction_text": tx["transaction_text"],
                    "amount": tx["amount"],
                    "recipient_name": tx["recipient_name"],
                    "date": tx["date"],
                }
                for tx in transactions
            ]
            
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
            )
            
            print(f"  ✅ ChromaDB initialized with {len(ids)} transactions!")
            
        except Exception as e:
            print(f"  ❌ Error initializing ChromaDB: {e}")
            raise
    
    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for a list of texts using OpenAI.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        response = self.oa_client.embeddings.create(
            model=self.model,
            input=texts,
        )
        return [item.embedding for item in response.data]
    
    def _create_query_embedding(self, query: str) -> List[float]:
        """
        Create embedding for user query.
        
        Args:
            query: Natural language query
            
        Returns:
            Embedding vector
        """
        response = self.oa_client.embeddings.create(
            model=self.model,
            input=[query],
        )
        return response.data[0].embedding
    
    def retrieve(self, query: str, k: int = 3) -> List[Dict]:
        """
        Search for most similar transactions using ChromaDB.
        Always returns top-k results without threshold filtering.
        
        Args:
            query: Natural language query
            k: Number of results to return (default 3)
            
        Returns:
            List of dictionaries with transaction information, sorted by similarity (descending)
        """
        # Create embedding for query
        query_embedding = self._create_query_embedding(query)
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
        )
        
        # Format results
        formatted_results = []
        if results["ids"] and results["ids"][0]:
            for i, (doc_id, doc, metadata, distance) in enumerate(zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0] if "distances" in results and results["distances"] else [None] * k,
            )):
                # Convert ChromaDB squared L2 distance to approximate cosine similarity
                # For normalized vectors: cosine_similarity ≈ 1 - (squared_l2_distance / 4)
                similarity = max(0.0, 1.0 - (distance / 4.0)) if distance is not None else None
                
                formatted_results.append({
                    "rank": i + 1,
                    "transaction_id": int(doc_id),
                    "document": doc,
                    "transaction_text": metadata.get("transaction_text"),
                    "amount": metadata.get("amount"),
                    "recipient_name": metadata.get("recipient_name"),
                    "date": metadata.get("date"),
                    "distance": distance,
                    "similarity": similarity,
                })
        
        return formatted_results
    
    def retrieve_one(self, query: str) -> Optional[Dict]:
        """
        Search for most similar transaction (top-1).
        Always returns best result without threshold filtering.
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary with information about most similar transaction or None if no results
        """
        results = self.retrieve(query, k=1)
        return results[0] if results else None