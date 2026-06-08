from shared.app_factory import create_app

from .routes import router as transactions_router
from .validation_routes import router as validation_router

app = create_app("transactions-svc", [transactions_router, validation_router])
