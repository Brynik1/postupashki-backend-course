from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    # пустой/одним словом username не пропускаем, пароль тоже не пустой
    username: str = Field(min_length=3, max_length=64, pattern=r"^\S+$")
    password: str = Field(min_length=4, max_length=128)


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


class CommitRequest(BaseModel):
    task_id: str
    image: str  # base64 png от ImageProcessor
