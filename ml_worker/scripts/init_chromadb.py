import os
import json
from typing import List, Dict
from chromadb import HttpClient
from langchain_community.embeddings import HuggingFaceEmbeddings
from chromadb.api.types import Documents, EmbeddingFunction
from chromadb.config import Settings
import logging
from collections import defaultdict
import time 

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class LangChainEmbeddingWrapper(EmbeddingFunction):
    def __init__(self, embedder):
        self.embedder = embedder

    def __call__(self, input: Documents) -> List[List[float]]:
        return self.embedder.embed_documents(input)

def load_json_data(filepath: str) -> List[Dict]:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_collection(client, collection_name: str, items: List[Dict]):
    try:
        # Удаляем, если уже существует
        client.delete_collection(name=collection_name)
    except Exception:
        pass

    # Создаем новую коллекцию
    collection = client.create_collection(name=collection_name)
    logger.info(f"Коллекция {collection_name} создана")

    # Используем сплиттер
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " ", ""]
    )

    for idx, item in enumerate(items):
        full_text = item.get("full_text", "")
        if not full_text:
            continue

        chunks = text_splitter.split_text(full_text)

        for i, chunk in enumerate(chunks):
            # Формируем текст + метаданные
            text_for_embedding = chunk
            metadata = {"source": item.get("filename"), "chunk_id": i}

            if item.get('colors'):
                text_for_embedding += "\nЦвета: " + ", ".join(item['colors'])
                metadata["colors"] = ", ".join(item['colors'])

            if item.get('main_colors'):
                text_for_embedding += "\nОсновные цвета: " + ", ".join(item['main_colors'])
                metadata["main_colors"] = ", ".join(item['main_colors'])

            if item.get('styles'):
                text_for_embedding += "\nСтили: " + item['styles']
                metadata["styles"] = item['styles']

            if item.get('fonts'):
                text_for_embedding += "\nШрифты: " + item['fonts']
                metadata["fonts"] = item['fonts']

            if item.get('restrictions'):
                text_for_embedding += "\nОграничения: " + item['restrictions']
                metadata["restrictions"] = item['restrictions']

            # Добавляем чанк в базу
            collection.add(
                documents=[text_for_embedding],
                metadatas=[metadata],
                ids=[f"{item['filename']}_chunk_{i}"]
            )
    logger.info(f"Коллекция '{collection_name}' заполнена данными")
    return collection

def wait_for_chromadb(host="chromadb", port=8000, timeout=60, retry_interval=5):
    """Ждём, пока ChromaDB станет доступной"""
    start = time.time()
    client = HttpClient(host=host, port=port, settings=Settings(chroma_api_impl="rest"))

    while time.time() - start < timeout:
        try:
            collections = client.list_collections()
            logger.info("ChromaDB доступна, список коллекций:", collections)
            return
        except Exception as e:
            logger.warning(f"ChromaDB недоступна: {e}, жду {retry_interval} секунд...")
            time.sleep(retry_interval)

    raise TimeoutError(f"Не удалось подключиться к ChromaDB за {timeout} секунд")

def main():
    DATA_PATH = "data/results_features.json"
    
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    chroma_client = HttpClient(
        host="chromadb",
        port=8000,
        settings=Settings(chroma_api_impl="rest")
    )

    logger.info("Загрузка данных из JSON...")
    data = load_json_data(DATA_PATH)

    grouped_data = defaultdict(list)
    for item in data:
        filename = item.get("filename", "unknown")
        grouped_data[filename].append(item)

    # Список ожидаемых коллекций
    expected_collections = {f"brandbook__{str(i).replace('.', '_')}_pdf" for i in [2, 3, 4]}
    existing_collections = set(col.name for col in chroma_client.list_collections())

    missing_collections = expected_collections - existing_collections

    if not missing_collections:
        logger.info("Все нужные коллекции уже созданы. Пропускаем инициализацию.")
        return

    logger.info(f"Нужно создать {len(missing_collections)} коллекций: {missing_collections}")

    for filename, items in grouped_data.items(): #brandbook__2_pdf
        collection_name = f"brandbook__{filename.replace('.', '_')}_pdf"

        if collection_name not in expected_collections:
            logger.warning(f"Коллекция '{collection_name}' не в списке ожидаемых. Пропускаем.")
            continue

        if collection_name in existing_collections:
            logger.info(f"Коллекция '{collection_name}' уже существует. Пропускаем создание.")
            continue

        logger.info(f"Создание новой коллекции '{collection_name}'")
        create_collection(chroma_client, collection_name, items)

    logger.info("Все отсутствующие коллекции успешно созданы")

if __name__ == "__main__":
    logger.info("Ожидаем доступности ChromaDB...")
    wait_for_chromadb()

    logger.info("Начало инициализации коллекций")
    main()