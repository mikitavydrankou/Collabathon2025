import os
import json
from pathlib import Path

import chromadb
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()

openai_api_key = os.environ.get("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("Brakuje zmiennej środowiskowej OPENAI_API_KEY")

# klient OpenAI
oa_client = OpenAI(api_key=openai_api_key)

# 2. Funkcja pomocnicza do liczenia embeddingów
def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Liczy embeddingi dla listy tekstów, używając modelu text-embedding-3-small.
    Zwraca listę wektorów floatów.
    """
    response = oa_client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    # response.data to lista obiektów z polem .embedding
    return [item.embedding for item in response.data]


# 3. Wczytanie transakcji z pliku JSON
SCRIPT_DIR = Path(__file__).parent
DATA_PATH = SCRIPT_DIR / "transactions.json"

print(f"Wczytywanie transakcji z: {DATA_PATH}")
with DATA_PATH.open("r", encoding="utf-8") as f:
    transactions = json.load(f)
print(f"✓ Wczytano {len(transactions)} transakcji")

# Spodziewamy się struktury:
# [
#   {
#     "transaction_id": 1,
#     "transaction_text": "...",
#     "enhanced_text": "...",
#     "amount": 5000.0,
#     "recipient_name": "Kate Davis",
#     "date": "2025-01-15T10:30:00"
#   },
#   ...
# ]

# 4. Przygotowanie danych do indeksowania w Chroma
ids: list[str] = []
documents: list[str] = []
metadatas: list[dict] = []

for tx in transactions:
    ids.append(str(tx["transaction_id"]))           # np. "1"
    documents.append(tx["enhanced_text"])           # kontekst do RAG
    metadatas.append(
        {
            "transaction_id": tx["transaction_id"],
            "transaction_text": tx["transaction_text"],
            "amount": tx["amount"],
            "recipient_name": tx["recipient_name"],
            "date": tx["date"],
        }
    )

# 5. Liczymy embeddingi dla wszystkich dokumentów
print(f"\nTworzenie embeddingów dla {len(documents)} transakcji...")
embeddings = embed_texts(documents)
print(f"✓ Utworzono {len(embeddings)} embeddingów")


# 7. Tworzymy / otwieramy bazę Chroma (persist na dysku)
print(f"\nDodawanie do ChromaDB...")
chroma_store_path = SCRIPT_DIR / "chroma_store"
chroma_client = chromadb.PersistentClient(path=str(chroma_store_path))

# Używamy kolekcji bez embedding_function, bo embeddingi podajemy sami
collection = chroma_client.get_or_create_collection(name="transactions")

# 8. Dodajemy dane do kolekcji
collection.add(
    ids=ids,
    documents=documents,
    metadatas=metadatas,
    embeddings=embeddings,
)

print(f"✓ Dodano {len(ids)} transakcji do kolekcji 'transactions' w ChromaDB")