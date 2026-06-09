"""Shared FastAPI application factory.

Every service builds its app here so CORS, health, metrics and startup are
defined once instead of being duplicated per service.
"""

import logging
import os
from typing import Iterable

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from shared.db import test_connection

logger = logging.getLogger(__name__)


def create_app(
    title: str,
    routers: Iterable[APIRouter],
) -> FastAPI:
    app = FastAPI(title=title)

    origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials="*" not in origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for router in routers:
        app.include_router(router)

    Instrumentator().instrument(app).expose(app)

    # Schema + seed are applied out-of-band by the migrate/seed Jobs, never on
    # service startup — so N replicas don't race on `alembic upgrade`.

    @app.get("/")
    def root():
        return {"status": "ok", "service": title}

    @app.get("/health")
    def health():
        return {"database": test_connection()}

    @app.get("/usage")
    def usage():
        from shared.usage import llm_usage

        return llm_usage()

    @app.post("/admin/reset-db")
    def reset_db():
        """Wipe and re-seed demo data. Exposed for the in-app System page."""
        from shared.seed import reset_database

        reset_database()
        return {"status": "ok", "message": "Demo data reset"}

    return app
