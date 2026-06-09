FROM python:3.10-slim

RUN pip install poetry

WORKDIR /app/migrate
ENV PYTHONPATH=/app/migrate

COPY shared-lib /app/shared-lib
COPY migrate/pyproject.toml ./pyproject.toml

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY migrate/migrate_job.py ./migrate_job.py

CMD ["python", "migrate_job.py"]
