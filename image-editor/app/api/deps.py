from fastapi import HTTPException, Request

from app.application.auth_service import AuthService
from app.application.task_service import TaskService
from app.container import Container
from app.domain.exceptions import InvalidCredentials
from app.domain.user import Session


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_task_service(request: Request) -> TaskService:
    return get_container(request).task_service


def get_auth_service(request: Request) -> AuthService:
    return get_container(request).auth_service


def get_current_session(request: Request) -> Session:
    """Достает токен из Authorization: Bearer ... и проверяет его"""
    auth_service = get_container(request).auth_service
    header = request.headers.get("Authorization") or ""
    if not header.startswith("Bearer "):
        raise InvalidCredentials()
    session = auth_service.resolve_token(header.removeprefix("Bearer ").strip())
    if session is None:
        raise InvalidCredentials()
    return session
