from sqlalchemy import Column, BigInteger, String, DateTime
from datetime import datetime

from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    nickname = Column(String, nullable=False)
    role = Column(String, default="user") # user, admin
    created_at = Column(DateTime, default=datetime.utcnow)
