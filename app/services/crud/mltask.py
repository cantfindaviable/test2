from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select

from models.mltask import MLTask, MLTaskCreate, MLTaskUpdate, TaskStatus

class MLTaskService:
    def __init__(self, session: Session):
        self.session = session

    def create(self, task_create: MLTaskCreate) -> MLTask:
        """Создает новую ML задачу"""
        task = MLTask(
            status=task_create.status,
            question=task_create.question,
            brandbook_id=task_create.brandbook_id,
            user_id=task_create.user_id
        )
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def get(self, task_id: int) -> Optional[MLTask]:
        """Получает задачу по ID"""
        return self.session.get(MLTask, task_id)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[MLTask]:
        """Получает список всех задач с пагинацией"""
        statement = select(MLTask).offset(skip).limit(limit)
        return self.session.exec(statement).all()

    def update(self, task_id: int, task_update: MLTaskUpdate) -> Optional[MLTask]:
        """Обновляет существующую задачу"""
        task = self.get(task_id)
        if not task:
            return None
        
        update_data = task_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
        
        task.updated_at = datetime.utcnow()
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def delete(self, task_id: int) -> bool:
        """Удаляет задачу по ID"""
        task = self.get(task_id)
        if not task:
            return False
        
        self.session.delete(task)
        self.session.commit()
        return True

    def set_status(self, task_id: int, status: TaskStatus) -> Optional[MLTask]:
        """Обновляет статус задачи"""
        return self.update(task_id, MLTaskUpdate(status=status))

    def set_result(self, task_id: int, result_data: dict) -> Optional[MLTask]:
        """
        Устанавливает результат выполнения задачи как набор полей.
        
        Args:
            task_id (int): ID задачи
            result_data (dict): Словарь с полями: enhanced_prompt, image_url, context
        
        Returns:
            Optional[MLTask]: Обновлённая задача или None
        """
        try:
            # Создаем объект MLTaskUpdate из данных
            update_data = {
                "status": TaskStatus.COMPLETED,
                "enhanced_prompt": result_data.get("enhanced_prompt"),
                "image_url": result_data.get("image_url"),
                "context": result_data.get("context")
            }

            task_update = MLTaskUpdate(**update_data)
            updated_task = self.update(task_id, task_update)

            return updated_task

        except Exception as e:
            raise
        
    def get_all_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[MLTask]:
        """
        Получает список ML-задач для конкретного пользователя с пагинацией
        
        Args:
            user_id (int): ID пользователя
            skip (int): Количество записей для пропуска
            limit (int): Максимальное количество возвращаемых записей
        
        Returns:
            List[MLTask]: Список задач пользователя
        """
        statement = (
            select(MLTask)
            .where(MLTask.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return self.session.exec(statement).all()