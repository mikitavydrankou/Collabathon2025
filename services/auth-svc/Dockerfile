FROM python:3.10-slim

RUN pip install poetry

WORKDIR /app/services/auth-svc
ENV PYTHONPATH=/app/services/auth-svc

COPY shared-lib /app/shared-lib
COPY services/auth-svc/pyproject.toml ./pyproject.toml

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY services/auth-svc/auth_svc ./auth_svc

EXPOSE 8000

CMD ["uvicorn", "auth_svc.main:app", "--host", "0.0.0.0", "--port", "8000"]
