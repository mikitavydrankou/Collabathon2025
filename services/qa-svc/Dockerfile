FROM python:3.10-slim

RUN pip install poetry

WORKDIR /app/services/qa-svc
ENV PYTHONPATH=/app/services/qa-svc

COPY shared-lib /app/shared-lib
COPY services/qa-svc/pyproject.toml ./pyproject.toml

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY services/qa-svc/qa_svc ./qa_svc

EXPOSE 8000

CMD ["uvicorn", "qa_svc.main:app", "--host", "0.0.0.0", "--port", "8000"]
