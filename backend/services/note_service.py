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
        self.SessionLocal = None
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        try:
            if Config.NEON_DATABASE_URL:
                self.engine = create_engine(Config.NEON_DATABASE_URL)
                # Create table if not exists
                Base.metadata.create_all(self.engine)
                self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
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
        if not self.SessionLocal:
            return None
        try:
            note = Note(
                user_id=user_id,
                thread_id=thread_id,
                content=content,
                category=category,
                request_context=request_context,
            )
            with self.SessionLocal() as session:
                session.add(note)
                session.commit()
                session.refresh(note)
                return note
        except SQLAlchemyError as e:
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
        if not self.SessionLocal:
            return []
        try:
            with self.SessionLocal() as session:
                query = session.query(Note).filter(Note.is_deleted == False)
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

    async def get_note(self, note_id: int, user_id: Optional[str] = None) -> Optional[Note]:
        if not self.SessionLocal:
            return None
        try:
            with self.SessionLocal() as session:
                query = session.query(Note).filter(Note.id == note_id, Note.is_deleted == False)
                if user_id:
                    query = query.filter(Note.user_id == user_id)
                return query.first()
        except SQLAlchemyError as e:
            print(f"Error fetching note: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching note: {str(e)}")
            return None

    async def update_note(
        self,
        note_id: int,
        user_id: Optional[str] = None,
        title: Optional[str] = None,  # Not supported by current model
        content: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,  # Not supported by current model
        priority: Optional[str] = None,     # Not supported by current model
        is_archived: Optional[bool] = None, # Not supported by current model
        is_pinned: Optional[bool] = None    # Not supported by current model
    ) -> Optional[dict]:
        if not self.SessionLocal:
            return None
        try:
            with self.SessionLocal() as session:
                query = session.query(Note).filter(Note.id == note_id, Note.is_deleted == False)
                if user_id:
                    query = query.filter(Note.user_id == user_id)
                note = query.first()
                if not note:
                    return None

                if content is not None:
                    note.content = content
                if category is not None:
                    note.category = category

                session.commit()
                session.refresh(note)
                # Return a dict to align with NoteAgent expectations
                return {
                    "id": note.id,
                    "user_id": note.user_id,
                    "thread_id": note.thread_id,
                    "content": note.content,
                    "category": note.category,
                    "request_context": note.request_context,
                }
        except SQLAlchemyError as e:
            print(f"Error updating note: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error updating note: {str(e)}")
            return None

    async def delete_note(self, note_id: int, user_id: Optional[str] = None) -> bool:
        if not self.SessionLocal:
            return False
        try:
            with self.SessionLocal() as session:
                query = session.query(Note).filter(Note.id == note_id, Note.is_deleted == False)
                if user_id:
                    query = query.filter(Note.user_id == user_id)
                note = query.first()
                if not note:
                    return False
                note.is_deleted = True
                session.commit()
                return True
        except SQLAlchemyError as e:
            print(f"Error deleting note: {str(e)}")
            return False
        except Exception as e:
            print(f"Unexpected error deleting note: {str(e)}")
            return False

    async def get_notes_by_user(self, user_id: str, limit: int = 20, category: Optional[str] = None) -> List[Note]:
        # Compatibility wrapper for NoteAgent
        return await self.get_notes(user_id=user_id, limit=limit, category=category)

    async def search_notes(self, user_id: Optional[str], query: str, category: Optional[str] = None) -> List[dict]:
        if not self.SessionLocal:
            return []
        try:
            from sqlalchemy import or_
            with self.SessionLocal() as session:
                q = session.query(Note).filter(Note.is_deleted == False)
                if user_id:
                    q = q.filter(Note.user_id == user_id)
                if category:
                    q = q.filter(Note.category == category)
                # Simple search on content
                like = f"%{query}%"
                q = q.filter(or_(Note.content.ilike(like)))
                notes = q.order_by(Note.id.desc()).all()
                return [
                    {
                        "id": n.id,
                        "user_id": n.user_id,
                        "thread_id": n.thread_id,
                        "content": n.content,
                        "category": n.category,
                        "request_context": n.request_context,
                    }
                    for n in notes
                ]
        except SQLAlchemyError as e:
            print(f"Error searching notes: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error searching notes: {str(e)}")
            return []

    async def close(self):
        try:
            if self.engine:
                self.engine.dispose()
            print("[OK] Note Service closed")
        except Exception as e:
            print(f"Error closing NoteService: {str(e)}")


