"""
Note Service for Neon Database
"""

from typing import List, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from config import Config
from models.note import Note, Base


class NoteService:
    """Service for managing notes in Neon Database."""

    def __init__(self):
        self.engine = None
        self.session: Optional[Session] = None
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        try:
            if Config.NEON_DATABASE_URL:
                self.engine = create_engine(Config.NEON_DATABASE_URL)
                # Create table if not exists
                Base.metadata.create_all(self.engine)
                SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
                self.session = SessionLocal()
                print("[OK] Note Service connected to Neon Database")
            else:
                print("WARNING: NEON_DATABASE_URL not set - notes will not be saved to DB")
            self._initialized = True
        except Exception as e:
            print(f"[ERROR] Error initializing NoteService: {str(e)}")
            self._initialized = True

    async def create_note(
        self,
        content: str,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        request_context: Optional[str] = None,
    ) -> Optional[Note]:
        if not self.session:
            return None
        try:
            note = Note(
                user_id=user_id,
                thread_id=thread_id,
                content=content,
                category=category,
                request_context=request_context,
            )
            self.session.add(note)
            self.session.commit()
            self.session.refresh(note)
            return note
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error creating note: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error creating note: {str(e)}")
            return None

    async def get_notes(
        self,
        user_id: Optional[str] = None,
        limit: int = 20,
        category: Optional[str] = None,
    ) -> List[Note]:
        if not self.session:
            return []
        try:
            query = self.session.query(Note).filter(Note.is_deleted == False)
            if user_id:
                query = query.filter(Note.user_id == user_id)
            if category:
                query = query.filter(Note.category == category)
            return query.order_by(Note.id.desc()).limit(limit).all()
        except SQLAlchemyError as e:
            print(f"Error fetching notes: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching notes: {str(e)}")
            return []

    async def close(self):
        try:
            if self.session:
                self.session.close()
            if self.engine:
                self.engine.dispose()
            print("[OK] Note Service closed")
        except Exception as e:
            print(f"Error closing NoteService: {str(e)}")


