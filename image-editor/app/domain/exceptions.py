class DomainError(Exception):
    status_code = 400
    detail = "domain error"


class UserAlreadyExists(DomainError):
    status_code = 409
    detail = "user already exists"


class InvalidCredentials(DomainError):
    status_code = 401
    detail = "invalid username or password"


class TaskNotFound(DomainError):
    status_code = 404
    detail = "task not found"


class TaskNotReady(DomainError):
    status_code = 409
    detail = "task is not ready yet"
