from diffusers import StableDiffusionXLPipeline, AutoPipelineForText2Image
from PIL import Image
import torch
import os
from loguru import logger
from typing import List, Optional

class ImageGenerator:
    def __init__(self):
        self.device = (
            "cuda" if torch.cuda.is_available() 
            else "mps" if getattr(torch.backends, "mps", False) and torch.backends.mps.is_available() 
            else "cpu"
        )
        self.torch_dtype = torch.float16 if self.device == "mps" else torch.float32
        self.pipeline = self._load_pipeline()

    def _load_pipeline(self):
        try:
            pipeline = AutoPipelineForText2Image.from_pretrained(
                "lykon/dreamshaper-xl-v2-turbo",
                torch_dtype=self.torch_dtype,
                variant="fp16"
            ).to(self.device)
            pipeline.vae.enable_slicing()
            pipeline.vae.enable_tiling()
            return pipeline
        except Exception as e:
            logger.error(f"Ошибка загрузки пайплайна: {e}")
            raise

    def generate(self, prompt: str, output_path: str) -> Optional[str]:
        try:
            image = self.pipeline(prompt).images[0]
            image.save(output_path)
            logger.info(f"Изображение создано: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Ошибка генерации изображения: {e}")
            return None