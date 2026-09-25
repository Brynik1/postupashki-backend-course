from pydantic import BaseModel


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str


class TaskCreateRequest(BaseModel):
    # параметры обработки фото; в hw3 сюда приедет сама картинка и фильтр
    image: str | None = None
    filter: dict | None = None  # {"name": ..., "parameters": {...}}
    parameters: dict | None = None


class TaskCreatedResponse(BaseModel):
    task_id: str


class TaskStatusResponse(BaseModel):
    status: str


class TaskResultResponse(BaseModel):
    status: str
    result: str | None = None
