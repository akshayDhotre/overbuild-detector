from fastapi import FastAPI

from overbuild.api.routes import router
from overbuild.observability.logging import configure_logging
from overbuild.observability.middleware import add_observability


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title="OverBuild Detector",
        description="Before you build, check if it already exists.",
        version="0.1.0",
    )
    app.include_router(router)
    add_observability(app)
    return app


app = create_app()
