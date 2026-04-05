from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = "jhgan/ko-sroberta-multitask"):
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
    
    def generate_embedding(self, text: str) -> list[float]:
        return self.model.encode(text).tolist()
    
    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts)
        return [emb.tolist() for emb in embeddings]

embedding_service = EmbeddingService()
