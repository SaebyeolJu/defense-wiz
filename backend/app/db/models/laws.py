from sqlalchemy import Column, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base

class Law(Base):
    __tablename__ = "laws"

    id = Column(BigInteger, primary_key=True, index=True)
    law_name = Column(String, nullable=False, index=True)
    law_type = Column(String, nullable=False)
    ministry = Column(String, nullable=False)
    source_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    versions = relationship("LawVersion", back_populates="law", cascade="all, delete-orphan")


class LawVersion(Base):
    __tablename__ = "law_versions"

    id = Column(BigInteger, primary_key=True, index=True)
    law_id = Column(BigInteger, ForeignKey("laws.id", ondelete="CASCADE"), nullable=False)
    version_label = Column(String, nullable=False)
    promulgation_date = Column(Date, nullable=False)
    effective_date = Column(Date, nullable=False)
    amended_type = Column(String, nullable=False)
    is_current = Column(Boolean, default=False)
    previous_version_id = Column(BigInteger, nullable=True) # nullable for first version
    raw_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    law = relationship("Law", back_populates="versions")
    articles = relationship("LawArticle", back_populates="version", cascade="all, delete-orphan")
