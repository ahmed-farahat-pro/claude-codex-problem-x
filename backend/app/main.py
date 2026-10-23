"""App factory. Run with: uvicorn app.main:create_app --factory --reload"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import __version__, db, retrieval
from .api import router
from .config import Settings
from .content import ContentRegistry
from .errors import ApiError
from .llm import build_models
from .llm.base import LabGenerator, TutorModel
from .services import Services


def create_app(
    settings: Settings | None = None,
    *,
    generator: LabGenerator | None = None,
    tutor: TutorModel | None = None,
) -> FastAPI:
    settings = (settings or Settings()).resolved()
    registry = ContentRegistry.load(settings.content_dir)
    default_generator, default_tutor = build_models(settings)
    services = Services(settings, registry, generator or default_generator, tutor or default_tutor)

    conn = db.connect(settings.db_path)
    try:
        db.init_schema(conn)
        retrieval.index_passages(conn, registry.all_passages())
    finally:
        conn.close()

    app = FastAPI(title="4weeks.ai backend", version=__version__)
    app.state.services = services
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ApiError)
    def api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(status_code=exc.status, content=exc.body())

    app.include_router(router)
    return app
