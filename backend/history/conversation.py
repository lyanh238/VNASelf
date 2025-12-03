"""
Conversation model for Neon Database
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, BigInteger
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Conversation(Base):
    """Model for storing conversation metadata in Neon Database."""
    
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    title = Column(String(500), nullable=False)  # Conversation title
    summary = Column(Text, nullable=True)  # LLM-generated summary
    
    # Metadata
    message_count = Column(Integer, default=0)  # Number of messages in conversation
    last_message_content = Column(Text, nullable=True)  # Last message content
    last_message_timestamp = Column(BigInteger, nullable=True)  # Last message timestamp
    
    # Timestamp fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, thread_id={self.thread_id}, title={self.title})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "user_id": self.user_id,
            "title": self.title,
            "summary": self.summary,
            "message_count": self.message_count,
            "last_message_content": self.last_message_content,
            "last_message_timestamp": self.last_message_timestamp,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_deleted": self.is_deleted
        }
    
    @classmethod
    def get_current_timestamp(cls):
        """Get current timestamp in milliseconds."""
        return int(datetime.now().timestamp() * 1000)
