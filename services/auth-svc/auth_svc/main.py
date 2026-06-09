from shared.app_factory import create_app

from .routes import router

app = create_app("auth-svc", [router])
