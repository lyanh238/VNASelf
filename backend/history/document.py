"""
Document embedding and metadata_ models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class DocumentMetadata(Base):
    """High-level metadata_ for each uploaded document."""

    __tablename__ = "document_metadata"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)  # Original filename
    stored_file_name = Column(String(255), nullable=False, unique=True)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False)
    document_type = Column(String(100), nullable=False, default="general")
    description = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    uploaded_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    embeddings = relationship(
        "DocumentEmbedding",
        back_populates="metadata_",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "file_name": self.file_name,
            "stored_file_name": self.stored_file_name,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "document_type": self.document_type,
            "description": self.description,
            "extra_metadata": self.extra_metadata or {},
            "uploaded_by": self.uploaded_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DocumentEmbedding(Base):
    """Embeddings generated per chunk for semantic search."""

    __tablename__ = "document_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    metadata_id = Column(
        Integer,
        ForeignKey("document_metadata.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)  # Ensure text-based column for embeddings
    embedding = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    metadata_ = relationship(
        "DocumentMetadata",
        back_populates="embeddings",
        lazy="joined",
    )

    def to_dict(self) -> Dict[str, Any]:
        metadata_ = self.metadata_.to_dict() if self.metadata_ else None
        return {
            "id": self.id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "embedding": self.embedding,
            "document_type": metadata_["document_type"] if metadata_ else None,
            "metadata_": metadata_,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
