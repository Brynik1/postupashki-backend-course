import time

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api import auth, tasks
from app.config import Settings
from app.container import Container
from app.domain.exceptions import DomainError
from app.infrastructure.metrics import API_LATENCY, API_REQUESTS


def create_app() -> FastAPI:
    app = FastAPI(
        title="ImageStudio API",
        description="Сервис обработки фотографий: загрузка задач, статус, результат.",
        version="0.1.0",
    )
    app.state.container = Container(Settings.from_env())
    app.include_router(tasks.router)
    app.include_router(auth.router)

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, error: DomainError) -> JSONResponse:
        return JSONResponse(status_code=error.status_code, content={"detail": error.detail})

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        request_seconds = time.perf_counter() - started
        API_LATENCY.labels(endpoint=request.url.path).observe(request_seconds)
        API_REQUESTS.labels(
            method=request.method,
            endpoint=request.url.path,
            status=str(response.status_code),
        ).inc()
        return response

    @app.get("/metrics", tags=["system"])
    def metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/health", tags=["system"])
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
