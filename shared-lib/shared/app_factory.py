"""Shared FastAPI application factory.

Every service builds its app here so CORS, health, metrics and startup are
defined once instead of being duplicated per service.
"""

import logging
import os
from pathlib import Path
from typing import Iterable

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

import shared
from shared.db import init_db, test_connection
from shared.seed import seed_database

logger = logging.getLogger(__name__)


def run_migrations() -> None:
    """Apply Alembic migrations to head. Idempotent and safe to run per service."""
    from alembic import command
    from alembic.config import Config

    base = Path(shared.__file__).resolve().parent.parent
    cfg = Config(str(base / "alembic.ini"))
    cfg.set_main_option("script_location", str(base / "alembic"))
    command.upgrade(cfg, "head")


def create_app(
    title: str,
    routers: Iterable[APIRouter],
    *,
    seed_capable: bool = False,
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

    @app.on_event("startup")
    def _startup() -> None:
        try:
            init_db()
            run_migrations()
            if seed_capable and _seed_enabled():
                seed_database()
        except Exception:
            logger.exception("startup database init failed")

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


def _seed_enabled() -> bool:
    return os.getenv("SEED_ON_START", "false").lower() in ("1", "true", "yes")
