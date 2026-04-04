from sqlalchemy import Column, BigInteger, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from app.db.base import Base

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(BigInteger, primary_key=True, index=True)
    article_id = Column(BigInteger, ForeignKey("law_articles.id", ondelete="CASCADE"), nullable=False)
    question_type = Column(String, nullable=False) # mcq, ox, blank
    question_text = Column(Text, nullable=False)
    choices_json = Column(JSONB, nullable=True)
    answer_json = Column(JSONB, nullable=False)
    explanation_text = Column(Text, nullable=False)
    difficulty = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(BigInteger, ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False)
    user_answer = Column(JSONB, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    feedback = Column(Text, nullable=True)
    attempted_at = Column(DateTime, default=datetime.utcnow)
