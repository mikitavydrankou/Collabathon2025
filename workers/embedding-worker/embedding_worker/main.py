import logging
import os

import chromadb
from openai import OpenAI

from shared.messaging import TRANSACTIONS_TOPIC, consume
from shared.tracing import init_tracing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("embedding_worker")

EMBED_MODEL = "text-embedding-3-small"
COLLECTION = "transactions"

_openai = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
_chroma = chromadb.HttpClient(
    host=os.getenv("CHROMA_HOST", "chroma"),
    port=int(os.getenv("CHROMA_PORT", "8000")),
)


def handle(event: dict) -> None:
    text = event.get("enhanced_text") or event.get("transaction_text") or ""
    if not text:
        return

    vector = _openai.embeddings.create(model=EMBED_MODEL, input=[text]).data[0].embedding
    metadata = {
        k: event[k]
        for k in ("transaction_id", "amount", "recipient_name", "date")
        if event.get(k) is not None
    }
    collection = _chroma.get_or_create_collection(COLLECTION)
    collection.upsert(
        ids=[str(event["transaction_id"])],
        documents=[text],
        embeddings=[vector],
        metadatas=[metadata],
    )
    logger.info("embedded transaction %s", event["transaction_id"])


def main() -> None:
    init_tracing("embedding-worker")
    consume(TRANSACTIONS_TOPIC, "embeddings", handle)


if __name__ == "__main__":
    main()
