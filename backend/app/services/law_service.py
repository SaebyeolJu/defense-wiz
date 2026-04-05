from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
from typing import Optional

from app.db.models.laws import Law, LawVersion
from app.db.models.articles import LawArticle
from app.services.ingestion_service import ingestion_service
from app.services.parser_service import parser_service

class LawService:
    async def sync_law_by_mst_id(self, db: AsyncSession, mst_id: str):
        """MST ID를 기반으로 법령 데이터를 수집하고 DB에 동기화(UPSERT)"""
        
        # 1. API 수집
        raw_data = await ingestion_service.get_law_detail(mst_id)
        if not raw_data:
            raise Exception(f"Failed to fetch law detail for MST: {mst_id}")

        # 2. 파싱
        parsed = parser_service.parse_law_data(raw_data)
        law = parsed["law"]
        version = parsed["version"]
        articles = parsed["articles"]

        # 3. DB 저장 (UPSERT)
        # Law 저장
        await self._upsert_law(db, law)
        
        # LawVersion 저장 (버전 정보가 바뀌었을 수도 있음)
        await self._upsert_law_version(db, version)
        
        # LawArticle 저장 (기존 해당 버전의 조문들은 삭제 후 재등록 또는 UPSERT)
        # 간단하게 구현하기 위해 해당 버전의 기존 조문 삭제 후 bulk insert 진행
        await self._sync_articles(db, version.id, articles)

        await db.commit()
        return law

    async def _upsert_law(self, db: AsyncSession, law: Law):
        stmt = insert(Law).values(
            id=law.id,
            law_name=law.law_name,
            law_type=law.law_type,
            ministry=law.ministry,
            source_url=law.source_url,
            is_active=law.is_active
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "law_name": law.law_name,
                "law_type": law.law_type,
                "ministry": law.ministry,
                "source_url": law.source_url
            }
        )
        await db.execute(stmt)

    async def _upsert_law_version(self, db: AsyncSession, version: LawVersion):
        stmt = insert(LawVersion).values(
            id=version.id,
            law_id=version.law_id,
            version_label=version.version_label,
            promulgation_date=version.promulgation_date,
            effective_date=version.effective_date,
            amended_type=version.amended_type,
            is_current=version.is_current
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "version_label": version.version_label,
                "promulgation_date": version.promulgation_date,
                "effective_date": version.effective_date,
                "amended_type": version.amended_type,
                "is_current": version.is_current
            }
        )
        await db.execute(stmt)

    async def _sync_articles(self, db: AsyncSession, version_id: int, articles: list[LawArticle]):
        # 해당 버전의 기존 조문 삭제
        from sqlalchemy import delete
        await db.execute(delete(LawArticle).where(LawArticle.law_version_id == version_id))
        
        # 새 조문들 bulk insert
        for article in articles:
            article.law_version_id = version_id
            db.add(article)

law_service = LawService()
