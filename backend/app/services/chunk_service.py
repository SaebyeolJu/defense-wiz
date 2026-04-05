import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.db.models.articles import LawArticle, LawChunk
from app.db.models.laws import LawVersion, Law
from app.services.embedding_service import embedding_service
from app.services.qdrant_service import qdrant_service

logger = logging.getLogger(__name__)

class ChunkService:
    async def process_and_index_articles(self, db: AsyncSession, law_version_id: int):
        """
        Parses LawArticles from Postgres, generates embeddings, saves to LawChunk, and pushes to Qdrant.
        1 조문 = 1 청크 기본 원칙
        """
        logger.info(f"Starting chunk and indexing process for version_id: {law_version_id}")
        
        # 1. Fetch articles with relations (Async)
        result = await db.execute(
            select(LawArticle)
            .options(joinedload(LawArticle.version).joinedload(LawVersion.law))
            .where(LawArticle.law_version_id == law_version_id)
        )
        articles = result.scalars().all()

        if not articles:
            logger.warning(f"No articles found for law_version_id: {law_version_id}")
            return

        batch_size = 50
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i+batch_size]
            texts = [a.normalized_text for a in batch]
            
            # 2. Generate embeddings
            vectors = embedding_service.generate_embeddings_batch(texts)
            
            # 3. Create LawChunk records & Qdrant Payloads
            qdrant_points = []
            
            for article, vector in zip(batch, vectors):
                point_id = str(uuid.uuid4())
                
                existing_res = await db.execute(
                    select(LawChunk).where(LawChunk.article_id == article.id)
                )
                existing_chunk = existing_res.scalar_one_or_none()
                
                if existing_chunk:
                    chunk = existing_chunk
                    chunk.chunk_text = article.normalized_text
                    # 이미 발급된 qdrant_point_id가 있다면 그대로 재사용하여 Qdrant에서 Overwrite 되게 함
                    if chunk.qdrant_point_id:
                        point_id = chunk.qdrant_point_id
                    else:
                        point_id = str(uuid.uuid4())
                        chunk.qdrant_point_id = point_id
                else:
                    point_id = str(uuid.uuid4())
                    chunk = LawChunk(
                        article_id=article.id,
                        chunk_text=article.normalized_text,
                        chunk_order=1,
                        qdrant_point_id=point_id
                    )
                    db.add(chunk)
                
                payload = {
                    "article_id": article.id,
                    "version_id": article.law_version_id,
                    "law_name": article.version.law.law_name if article.version and article.version.law else "Unknown",
                    "article_no": article.article_no,
                    "article_title": article.title or "",
                    "chunk_text": article.normalized_text,
                }
                
                qdrant_points.append({
                    "id": point_id,
                    "vector": vector,
                    "payload": payload
                })
                
            # 4. Save to Qdrant
            qdrant_service.upsert_chunks(qdrant_points)
            
            logger.info(f"Indexed batch of {len(batch)} chunks for version_id {law_version_id}")
        
        # 5. Commit to PostgreSQL
        await db.commit()
        logger.info(f"Successfully processed {len(articles)} articles!")

chunk_service = ChunkService()
