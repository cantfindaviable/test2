from typing import List, Dict
from ml_worker.chromadb_manager import ChromaDBManager

class RAGSearcher:
    def __init__(self, chroma_manager: ChromaDBManager):
        self.chroma_manager = chroma_manager
    
    def search(self, query: str, filename: str, metadata_filter: dict = None, k: int = 4) -> List[Dict]:
        try:
            collection = self.chroma_manager.get_collection(filename)
            results = collection.query(query_texts=[query], n_results=k, where=metadata_filter)
            
            # Формируем результаты
            return [
                {
                    "text": doc,
                    "metadata": meta,
                    "similarity_score": score,
                    "images": meta.get("image_paths", [])
                }
                for doc, meta, score in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )
            ]
        except Exception as e:
            raise