from fastapi import APIRouter, Depends

from app.api import schemas
from app.api.deps import get_auth_service
from app.application.auth_service import AuthService

router = APIRouter(tags=["auth"])


@router.post("/register", status_code=201)
def register(
    request: schemas.RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    user = auth_service.register(request.username, request.password)
    return {"username": user.username, "id": user.id}


@router.post("/login", response_model=schemas.LoginResponse)
def login(
    request: schemas.LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> schemas.LoginResponse:
    session = auth_service.login(request.username, request.password)
    return schemas.LoginResponse(token=session.session_id)
