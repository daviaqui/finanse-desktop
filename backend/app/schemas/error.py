from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Public error contract returned by every API failure."""

    detail: str
    code: str
