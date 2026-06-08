FROM python:3.10-slim

RUN pip install poetry

WORKDIR /app/workers/anomaly-worker
ENV PYTHONPATH=/app/workers/anomaly-worker

COPY shared-lib /app/shared-lib
COPY workers/anomaly-worker/pyproject.toml ./pyproject.toml

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY workers/anomaly-worker/anomaly_worker ./anomaly_worker

CMD ["python", "-m", "anomaly_worker.main"]
