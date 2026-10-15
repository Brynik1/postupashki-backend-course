import base64
import binascii
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class RegisterRequest(BaseModel):
    # пустой/одним словом username не пропускаем, пароль тоже не пустой
    username: str = Field(min_length=3, max_length=64, pattern=r"^\S+$")
    password: str = Field(min_length=4, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str


class FilterRequest(BaseModel):
    """Какой фильтр применить и с какими параметрами"""

    name: Literal["Negative", "FlipX", "Blur", "Sharpen"]
    parameters: dict | None = None

    @model_validator(mode="after")
    def check_parameters(self) -> "FilterRequest":
        params = self.parameters or {}
        allowed = {"Blur": {"radius"}, "Sharpen": {"percent"}}.get(self.name, set())
        unknown = set(params) - allowed
        if unknown:
            raise ValueError(f"unexpected parameters for {self.name}: {sorted(unknown)}")
        if self.name == "Blur":
            radius = params.get("radius", 2.0)
            if not isinstance(radius, int | float) or not 0 <= float(radius) <= 64:
                raise ValueError("Blur radius must be a number between 0 and 64")
        if self.name == "Sharpen":
            percent = params.get("percent", 150)
            if not isinstance(percent, int | float) or not 1 <= percent <= 500:
                raise ValueError("Sharpen percent must be a number between 1 and 500")
        return self


class TaskCreateRequest(BaseModel):
    # картинка обязательна и должна быть валидным base64
    image: str = Field(min_length=1)
    filter: FilterRequest

    @field_validator("image")
    @classmethod
    def valid_base64(cls, value: str) -> str:
        try:
            base64.b64decode(value, validate=True)
        except (binascii.Error, ValueError):
            raise ValueError("image must be valid base64")
        return value


class TaskCreatedResponse(BaseModel):
    task_id: str


class TaskStatusResponse(BaseModel):
    status: str


class TaskResultResponse(BaseModel):
    status: str
    result: str | None = None


class CommitRequest(BaseModel):
    # процессор либо присылает готовую картинку, либо переводит таску в failed
    task_id: str
    image: str | None = None
    error: str | None = None

    @model_validator(mode="after")
    def one_of_image_or_error(self) -> "CommitRequest":
        if (self.image is None) == (self.error is None):
            raise ValueError("commit must have exactly one of image/error")
        return self
