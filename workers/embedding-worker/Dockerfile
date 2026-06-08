FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

WORKDIR /app/workers/embedding-worker
ENV PYTHONPATH=/app/workers/embedding-worker

COPY shared-lib /app/shared-lib
COPY workers/embedding-worker/pyproject.toml ./pyproject.toml

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY workers/embedding-worker/embedding_worker ./embedding_worker

CMD ["python", "-m", "embedding_worker.main"]
