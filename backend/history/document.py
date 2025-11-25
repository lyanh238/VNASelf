"""
Document embedding model for Neon Database.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    JSON,
    func,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class DocumentEmbedding(Base):
    """Model for storing document chunk embeddings in Neon Database."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False, index=True)
    file_path = Column(Text, nullable=True)
    file_type = Column(String(50), nullable=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "embedding": self.embedding,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


