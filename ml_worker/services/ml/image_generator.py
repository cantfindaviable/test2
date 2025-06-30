from diffusers import StableDiffusionXLPipeline
from PIL import Image
import torch
import requests
import base64
from io import BytesIO
import os
import logging
from typing import Optional

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImageGenerator:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if self.device == "cuda" else torch.float32
        self.api_key = os.getenv("MODEL_LAB_API_KEY")
        self.use_local = torch.cuda.is_available()

        # Загружаем локальную модель только если есть GPU
        self.pipeline = self._load_pipeline() if self.use_local else None

    def _load_pipeline(self):
        try:
            logger.info("Загрузка локальной модели Stable Diffusion XL...")
            pipeline = StableDiffusionXLPipeline.from_pretrained(
                "stabilityai/stable-diffusion-xl-base-1.0",
                torch_dtype=self.torch_dtype,
                use_safetensors=True,
                variant="fp16"
            ).to(self.device)

            # Оптимизации для малой памяти
            pipeline.enable_attention_slicing()
            pipeline.enable_vae_slicing()
            pipeline.enable_xformers_memory_efficient_attention()

            logger.info("Локальная модель загружена")
            return pipeline
        except Exception as e:
            logger.warning(f"Не удалось загрузить локальную модель: {e}")
            self.use_local = False
            return None

    def generate(self, prompt: str, output_path: str) -> str:
        """
        Генерирует изображение через локальную модель или API
        Возвращает путь к сохранённому файлу
        """
        logger.info(f"Генерация изображения: {prompt[:50]}...")

        image = None
        if self.use_local and self.pipeline:
            image_path = self._generate_local(prompt, output_path)
            logger.info(f"Изображение создано локально: {image_path}")
            return image_path
        else:
            image_path = self._generate_api(prompt, output_path)
            logger.info(f"Изображение получено через API: {image_path}")
            return image_path

    def _generate_local(self, prompt: str, output_path: str) -> Optional[str]:
        """Генерация с использованием локальной модели"""
        try:
            image = self.pipeline(prompt=prompt).images[0]
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            image.save(output_path)
            return output_path
        except Exception as e:
            logger.error(f"Ошибка при локальной генерации: {e}")
            raise

    def _generate_api(self, prompt: str, output_path: str) -> Optional[str]:
        """Генерация через внешнее API"""
        url = "https://modelslab.com/api/v6/realtime/text2img" 

        payload = {
            "key": self.api_key,
            "prompt": prompt,
            "negative_prompt": "(worst quality:2), (low quality:2), (normal quality:2), (jpeg artifacts), (blurry), (duplicate), (morbid), (mutilated), (out of frame), (extra limbs), (bad anatomy), (disfigured), (deformed), (cross-eye), (glitch), (oversaturated), (overexposed), (underexposed), (bad proportions), (bad hands), (bad feet), watermark, text, logo, signature, grainy, tiling, censored, nsfw, ugly, blurry eyes, noisy image, bad lighting, unnatural skin, asymmetry",
            "samples": "1",
            "height": "1024",
            "width": "1024",
            "safety_checker": False,
            "base64": False,
            "webhook": None,
            "track_id": None
        }

        try:
            response = requests.post(url, json=payload, timeout=60)
            data = response.json()

            if data.get("status") == "success":
                image_url = data["output"][0]

                # Скачиваем и сохраняем изображение
                image_data = requests.get(image_url).content
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                with open(output_path, "wb") as f:
                    f.write(image_data)

                logger.info(f"Изображение успешно скачано: {output_path}")
                return output_path
            else:
                error_msg = data.get("error", "Неизвестная ошибка")
                logger.error(f"Ошибка от API: {error_msg}")
                raise RuntimeError(error_msg)

        except requests.RequestException as e:
            logger.error(f"Ошибка подключения к API: {e}")
            raise
        except Exception as e:
            logger.error(f"Ошибка генерации: {e}")
            raise
