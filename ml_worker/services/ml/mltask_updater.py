import requests
import os
from typing import Dict
import logging

logger = logging.getLogger(__name__)

API_URL = os.getenv("APP_API_URL", "http://app:8080")
UPDATE_TASK_ENDPOINT = "/api/ml/update_task/"

def update_task_result_in_api(task_id: int, result: dict):
    """
    Отправляет результат выполнения задачи в API.
    
    Args:
        task_id (int): ID задачи
        result (dict): Словарь с полями enhanced_prompt, image_url, context
    
    Returns:
        dict: Ответ от сервера
    """
    url = f"{API_URL}{UPDATE_TASK_ENDPOINT}{task_id}"
    
    try:
        # Передаём данные как JSON, без оборачивания в "result"
        payload = {
            "status": "completed",
            "enhanced_prompt": result.get("enhanced_prompt"),
            "image_url": result.get("image_url"),
            "context": result.get("context")
        }

        response = requests.post(url, json=payload)
        
        if response.status_code == 404:
            logger.error(f"Маршрут {url} не найден!")
            raise Exception(f"Маршрут не найден: {response.text}")
        elif response.status_code != 200:
            raise Exception(f"Сервер вернул {response.status_code}: {response.text}")

        return response.json()

    except Exception as e:
        logger.error(f"Не удалось отправить результат задачи в API: {e}")
        raise

# def update_task_result_in_api(task_id: int, result: dict):
#     """
#     Отправляет результат выполнения задачи в основное API.
#     """
#     url = f"{API_URL}{UPDATE_TASK_ENDPOINT}{task_id}"
    
#     try:
#         response = requests.post(url, json={"status": "completed", "result": result})
        
#         if response.status_code == 404:
#             logger.error(f"Маршрут {UPDATE_TASK_ENDPOINT} не найден!")
#             raise Exception(f"Маршрут не найден: {response.text}")
#         elif response.status_code != 200:
#             raise Exception(f"Ошибка сервера ({response.status_code}): {response.text}")

#         return response.json()

#     except Exception as e:
#         logger.error(f"Не удалось отправить результат задачи в API: {e}")
#         raise