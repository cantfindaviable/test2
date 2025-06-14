from typing import Optional
import os

from models.mltask import TaskStatus
from services.crud.mltask import MLTaskService
from services.ml.rag_searcher import RAGSearcher
from services.ml.prompt_enhancer import PromptEnhancer
from services.ml.image_generator import ImageGenerator

class DesignGenerationTask:
    def __init__(
        self,
        rag_searcher: RAGSearcher,
        prompt_enhancer: PromptEnhancer,
        image_generator: ImageGenerator,
        task_service: MLTaskService
    ):
        self.rag_searcher = rag_searcher
        self.prompt_enhancer = prompt_enhancer
        self.image_generator = image_generator
        self.task_service = task_service

    def run(self, task_id: int, brand_filename: str, output_path: str) -> Optional[str]:
        """
        Полный пайплайн генерации дизайна:
        1. Поиск по брендбуку через RAG
        2. Уточнение промпта через LLM (Ollama или Qwen)
        3. Генерация изображения через DreamShaper XL / SDXL
        4. Обновление задачи в БД
        """
        try:
            # Шаг 1: Получаем задачу из БД
            ml_task = self.task_service.get(task_id)

            # Шаг 2: Обновляем статус на PROCESSING
            self.task_service.set_status(task_id, TaskStatus.PROCESSING)

            # Шаг 3: Поиск по брендбуку
            search_result = self.rag_searcher.search(
                query=ml_task.question,
                filename=brand_filename,
                k=1
            )
            context = "\n".join([item["text"] for item in search_result])

            # Шаг 4: Уточнение промпта
            enhanced_prompt = self.prompt_enhancer.enhance_prompt(ml_task.question, context)

            # Шаг 5: Генерация изображения
            result_path = self.image_generator.generate(enhanced_prompt, output_path)

            if result_path:
                # Шаг 6: Сохраняем результат в БД
                self.task_service.set_result(task_id, result_path)
                return result_path
            else:
                self.task_service.set_status(task_id, TaskStatus.FAILED)
                return None
        except Exception as e:
            self.task_service.set_status(task_id, TaskStatus.FAILED)
            return None