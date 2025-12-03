"""
Document embedding service for Neon Database.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from config import Config
from history.document import DocumentEmbedding, DocumentMetadata, Base


class DocumentService:
    """Service that stores and retrieves document embeddings from Neon Database."""

    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        try:
            if Config.NEON_DATABASE_URL:
                self.engine = create_engine(Config.NEON_DATABASE_URL)
                Base.metadata.create_all(self.engine)
                self.SessionLocal = sessionmaker(
                    autocommit=False, autoflush=False, bind=self.engine
                )
                print("[OK] Document Service connected to Neon Database")
            else:
                print("WARNING: NEON_DATABASE_URL not set - document embeddings disabled")
            self._initialized = True
        except Exception as exc:
            print(f"[ERROR] Error initializing DocumentService: {exc}")
            self._initialized = True

    async def save_document_chunks(
        self,
        file_name: str,
        file_path: str,
        file_type: str,
        chunks: List[str],
        embeddings: List[List[float]],
        *,
        original_file_name: Optional[str] = None,
        document_type: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
        uploaded_by: Optional[str] = None,
    ) -> int:
        """Persist chunk embeddings for a processed document."""
        if not self.SessionLocal:
            return 0
        try:
            saved = 0
            with self.SessionLocal() as session:
                stored_file_name = Path(file_path).name
                canonical_name = original_file_name or file_name
                doc_type = (document_type or "general").lower()

                # Remove previous embeddings + metadata for the stored file
                session.query(DocumentEmbedding).filter(
                    DocumentEmbedding.file_path == file_path
                ).delete(synchronize_session=False)
                session.query(DocumentMetadata).filter(
                    DocumentMetadata.stored_file_name == stored_file_name
                ).delete(synchronize_session=False)

                metadata_entry = DocumentMetadata(
                    file_name=canonical_name,
                    stored_file_name=stored_file_name,
                    file_path=file_path,
                    file_type=file_type,
                    document_type=doc_type,
                    extra_metadata=extra_metadata,
                    uploaded_by=uploaded_by,
                )
                session.add(metadata_entry)
                session.flush()

                for idx, (content, embedding) in enumerate(zip(chunks, embeddings)):
                    doc = DocumentEmbedding(
                        metadata_id=metadata_entry.id,
                        file_name=canonical_name,
                        file_path=file_path,
                        file_type=file_type,
                        chunk_index=idx,
                        content=content,
                        embedding=embedding,
                    )
                    session.add(doc)
                    saved += 1
                session.commit()
            return saved
        except SQLAlchemyError as exc:
            print(f"[ERROR] Error saving document embeddings: {exc}")
            return 0
        except Exception as exc:
            print(f"[ERROR] Unexpected error saving document embeddings: {exc}")
            return 0

    async def get_document_chunks(self, limit: int = 1000) -> List[dict]:
        """Return stored document chunks with embeddings."""
        if not self.SessionLocal:
            return []
        try:
            with self.SessionLocal() as session:
                query = (
                    session.query(DocumentEmbedding)
                    .order_by(DocumentEmbedding.created_at.desc())
                    .limit(limit)
                )
                return [doc.to_dict() for doc in query.all()]
        except SQLAlchemyError as exc:
            print(f"[ERROR] Error fetching document embeddings: {exc}")
            return []
        except Exception as exc:
            print(f"[ERROR] Unexpected error fetching document embeddings: {exc}")
            return []

    async def close(self):
        try:
            if self.engine:
                self.engine.dispose()
                print("[OK] Document Service closed")
        except Exception as exc:
            print(f"[ERROR] Error closing DocumentService: {exc}")


