import requests
from typing import Optional
from loguru import logger

class PromptEnhancer:
    def __init__(self, ollama_host="ollama", ollama_port=11434, model_name="gemma3:1b"):
        self.ollama_url = f"http://{ollama_host}:{ollama_port}/api/generate"
        self.model_name = model_name

    def enhance_prompt(self, designer_prompt: str, context: str) -> str:
        system_prompt = f"""
You are a strict assistant that creates designer specifications based on brand guidelines.
Generate output in English in the exact format below, no additional text:
- HEADER:
- COLORS:
- STYLE:
- RESTRICTIONS:

Context:
---
{context}
---
Initial task: "{designer_prompt}"
"""

        payload = {
            "model": self.model_name,
            "prompt": system_prompt,
            "stream": False
        }

        try:
            response = requests.post(self.ollama_url, json=payload)
            data = response.json()
            logger.info(f"Результат LLM: {data['response']}")
            return data['response']
        except Exception as e:
            logger.error(f"Не удалось вызвать Ollama: {e}")
            raise