FROM python:3.10-slim

RUN pip install poetry

WORKDIR /app/backend

COPY backend/pyproject.toml ./pyproject.toml
COPY backend/src ./src
COPY shared ../shared

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY backend ./

EXPOSE 8000

CMD ["poetry", "run", "start"]
