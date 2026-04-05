import asyncio
import os
import sys
from sqlalchemy.future import select

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import AsyncSessionLocal
from app.db.models.laws import Law, LawVersion
from app.db.models.articles import LawArticle

async def inspect():
    async with AsyncSessionLocal() as db:
        # 1. Laws 확인
        print("\n=== [Table: laws] ===")
        laws = (await db.execute(select(Law))).scalars().all()
        for l in laws:
            print(f"ID: {l.id} | Name: {l.law_name} | Type: {l.law_type} | Ministry: {l.ministry}")

        # 2. LawVersions 확인
        print("\n=== [Table: law_versions] ===")
        versions = (await db.execute(select(LawVersion))).scalars().all()
        for v in versions:
            print(f"ID: {v.id} | Label: {v.version_label} | Date: {v.effective_date} | Current: {v.is_current}")

        # 3. LawArticles 확인 (샘플 10개)
        print("\n=== [Table: law_articles (Sample 10)] ===")
        articles = (await db.execute(select(LawArticle).order_by(LawArticle.display_order).limit(10))).scalars().all()
        print(f"{'Key':<25} | {'Art':<5} | {'Par':<5} | {'Item':<5} | {'Title':<15}")
        print("-" * 70)
        for a in articles:
            print(f"{a.article_key:<25} | {str(a.article_no):<5} | {str(a.paragraph_no):<5} | {str(a.item_no):<5} | {str(a.title):<15}")

if __name__ == "__main__":
    asyncio.run(inspect())
