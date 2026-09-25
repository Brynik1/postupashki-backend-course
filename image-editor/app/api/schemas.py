from pydantic import BaseModel, Field


class TaskCreateRequest(BaseModel):
    # параметры обработки фото; в hw3 сюда приедет сама картинка и фильтр
    image: str | None = None
    filter_name: str | None = Field(None, alias="filter")
    parameters: dict | None = None


class TaskCreatedResponse(BaseModel):
    task_id: str


class TaskStatusResponse(BaseModel):
    status: str


class TaskResultResponse(BaseModel):
    status: str
    result: str | None = None
