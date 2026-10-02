from fastapi import APIRouter, Depends, Request, Response, Security

from app.api import schemas
from app.api.deps import get_current_session, get_task_service
from app.application.task_service import TaskService
from app.domain.user import Session

router = APIRouter(tags=["tasks"])


@router.post("/task", response_model=schemas.TaskCreatedResponse, status_code=201)
def create_task(
    request: schemas.TaskCreateRequest | None = None,
    session: Session = Security(get_current_session),
    task_service: TaskService = Depends(get_task_service),
) -> schemas.TaskCreatedResponse:
    payload = request.model_dump() if request is not None else {}
    task = task_service.create_task(payload)
    return schemas.TaskCreatedResponse(task_id=str(task.task_id))


@router.get("/status/{task_id}", response_model=schemas.TaskStatusResponse)
def get_status(
    task_id: str,
    session: Session = Security(get_current_session),
    task_service: TaskService = Depends(get_task_service),
) -> schemas.TaskStatusResponse:
    return schemas.TaskStatusResponse(**task_service.get_status(task_id))


@router.get("/result/{task_id}", response_model=schemas.TaskResultResponse)
def get_result(
    task_id: str,
    request: Request,
    session: Session = Security(get_current_session),
    task_service: TaskService = Depends(get_task_service),
):
    # браузеру отсылаем сам png, API-клиентам - json с base64 (readme hw3)
    if "image/" in request.headers.get("Accept", ""):
        image, _format = task_service.get_image(task_id)
        return Response(content=image, media_type="image/png")
    return schemas.TaskResultResponse(**task_service.get_result(task_id).to_dict())


@router.post("/commit", response_model=schemas.TaskStatusResponse)
def commit(
    request: schemas.CommitRequest,
    task_service: TaskService = Depends(get_task_service),
) -> schemas.TaskStatusResponse:
    """Webhook для ImageProcessor: обработчик кладет готовый результат"""
    task = task_service.commit_result(request.task_id, request.image)
    return schemas.TaskStatusResponse(status=task.status.value)
