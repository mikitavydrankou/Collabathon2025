FROM python:3.10-slim

RUN pip install poetry

WORKDIR /app/services/chatbot-svc
ENV PYTHONPATH=/app/services/chatbot-svc

COPY shared-lib /app/shared-lib
COPY services/chatbot-svc/pyproject.toml ./pyproject.toml

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY services/chatbot-svc/chatbot_svc ./chatbot_svc

EXPOSE 8000

CMD ["uvicorn", "chatbot_svc.main:app", "--host", "0.0.0.0", "--port", "8000"]
