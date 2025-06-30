from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING, List
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from models.user import User
    from models.event import Event

class TaskStatus(str, Enum):
    """Статусы выполнения ML задачи"""
    NEW = "new"              # Новая задача
    QUEUED = "queued"        # В очереди на выполнение
    RAG_SEARCHING = "rag_searching"
    LLM_PROMPT_ENHANCEMENT = "llm_prompt_enhancement"
    IMAGE_GENERATION = "image_generation"
    COMPLETED = "completed"   # Выполнена
    FAILED = "failed"        # Ошибка выполнения

class MLTaskBase(SQLModel):
    """
    Базовая модель ML задачи.
    
    Атрибуты:
        status (TaskStatus): Текущий статус задачи
        result (Optional[str]): Результат обработки ML моделью
    """
    status: TaskStatus = Field(default=TaskStatus.NEW)
    question: Optional[str] = Field(default=None)
    brandbook_id: Optional[str] = Field(default=None)
    enhanced_prompt: Optional[str] = Field(default=None)
    image_url: Optional[str] = Field(default=None)
    context: Optional[str] = Field(default=None)
    
class MLTask(MLTaskBase, table=True):
    """
    Модель ML задачи для хранения в базе данных.
    
    Атрибуты:
        id (int): Уникальный идентификатор задачи
        event_id (int): ID связанного события
        user_id (int): ID пользователя, создавшего задачу
        created_at (datetime): Время создания задачи
        updated_at (datetime): Время последнего обновления
        creator (User): Связь с создателем
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    brandbook_id: Optional[str] = Field(default=None)
    # event_id: Optional[int] = Field(foreign_key="event.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    creator: Optional["User"] = Relationship(
        back_populates="ml_tasks",
        sa_relationship_kwargs={"lazy": "selectin"}
    )
    # event: Optional[Event] = Relationship(back_populates="mltask")

    def to_queue_message(self) -> dict:
        """Формирует сообщение для отправки в RabbitMQ"""
        return {
            "task_id": self.id,
            "question": self.question,
        }

class MLTaskCreate(MLTaskBase):
    """DTO для создания новой ML задачи"""
    question: str
    user_id: int
    status: TaskStatus
    brandbook_id: str

class MLTaskUpdate(MLTaskBase):
    """DTO для обновления существующей ML задачи"""
    status: Optional[TaskStatus] = None
    question: Optional[str] = None
    brandbook_id: Optional[str] = None
    enhanced_prompt: Optional[str] = None
    image_url: Optional[str] = None
    context: Optional[str] = None

class TaskResultRequest(MLTaskBase):
    enhanced_prompt: Optional[str] = None
    image_url: Optional[str] = None
    context: Optional[str] = None