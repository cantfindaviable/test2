import logging
from typing import Dict, List

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

class ImageCaptioner:
    def __init__(self, llm_service):
        self.llm = llm_service
    
    def generate_caption(self, image_path: str, colors: List[str] = None) -> Dict:
        """Генерация описания изображения с использованием LLM"""
        try:
            prompt = f"""
            Сгенерируй подробное описание изображения из брендбука. 
            Учитывай что это часть фирменного стиля компании.
            """
            
            if colors:
                prompt += f"\nОсновные цвета изображения: {', '.join(colors)}"
            
            response = self.llm.generate(prompt)
            return {
                "image_path": image_path,
                "caption": response,
                "colors": colors
            }
        except Exception as e:
            logging.error(f"Ошибка генерации описания изображения {image_path}: {e}")
            return {
                "image_path": image_path,
                "caption": "Не удалось сгенерировать описание",
                "colors": colors
            }
    
    def process_images(self, image_entries: List[Dict]) -> List[Dict]:
        """Обработка списка изображений"""
        captions = []
        for entry in image_entries:
            if entry["type"] in ["page_colors_image", "page_colors_scrin"]:
                caption = self.generate_caption(
                    entry["image_path"],
                    entry["content"]
                )
                captions.append(caption)
        return captions