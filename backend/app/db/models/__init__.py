from app.db.base import Base
from app.db.models.laws import Law, LawVersion
from app.db.models.articles import LawArticle, LawChunk, LawVersionDiff
from app.db.models.users import User
from app.db.models.qa_logs import QaLog
from app.db.models.quiz import QuizQuestion, QuizAttempt

# Alembic 타겟 메타데이터 등록을 위한 패키지 노출
__all__ = [
    "Base",
    "Law",
    "LawVersion",
    "LawArticle",
    "LawChunk",
    "LawVersionDiff",
    "User",
    "QaLog",
    "QuizQuestion",
    "QuizAttempt"
]
