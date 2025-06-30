import requests
from typing import Optional
from loguru import logger
from llm import do_task

import logging
from typing import Optional


logger = logging.getLogger(__name__)

class PromptEnhancer:
    def __init__(self, ollama_host="ollama", ollama_port=11434, model_name="gemma3:1b"):
        self.model_name = model_name

    def enhance_prompt(self, designer_prompt: str, context: str) -> str:
        """
        Улучшает промпт с помощью LLM, используя предоставленный контекст.
        
        Args:
            designer_prompt: Исходное описание задачи дизайнера
            context: Контекст из RAG (найденные документы)
            
        Returns:
            str: Результат генерации — улучшенный промпт
        """
        system_prompt = f"""
You are a strict assistant that creates designer specifications based on brand guidelines.
Generate output in English in the exact format below, no additional text:
- HEADER: Ititial task in english
- COLORS:
- STYLE:
- RESTRICTIONS:

Context:
---
{context}
---
Initial task: "{designer_prompt}"
"""

        logger.info("Улучшение промпта через LLM")
        result = do_task(system_prompt)

        if not result or "ошибка" in result.lower():
            logger.error("Не удалось улучшить промпт")
            raise ValueError(f"Ошибка при улучшении промпта: {result}")

        logger.debug(f"Улучшенный промпт: {result}")
        return result
    