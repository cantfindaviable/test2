import os
import logging
from typing import List, Dict
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

from .color_extractor import extract_colors

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

def process_brandbook(pdf_path: str, output_folder: str = "brandbook_images") -> List[Dict]:
    """
    Обработка PDF-брендбука:
    1. Извлечение текста
    2. Извлечение изображений и OCR
    3. Если текст и изображения отсутствуют — делает скриншот страницы
    """
    file_name = os.path.basename(pdf_path)
    base_name = os.path.splitext(file_name)[0]
    logging.info(f"Обработка файла: {pdf_path}")
    logging.info(f"Формирование выходной директории: {output_folder}")
    output_folder = os.path.join(output_folder, base_name)
    os.makedirs(output_folder, exist_ok=True)

    data = []
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    logging.info(f"Загружено {total_pages} страниц")

    for page_num in range(total_pages):
        logging.info(f"--- Обработка страницы {page_num + 1}/{total_pages} ---")
        page = doc.load_page(page_num)
        page_text = page.get_text().strip()
        image_list = page.get_images(full=True)

        # 1. Обработка текста
        if page_text:
            logging.info(f"[Страница {page_num + 1}] Найден текст (длина: {len(page_text)})")
            data.append({
                "type": "text",
                "content": page_text,
                "page": page_num + 1
            })
        else:
            logging.info(f"[Страница {page_num + 1}] Текст не найден")

        # 2. Обработка встроенных изображений
        if image_list:
            logging.info(f"[Страница {page_num + 1}] Найдено {len(image_list)} изображений")
        else:
            logging.info(f"[Страница {page_num + 1}] Изображения не найдены")

        cnt = 0
        for img in image_list:
            xref = img[0]
            width, height = img[2], img[3]
            if width < 40 or height < 40:
                logging.debug(f"[Страница {page_num + 1}] Пропущено маленькое изображение (xref={xref})")
                continue

            logging.info(f"[Страница {page_num + 1}] Извлечение изображения xref={xref}")
            image = doc.extract_image(xref)
            image_path = os.path.join(output_folder, f"page{page_num+1}_img{cnt}.png")
            cnt += 1

            # Сохраняем изображение перед обработкой
            with open(image_path, "wb") as f:
                f.write(image["image"])

            # Извлечение цветов
            hex_colors = extract_colors(image_path, num_colors=6)
            if hex_colors:
                logging.info(f"[Изображение {image_path}] Найдены цвета: {hex_colors}")
                data.append({
                    "type": "page_colors_image",
                    "content": hex_colors,
                    "page": page_num + 1,
                    "image_path": image_path
                })
            else:
                logging.warning(f"[Страница {page_num + 1}] Цвета не найдены или все фоновые")

            # OCR для изображения
            try:
                ocr_text = pytesseract.image_to_string(Image.open(image_path), lang='rus+eng').strip()
                if ocr_text:
                    logging.info(f"[Страница {page_num + 1}] OCR: найден текст длиной {len(ocr_text)}")
                    data.append({
                        "type": "ocr_text",
                        "content": ocr_text,
                        "page": page_num + 1,
                        "image_path": image_path
                    })
                else:
                    logging.debug(f"[Страница {page_num + 1}] OCR: текст не распознан")
            except Exception as e:
                logging.error(f"[Страница {page_num + 1}] OCR error: {e}")

        # 3. Если нет текста и изображений — делаем скриншот
        if not page_text and not image_list:
            logging.warning(f"[Страница {page_num + 1}] Нет текста и изображений. Сохраняю скриншот.")
            pix = page.get_pixmap(dpi=300)
            image_path = os.path.join(output_folder, f"page{page_num+1}_full.png")
            pix.save(image_path)

            # OCR для скриншота
            try:
                ocr_text_scrin = pytesseract.image_to_string(Image.open(image_path), lang='rus+eng').strip()
                if ocr_text_scrin:
                    logging.info(f"[Страница {page_num + 1}] OCR (скрин): найден текст длиной {len(ocr_text_scrin)}")
                    data.append({
                        "type": "ocr_text_scrin",
                        "content": ocr_text_scrin,
                        "page": page_num + 1,
                        "image_path": image_path
                    })
                else:
                    logging.debug(f"[Страница {page_num + 1}] OCR (скрин): текст не распознан")
            except Exception as e:
                logging.error(f"[Страница {page_num + 1}] OCR (скрин) error: {e}")

            # Извлечение HEX-цветов со скрина
            logging.info(f"[Страница {page_num + 1}] Извлечение цветов с изображения")
            hex_colors = extract_colors(image_path, num_colors=6)
            if hex_colors:
                logging.info(f"[Страница {page_num + 1}] Найдены цвета: {hex_colors}")
                data.append({
                    "type": "page_colors_scrin",
                    "content": hex_colors,
                    "page": page_num + 1,
                    "image_path": image_path
                })
            else:
                logging.warning(f"[Страница {page_num + 1}] Цвета не найдены или все фоновые")

    logging.info("===Обработка завершена===")
    return data