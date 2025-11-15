"""
Transaction Retriever - wyszukiwanie podobnych transakcji używając embeddingów z ChromaDB.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from chromadb.config import Settings

load_dotenv()


class TransactionRetriever:
    """
    Retriever do wyszukiwania podobnych transakcji na podstawie zapytania w języku naturalnym.
    Używa tylko ChromaDB.
    """
    
    def __init__(
        self,
        chroma_db_path: Optional[str] = None,
        collection_name: str = "transactions",
    ):
        """
        Inicjalizacja retrievera.
        
        Args:
            chroma_db_path: Ścieżka do bazy ChromaDB
            collection_name: Nazwa kolekcji w ChromaDB
        """
        # OpenAI client do tworzenia query embeddings
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            raise RuntimeError("Brakuje zmiennej środowiskowej OPENAI_API_KEY")
        
        self.oa_client = OpenAI(api_key=openai_api_key)
        self.model = "text-embedding-3-small"
        
        # Setup ścieżek
        script_dir = Path(__file__).parent
        
        if chroma_db_path is None:
            chroma_db_path = str(script_dir / "chroma_store")
        
        # ChromaDB setup
        self.chroma_client = chromadb.PersistentClient(
            path=chroma_db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.chroma_client.get_collection(name=collection_name)
        print(f"✓ ChromaDB załadowane z: {chroma_db_path}")
        print(f"✓ Kolekcja '{collection_name}' zawiera {self.collection.count()} transakcji")
    
    def _create_query_embedding(self, query: str) -> List[float]:
        """
        Tworzy embedding dla zapytania użytkownika.
        
        Args:
            query: Zapytanie w języku naturalnym
            
        Returns:
            Wektor embedding
        """
        response = self.oa_client.embeddings.create(
            model=self.model,
            input=[query],
        )
        return response.data[0].embedding
    
    def retrieve(self, query: str, k: int = 1) -> List[Dict]:
        """
        Wyszukuje najbardziej podobne transakcje używając ChromaDB.
        Zawsze zwraca top-k wyników bez threshold filtering.
        
        Args:
            query: Zapytanie w języku naturalnym
            k: Liczba wyników do zwrócenia (domyślnie 1)
            
        Returns:
            Lista słowników z informacjami o transakcjach, posortowana według similarity (malejąco)
        """
        # Twórz embedding dla query
        query_embedding = self._create_query_embedding(query)
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
        )
        
        # Formatuj wyniki
        formatted_results = []
        if results["ids"] and results["ids"][0]:
            for i, (doc_id, doc, metadata, distance) in enumerate(zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0] if "distances" in results and results["distances"] else [None] * k,
            )):
                # Konwertuj ChromaDB squared L2 distance na przybliżoną cosine similarity
                # Dla znormalizowanych wektorów: cosine_similarity ≈ 1 - (squared_l2_distance / 4)
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
        Wyszukuje najbardziej podobną transakcję (top-1).
        Zawsze zwraca najlepszy wynik bez threshold filtering.
        
        Args:
            query: Zapytanie w języku naturalnym
            
        Returns:
            Słownik z informacją o najbardziej podobnej transakcji lub None jeśli brak wyników
        """
        results = self.retrieve(query, k=1)
        return results[0] if results else None