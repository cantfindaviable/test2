from services.ml.rag_searcher import RAGSearcher
from services.ml.prompt_enhancer import PromptEnhancer
from services.ml.image_generator import ImageGenerator
from services.ml.mltask_updater import update_task_result_in_api
from chromadb_manager import ChromaDBManager
from llm import do_task

import logging
logger = logging.getLogger(__name__)

def process_task(task_data):
    """
    Основной обработчик задачи.
    Выполняет полный цикл: RAG-поиск → улучшение промпта → генерация изображения → обновление статуса
    """
    try:
        logger.info("Начало обработки задачи", extra={"task_id": task_data.get("task_id")})
        
        # 1. Получаем данные из сообщения
        task_id = task_data.get("task_id")
        question = task_data.get("question")
        brandbook_id = task_data.get("brandbook_id")

        logger.debug("Получены данные для обработки",
                     extra={"task_id": task_id, "question": question, "brandbook_id": brandbook_id})

        if not all([task_id, question]):
            logger.warning("Отсутствуют ключевые поля", extra={"task_id": task_id})
            raise ValueError("task_id и question обязательны для обработки")
        
        logger.info("Подключение к ChromaDB", extra={"task_id": task_id})
        chroma_manager = ChromaDBManager(host="chromadb", port=8000)

        # 2. Инициализируем RAG-поиск
        logger.info("Запуск RAG-поиска", extra={"task_id": task_id})
        rag_searcher = RAGSearcher(chroma_manager)
        context = rag_searcher.search(question, collection_name=brandbook_id)

        summarized_context = do_task(f"summarize this text. leave only the essence, as if you were writing a technical specification for a designer, and don't write anything extra {context}")
        # logger.info("Найденный контекст", extra={"task_id": task_id, "context": context})
        logger.info(f"Найденный контекст {context}")
        # logger.info("Найденный сокращенный контекст", extra={"task_id": task_id, "summarized_context": summarized_context})
        logger.info(f"Найденный сокращенный контекст {summarized_context}")

        # 3. Улучшаем промпт
        logger.info("Улучшение промпта", extra={"task_id": task_id})
        prompt_enhancer = PromptEnhancer()
        enhanced_prompt = prompt_enhancer.enhance_prompt(question, context)

        logger.debug("Улучшенный промпт", extra={"task_id": task_id, "enhanced_prompt": enhanced_prompt})
        logger.info(f"Улучшенный промпт {enhanced_prompt}")

        enhanced_prompt2 = prompt_enhancer.enhance_prompt(question, summarized_context)

        logger.debug("Улучшенный промпт2", extra={"task_id": task_id, "enhanced_prompt": enhanced_prompt2})
        logger.info(f"Улучшенный промпт2 {enhanced_prompt2}")

        # 4. Генерируем изображение
        # logger.info("Запуск генерации изображения", extra={"task_id": task_id})
        # image_generator = ImageGenerator()
        # image_url = image_generator.generate(enhanced_prompt, output_path=f'generated_images/{task_id}.png')

        # logger.debug("Изображение создано", extra={"task_id": task_id, "image_url": image_url})

        logger.info("Тест без запуска на генерацию generated_images/1.png", extra={"task_id": task_id})
        image_url = 'generated_images/1.png'
        # 5. Формируем результат
        result = {
            "enhanced_prompt": enhanced_prompt,
            "image_url": image_url,
            "context": context
        }

        # 6. Отправляем результат в API
        logger.info(f"Отправка результата в API {task_id}:image_url {image_url}")
        update_task_result_in_api(task_id, {"status": "completed", "result": result})

        logger.info("Задача успешно завершена", extra={"task_id": task_id})
        return result

    except Exception as e:
        logger.error("Ошибка при выполнении задачи", exc_info=True,
                      extra={"task_id": task_data.get("task_id"), "error": str(e)})
        update_task_result_in_api(task_id, {"status": "failed", "error": str(e)})
        return {"status": "failed", "error": str(e)}