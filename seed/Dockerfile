FROM python:3.10-slim

RUN pip install poetry

WORKDIR /app/seed
ENV PYTHONPATH=/app/seed

COPY shared-lib /app/shared-lib
COPY seed/pyproject.toml ./pyproject.toml

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY seed/seed_job.py ./seed_job.py

CMD ["python", "seed_job.py"]
