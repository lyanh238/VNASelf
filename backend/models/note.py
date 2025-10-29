"""
Note model for Neon Database
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Note(Base):
    """Model for storing user notes in Neon Database."""

    __tablename__ = "note"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    thread_id = Column(String(255), nullable=True, index=True)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=True, index=True)
    request_context = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "thread_id": self.thread_id,
            "content": self.content,
            "category": self.category,
            "request_context": self.request_context,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_deleted": self.is_deleted,
        }

    @classmethod
    def get_current_timestamp(cls):
        return int(datetime.now().timestamp() * 1000)


