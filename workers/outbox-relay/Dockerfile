FROM python:3.10-slim

RUN pip install poetry

WORKDIR /app/workers/outbox-relay
ENV PYTHONPATH=/app/workers/outbox-relay

COPY shared-lib /app/shared-lib
COPY workers/outbox-relay/pyproject.toml ./pyproject.toml

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY workers/outbox-relay/outbox_relay ./outbox_relay

CMD ["python", "-m", "outbox_relay.main"]
