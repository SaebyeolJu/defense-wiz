from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from app.db.base import Base

class QaLog(Base):
    __tablename__ = "qa_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    intent_type = Column(String, nullable=False) # qa, compare, summary, quiz
    question = Column(Text, nullable=False)
    retrieved_chunk_ids = Column(JSONB, nullable=True)
    final_answer = Column(Text, nullable=True)
    confidence_score = Column(String, nullable=True) # high, medium, low
    created_at = Column(DateTime, default=datetime.utcnow)
