from typing import Dict, List
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

class TextClassifier:
    def __init__(self, llm_service):
        self.llm = llm_service
    
    def classify_text(self, text: str) -> Dict:
        """Классификация текста с использованием LLM"""
        try:
            prompt = f"""
            Проанализируй текст из брендбука и определи его тип. Возможные типы:
            - brand_values: Ценности бренда
            - logo_usage: Правила использования логотипа
            - color_palette: Цветовая палитра
            - typography: Типографика
            - tone_of_voice: Тон общения
            - other: Другое
            
            Текст: {text}
            
            Верни ответ в формате JSON: {{"type": "тип_текста", "confidence": уверенность_в_процентах}}
            """
            
            response = self.llm.generate(prompt)
            return response
        except Exception as e:
            logging.error(f"Ошибка классификации текста: {e}")
            return {"type": "other", "confidence": 0}
    
    def process_text_entries(self, text_entries: List[Dict]) -> List[Dict]:
        """Обработка списка текстовых записей"""
        classified = []
        for entry in text_entries:
            if entry["type"] == "text":
                classification = self.classify_text(entry["content"])
                classified.append({
                    **entry,
                    "classification": classification
                })
        return classified