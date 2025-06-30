from typing import List, Dict
from chromadb_manager import ChromaDBManager

import logging
logger = logging.getLogger(__name__)

class RAGSearcher:
    def __init__(self, chroma_manager: ChromaDBManager):
        self.chroma_manager = chroma_manager

    def search(self, query: str, collection_name: str = "default") -> List[str]:
        """
        Выполняет поиск в указанной коллекции ChromaDB
        """
        try:
            collection = self.chroma_manager.client.get_collection(name=collection_name)
            results = collection.query(query_texts=[query], n_results=2)
            logger.debug(f"Найдены документы: {results['documents']}")
            return results['documents']
        except Exception as e:
            logger.error(f"Ошибка поиска в ChromaDB: {e}")
            return []
        
        

# class RAGSearcher:
#     def __init__(self, chroma_manager: ChromaDBManager):
#         self.chroma_manager = chroma_manager
    
#     def search(self, query: str, filename: str, metadata_filter: dict = None, k: int = 4) -> List[Dict]:
#         try:
#             collection = self.chroma_manager.get_collection(filename)
#             results = collection.query(query_texts=[query], n_results=k, where=metadata_filter)
            
#             # Формируем результаты
#             return [
#                 {
#                     "text": doc,
#                     "metadata": meta,
#                     "similarity_score": score,
#                     "images": meta.get("image_paths", [])
#                 }
#                 for doc, meta, score in zip(
#                     results["documents"][0],
#                     results["metadatas"][0],
#                     results["distances"][0]
#                 )
#             ]
#         except Exception as e:
#             raise

# rag_searcher.py