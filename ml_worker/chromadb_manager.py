from chromadb import HttpClient
from langchain_community.embeddings import HuggingFaceEmbeddings
from chromadb.api.types import EmbeddingFunction, Documents
import numpy as np
from typing import List, Optional
from chromadb.config import Settings
import logging
logger = logging.getLogger(__name__)

class LangChainEmbeddingWrapper(EmbeddingFunction):
    def __init__(self, embedder):
        self.embedder = embedder

    def __call__(self, input: Documents) -> List[List[float]]:
        return self.embedder.embed_documents(input)

class ChromaDBManager:
    def __init__(self, host="chromadb", port=8000):
        """
        Подключение к удалённому ChromaDB через REST API
        """
        self.client = HttpClient(
            host=host,
            port=port,
            settings=Settings(
                chroma_api_impl="rest",
                # chroma_server_rest_api_version="v2"
            )
        )
        logger.info("Подключились к ChromaDB", extra={"host": host, "port": port})
        self.embedder = self._load_embeddings()
    
    def _load_embeddings(self):
        """Загрузка модели эмбеддингов"""
        return LangChainEmbeddingWrapper(
            HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        )

    def get_collection(self, filename: str):
        collection_name = f"brandbook__{filename.replace('.', '_')}"
        try:
            return self.client.get_collection(name=collection_name, embedding_function=self.embedder)
        except Exception as e:
            logger.error(f"Коллекция {collection_name} не найдена: {e}")
            raise