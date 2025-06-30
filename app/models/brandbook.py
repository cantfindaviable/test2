from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum

# Условный импорт для избежания циклических зависимостей
if TYPE_CHECKING:
    from models.event import Event
    from models.mltask import MLTask

class BrandbookBase(SQLModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    file_path: str = Field(..., max_length=255)

class Brandbook(BrandbookBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: Optional[int] = Field(default=None, foreign_key="event.id")
    event: Optional["Event"] = Relationship(back_populates="brandbooks")

    # mltask_id: Optional[int] = Field(default=None, foreign_key="mltask.id")
    # mltask: Optional["MLTask"] = Relationship(back_populates="brandbooks")

    def __str__(self) -> str:
        return f"Brandbook ID: {self.id}, Name: {self.name}"

class BrandbookCreate(BrandbookBase):
    event_id: Optional[int] = None

class BrandbookUpdate(BrandbookBase):
    name: Optional[str] = None
    file_path: Optional[str] = None


class ProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class BrandbookProcessing(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    filename: str
    file_path: str
    status: ProcessingStatus = Field(default=ProcessingStatus.UPLOADED)
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: datetime | None = None
    error_message: str | None = None