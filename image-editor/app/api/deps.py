from fastapi import Request

from app.application.task_service import TaskService
from app.container import Container


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_task_service(request: Request) -> TaskService:
    return get_container(request).task_service
