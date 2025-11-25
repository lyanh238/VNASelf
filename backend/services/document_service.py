"""
Document embedding service for Neon Database.
"""

from typing import List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from config import Config
from history.document import DocumentEmbedding, Base


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
    ) -> int:
        """Persist chunk embeddings for a processed document."""
        if not self.SessionLocal:
            return 0
        try:
            saved = 0
            with self.SessionLocal() as session:
                # Remove previous embeddings for this file to avoid duplication
                session.query(DocumentEmbedding).filter(
                    DocumentEmbedding.file_name == file_name
                ).delete()
                for idx, (content, embedding) in enumerate(zip(chunks, embeddings)):
                    doc = DocumentEmbedding(
                        file_name=file_name,
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


