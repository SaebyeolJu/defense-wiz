import sys
import os
import asyncio

# Add backend to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from app.db.session import AsyncSessionLocal
from app.db.models.laws import LawVersion, Law
from app.services.chunk_service import chunk_service
from sqlalchemy import select
from sqlalchemy.orm import joinedload

async def main():
    async with AsyncSessionLocal() as db:
        try:
            # 비동기 실행
            result = await db.execute(
                select(LawVersion)
                .options(joinedload(LawVersion.law))
                .order_by(LawVersion.id.desc())
                .limit(1)
            )
            law_version = result.scalar_one_or_none()

            if not law_version:
                print("No LawVersions found in DB. Please sync laws first.")
                return

            print(f"Starting indexing for Law Version ID: {law_version.id} ({law_version.law.law_name})")
            
            # 비동기 서비스 호출
            await chunk_service.process_and_index_articles(db, law_version.id)
            
            print("Indexing completed!")
            
        except Exception as e:
            print(f"Error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
