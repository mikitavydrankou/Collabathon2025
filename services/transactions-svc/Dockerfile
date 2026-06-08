FROM python:3.10-slim

RUN pip install poetry

WORKDIR /app/services/transactions-svc
ENV PYTHONPATH=/app/services/transactions-svc

COPY shared-lib /app/shared-lib
COPY services/transactions-svc/pyproject.toml ./pyproject.toml

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY services/transactions-svc/transactions_svc ./transactions_svc

EXPOSE 8000

CMD ["uvicorn", "transactions_svc.main:app", "--host", "0.0.0.0", "--port", "8000"]
