from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime

from core.database import Base


class Conversation(Base):

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)

    status = Column(String(30), default="ACTIVE")

    created_at = Column(DateTime, default=datetime.utcnow)