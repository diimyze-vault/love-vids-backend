from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Meta(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"


class UnifiedResponse(BaseModel, Generic[T]):
    status: str = "success"
    data: Optional[T] = None
    meta: Meta = Field(default_factory=Meta)


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    code: Optional[str] = None
    meta: Meta = Field(default_factory=Meta)
