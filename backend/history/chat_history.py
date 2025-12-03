"""
Logs model for Neon Database
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, BigInteger
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Logs(Base):
    """Model for storing conversation logs in Neon Database."""
    
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    message_type = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    agent_name = Column(String(100), nullable=True)  # Which agent handled this message
    
    meta_info = Column("metadata", Text, nullable=True)  # JSON string for additional data
    
    # Timestamp fields
    timestamp = Column(BigInteger, nullable=False, index=True)  # Unix timestamp in milliseconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Logs(id={self.id}, thread_id={self.thread_id}, type={self.message_type}, timestamp={self.timestamp})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "user_id": self.user_id,
            "message_type": self.message_type,
            "content": self.content,
            "agent_name": self.agent_name,
            "metadata": self.meta_info,
            "timestamp": self.timestamp,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_deleted": self.is_deleted
        }
    
    @classmethod
    def get_current_timestamp(cls):
        """Get current timestamp in milliseconds."""
        return int(datetime.now().timestamp() * 1000)
