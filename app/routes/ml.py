import logging
from typing import Dict, List
from fastapi import APIRouter, HTTPException, Depends, Request, Response, status, Form
from typing import Optional
from sqlmodel import Session
from database.database import get_session
from models.mltask import MLTask, TaskStatus, MLTaskCreate, MLTaskUpdate, TaskResultRequest
from models.user import User
from services.rm.rm import rabbit_client
from services.rm.rpc import rpc_client
from services.logging.logging import get_logger
from services.crud.mltask import MLTaskService
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from auth.authenticate import authenticate_cookie
from auth.dependencies import get_current_user

logging.getLogger('pika').setLevel(logging.INFO)

logger = get_logger(logger_name=__name__)

ml_route = APIRouter()

def get_mltask_service(session: Session = Depends(get_session)) -> MLTaskService:
    return MLTaskService(session)


@ml_route.post("/send_task_result/{task_id}")
def send_task_result(
    task_id: int,
    request: TaskResultRequest,
    mltask_service: MLTaskService = Depends(get_mltask_service)
):
    """
    Принимает результат выполнения задачи и обновляет её статус.
    
    Args:
        task_id (int): ID задачи
        request (TaskResultRequest): данные с полями enhanced_prompt, image_url, context
    
    Returns:
        dict: Успешный ответ
    """
    try:
        result_dict = {
            "enhanced_prompt": request.enhanced_prompt,
            "image_url": request.image_url,
            "context": request.context
        }

        logger.info(f"!!!!!!!!Launch mltask_service.set_result")
        updated_task = mltask_service.set_result(task_id, result_dict)
        logger.info(f"!!!!!!!!Task result has been set: {result_dict}")

        if not updated_task:
            raise HTTPException(status_code=404, detail="Задача не найдена")

        return {"message": "Результат успешно установлен", "task_id": task_id}
    
    except Exception as e:
        logger.error(f"Unexpected error in sending task result: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@ml_route.post("/update_task/{task_id}")
async def update_task_result(
    task_id: int,
    data: dict,
    mltask_service: MLTaskService = Depends(get_mltask_service)
):
    """
    Принимает результат выполнения ML-задачи и обновляет статус/результат.
    Использует готовые методы MLTaskService.
    """
    try:
        status = data.get("status")
        result_data = data.get("result", {})  # словарь с полями

        if status == "completed":
            updated_task = mltask_service.update(
                task_id,
                MLTaskUpdate(**{
                    "status": TaskStatus.COMPLETED,
                    "enhanced_prompt": result_data.get("enhanced_prompt"),
                    "image_url": result_data.get("image_url"),
                    "context": result_data.get("context")
                })
            )
        elif status == "failed":
            updated_task = mltask_service.update(
                task_id,
                MLTaskUpdate(
                    status=TaskStatus.FAILED,
                    context=result_data.get("context"),  # например, для отладки
                    enhanced_prompt=result_data.get("enhanced_prompt")
                )
            )
        else:
            raise HTTPException(status_code=400, detail="Неизвестный статус задачи")

        if not updated_task:
            raise HTTPException(status_code=404, detail="Задача не найдена")

        return {
            "status": "ok",
            "task_id": task_id,
            "updated_status": updated_task.status,
            "updated_task": updated_task
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении задачи: {str(e)}")
     
@ml_route.post("/send_task", response_model=dict)
async def send_task(
    request: Request,
    message: str = Form(...),
    brandbook_id: Optional[str] = Form(None),
    mltask_service: MLTaskService = Depends(get_mltask_service),
    current_user: User = Depends(get_current_user) 
):
    """
    Отправляет ML-задачу от текущего пользователя.
    user_id берётся из JWT-токена через Depends(get_current_user)
    """
    user_id = current_user.id

    try:
        task_create = MLTaskCreate(
            question=message,
            user_id=user_id,
            brandbook_id=brandbook_id,
            status=TaskStatus.NEW
        )
        created_task = mltask_service.create(task_create)
        logger.info(f"Задача создана: {created_task}")

        rabbit_client.send_to_queue("rag_queue", {
            "task_id": created_task.id,
            "question": message,
            "brandbook_id": brandbook_id
        })

        mltask_service.set_status(created_task.id, TaskStatus.QUEUED)

        return {"message": "Задача отправлена в очередь", "task_id": created_task.id}

    except Exception as e:
        logger.error(f"Ошибка при создании задачи: {str(e)}")
        if 'created_task' in locals():
            mltask_service.set_status(created_task.id, TaskStatus.FAILED)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@ml_route.post("/send_task_rpc", response_model=Dict[str, str])
async def send_task_rpc(
    message: str,
    user_id: int,
    mltask_service: MLTaskService = Depends(get_mltask_service)
) -> Dict[str, str]:
    """
    Endpoint for sending ML task using RPC.

    Args:
        message (str): The message to be sent.
        user_id (int): ID of the user creating the task.

    Returns:
        Dict[str, str]: Response message with original and processed text.
    """
    
    try:
        # Create task using service
        task_create = MLTaskCreate(
            question=message,
            user_id=user_id,
            status=TaskStatus.NEW
        )
        ml_task = mltask_service.create(task_create) 

        logger.info(f"Sending RPC request with message: {message}")
        result = rpc_client.call(text=message)
        logger.info(f"Received RPC response: {result}")

        # Update task with result using service
        mltask_service.set_result(ml_task.id, result)
        
        return {"original": message, "processed": result}
    except Exception as e:
        logger.error(f"Unexpected error in RPC call: {str(e)}")
        if ml_task:
            mltask_service.set_status(ml_task.id, TaskStatus.FAILED)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@ml_route.get("/tasks", response_model=List[MLTask])
async def get_all_tasks(
    mltask_service: MLTaskService = Depends(get_mltask_service)
):
    """Get all ML tasks."""
    return mltask_service.get_all()

@ml_route.get("/tasks/{task_id}", response_model=MLTask)
async def get_task(
    task_id: int,
    mltask_service: MLTaskService = Depends(get_mltask_service)
):
    """Get ML task by ID."""
    task = mltask_service.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@ml_route.get("/tasks/user/{user_id}", response_model=List[MLTask])
async def get_tasks_by_user(user_id: int, mltask_service: MLTaskService = Depends(get_mltask_service)) -> List[MLTask]:
    """Получает все задачи пользователя по его ID"""
    tasks = mltask_service.get_all_by_user(user_id)
    if not tasks:
        raise HTTPException(status_code=404, detail="Задачи не найдены")
    return tasks