from fastapi import Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.auth_service import AuthService
from app.application.task_service import TaskService
from app.container import Container
from app.domain.exceptions import NotAuthorized
from app.domain.user import Session

# схема для Swagger UI: кнопка Authorize -> "Bearer <token>"
_bearer = HTTPBearer(auto_error=False)


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_task_service(request: Request) -> TaskService:
    return get_container(request).task_service


def get_auth_service(request: Request) -> AuthService:
    return get_container(request).auth_service


def get_current_session(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> Session:
    """Проверяет Authorization: Bearer ... и сессию в хранилище"""
    auth_service = get_container(request).auth_service
    if credentials is None:
        raise NotAuthorized()
    session = auth_service.resolve_token(credentials.credentials)
    if session is None:
        raise NotAuthorized()
    return session
