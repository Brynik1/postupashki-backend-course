from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import tasks
from app.config import Settings
from app.container import Container
from app.domain.exceptions import DomainError


def create_app() -> FastAPI:
    app = FastAPI(
        title="ImageStudio API",
        description="Сервис обработки фотографий: загрузка задач, статус, результат.",
        version="0.1.0",
    )
    app.state.container = Container(Settings())
    app.include_router(tasks.router)

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, error: DomainError) -> JSONResponse:
        return JSONResponse(status_code=error.status_code, content={"detail": error.detail})

    @app.get("/health", tags=["system"])
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
