FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy shared directory (needed by mcp_server)
COPY shared /app/shared

# Copy mcp_server pyproject.toml and install dependencies
COPY mcp_server/pyproject.toml /app/mcp_server/
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir poetry && \
    cd /app/mcp_server && \
    poetry config virtualenvs.create false && \
    poetry config installer.max-workers 10 && \
    poetry install --no-root --no-interaction --no-ansi || \
    (echo "Poetry install failed, retrying in 10 seconds..." && sleep 10 && poetry install --no-root --no-interaction --no-ansi)

# Copy mcp_server application code
COPY mcp_server /app/mcp_server

# Set Python path to include both mcp_server and shared
ENV PYTHONPATH=/app:/app/mcp_server

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port 8001 for MCP server
EXPOSE 8001

# Run the MCP FastAPI server
CMD ["uvicorn", "mcp_server.app:app", "--host", "0.0.0.0", "--port", "8001"]

