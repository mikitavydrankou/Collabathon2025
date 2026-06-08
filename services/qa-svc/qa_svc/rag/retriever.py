"""Transaction retriever: vector search over the shared Chroma server."""

import os
from typing import Dict, List, Optional

import chromadb
from openai import OpenAI


class TransactionRetriever:
    """Search similar transactions by natural language using Chroma + OpenAI embeddings."""

    def __init__(self, collection_name: str = "transactions", **_ignored):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY environment variable")

        self.oa_client = OpenAI(api_key=api_key)
        self.model = "text-embedding-3-small"
        self.collection_name = collection_name

        self.chroma_client = chromadb.HttpClient(
            host=os.getenv("CHROMA_HOST", "chroma"),
            port=int(os.getenv("CHROMA_PORT", "8000")),
        )
        self.collection = self.chroma_client.get_or_create_collection(name=collection_name)

    def _create_query_embedding(self, query: str) -> List[float]:
        response = self.oa_client.embeddings.create(model=self.model, input=[query])
        return response.data[0].embedding

    def retrieve(self, query: str, k: int = 3) -> List[Dict]:
        query_embedding = self._create_query_embedding(query)
        results = self.collection.query(query_embeddings=[query_embedding], n_results=k)

        formatted_results: List[Dict] = []
        if results["ids"] and results["ids"][0]:
            distances = (
                results["distances"][0]
                if results.get("distances")
                else [None] * len(results["ids"][0])
            )
            for i, (doc_id, doc, metadata, distance) in enumerate(
                zip(results["ids"][0], results["documents"][0], results["metadatas"][0], distances)
            ):
                # Squared L2 distance to approximate cosine similarity for normalized vectors.
                similarity = (
                    max(0.0, 1.0 - (distance / 4.0)) if distance is not None else None
                )
                formatted_results.append(
                    {
                        "rank": i + 1,
                        "transaction_id": int(doc_id),
                        "document": doc,
                        "transaction_text": metadata.get("transaction_text"),
                        "amount": metadata.get("amount"),
                        "recipient_name": metadata.get("recipient_name"),
                        "date": metadata.get("date"),
                        "distance": distance,
                        "similarity": similarity,
                    }
                )

        return formatted_results

    def retrieve_one(self, query: str) -> Optional[Dict]:
        results = self.retrieve(query, k=1)
        return results[0] if results else None
