FROM python:3.10-slim

RUN pip install poetry

WORKDIR /app/mcp-svc
ENV PYTHONPATH=/app/mcp-svc
ENV PYTHONUNBUFFERED=1

COPY shared-lib /app/shared-lib
COPY mcp_server/pyproject.toml ./pyproject.toml

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY mcp_server ./mcp_server

EXPOSE 8001

CMD ["uvicorn", "mcp_server.app:app", "--host", "0.0.0.0", "--port", "8001"]
