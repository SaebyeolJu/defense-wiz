from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base

class LawArticle(Base):
    __tablename__ = "law_articles"

    id = Column(BigInteger, primary_key=True, index=True)
    law_version_id = Column(BigInteger, ForeignKey("law_versions.id", ondelete="CASCADE"), nullable=False)
    article_key = Column(String, nullable=False, index=True)
    article_no = Column(String, nullable=False)
    paragraph_no = Column(String, nullable=True)
    item_no = Column(String, nullable=True)
    subitem_no = Column(String, nullable=True)
    title = Column(String, nullable=True)
    full_text = Column(Text, nullable=False)
    normalized_text = Column(Text, nullable=False)
    display_order = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    version = relationship("LawVersion", back_populates="articles")
    chunks = relationship("LawChunk", back_populates="article", cascade="all, delete-orphan")

class LawChunk(Base):
    __tablename__ = "law_chunks"

    id = Column(BigInteger, primary_key=True, index=True)
    article_id = Column(BigInteger, ForeignKey("law_articles.id", ondelete="CASCADE"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_order = Column(Integer, nullable=False, default=1)
    qdrant_point_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    article = relationship("LawArticle", back_populates="chunks")

class LawVersionDiff(Base):
    __tablename__ = "law_version_diffs"

    id = Column(BigInteger, primary_key=True, index=True)
    law_id = Column(BigInteger, ForeignKey("laws.id", ondelete="CASCADE"), nullable=False)
    old_version_id = Column(BigInteger, ForeignKey("law_versions.id", ondelete="CASCADE"), nullable=False)
    new_version_id = Column(BigInteger, ForeignKey("law_versions.id", ondelete="CASCADE"), nullable=False)
    article_key = Column(String, nullable=False, index=True)
    change_type = Column(String, nullable=False) # added, deleted, modified, unchanged
    old_article_id = Column(BigInteger, nullable=True)
    new_article_id = Column(BigInteger, nullable=True)
    old_text = Column(Text, nullable=True)
    new_text = Column(Text, nullable=True)
    diff_summary = Column(Text, nullable=True)
    changed_fields = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
