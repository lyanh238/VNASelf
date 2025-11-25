"""
Conversation Service for Neon Database with improved connection handling
"""

import asyncio
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, text, and_, or_, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, date
import json

from config import Config
from history.conversation import Conversation, Base

class ConversationService:
    """Service for managing conversation metadata in Neon Database."""
    
    def __init__(self):
        self.engine = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connection."""
        if self._initialized:
            return
        
        try:
            if Config.NEON_DATABASE_URL:
                # Configure engine with proper SSL settings and connection pooling
                self.engine = create_engine(
                    Config.NEON_DATABASE_URL,
                    pool_size=5,
                    max_overflow=10,
                    pool_pre_ping=True,  # This will test connections before use
                    pool_recycle=3600,   # Recycle connections every hour
                    connect_args={
                        "sslmode": "require",
                        "connect_timeout": 10,
                        "application_name": "x2d35_conversation_service"
                    }
                )
                # Check if conversations table exists, if not create it
                try:
                    Base.metadata.create_all(self.engine)
                    print("[OK] Conversation Service connected to Neon Database")
                except Exception as e:
                    print(f"WARNING: Table creation warning: {str(e)}")
                    print("[OK] Conversation Service connected to existing conversations table")
            else:
                print("WARNING: NEON_DATABASE_URL not set - conversations will not be saved")
            
            self._initialized = True
            
        except Exception as e:
            print(f"[ERROR] Error initializing conversation service: {str(e)}")
            # Don't raise error, just disable conversations
            self._initialized = True
    
    def _get_session(self) -> Optional[Session]:
        """Get database session with proper error handling."""
        if not self.engine:
            return None
        
        try:
            # Create a new session for each operation to avoid stale connections
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            return SessionLocal()
        except Exception as e:
            print(f"Error creating database session: {str(e)}")
            return None
    
    async def create_conversation(
        self,
        thread_id: str,
        user_id: str,
        title: str,
        summary: Optional[str] = None
    ) -> Optional[Conversation]:
        """Create a new conversation."""
        session = self._get_session()
        if not session:
            return None
        
        try:
            conversation = Conversation(
                thread_id=thread_id,
                user_id=user_id,
                title=title,
                summary=summary,
                message_count=0
            )
            
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
            
            return conversation
            
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error creating conversation: {str(e)}")
            return None
        except Exception as e:
            session.rollback()
            print(f"Unexpected error creating conversation: {str(e)}")
            return None
        finally:
            session.close()
    
    async def get_conversation_by_thread_id(self, thread_id: str) -> Optional[Conversation]:
        """Get conversation by thread ID."""
        session = self._get_session()
        if not session:
            return None
        
        try:
            conversation = session.query(Conversation)\
                .filter(Conversation.thread_id == thread_id)\
                .filter(Conversation.is_deleted == False)\
                .first()
            
            return conversation
            
        except SQLAlchemyError as e:
            print(f"Error getting conversation: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error getting conversation: {str(e)}")
            return None
        finally:
            session.close()
    
    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Conversation]:
        """Get all conversations for a user."""
        session = self._get_session()
        if not session:
            return []
        
        try:
            conversations = session.query(Conversation)\
                .filter(Conversation.user_id == user_id)\
                .filter(Conversation.is_deleted == False)\
                .order_by(Conversation.last_message_timestamp.desc().nullslast(), Conversation.created_at.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
            
            return conversations
            
        except SQLAlchemyError as e:
            print(f"Error getting user conversations: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error getting user conversations: {str(e)}")
            return []
        finally:
            session.close()
    
    async def update_conversation_title(
        self,
        thread_id: str,
        new_title: str
    ) -> bool:
        """Update conversation title."""
        session = self._get_session()
        if not session:
            return False
        
        try:
            result = session.query(Conversation)\
                .filter(Conversation.thread_id == thread_id)\
                .filter(Conversation.is_deleted == False)\
                .update({"title": new_title, "updated_at": datetime.now()})
            
            session.commit()
            return result > 0
            
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error updating conversation title: {str(e)}")
            return False
        except Exception as e:
            session.rollback()
            print(f"Unexpected error updating conversation title: {str(e)}")
            return False
        finally:
            session.close()
    
    async def update_conversation_summary(
        self,
        thread_id: str,
        summary: str
    ) -> bool:
        """Update conversation summary."""
        session = self._get_session()
        if not session:
            return False
        
        try:
            result = session.query(Conversation)\
                .filter(Conversation.thread_id == thread_id)\
                .filter(Conversation.is_deleted == False)\
                .update({"summary": summary, "updated_at": datetime.now()})
            
            session.commit()
            return result > 0
            
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error updating conversation summary: {str(e)}")
            return False
        except Exception as e:
            session.rollback()
            print(f"Unexpected error updating conversation summary: {str(e)}")
            return False
        finally:
            session.close()
    
    async def update_conversation_last_message(
        self,
        thread_id: str,
        last_message_content: str,
        last_message_timestamp: int,
        message_count: Optional[int] = None
    ) -> bool:
        """Update conversation last message info."""
        session = self._get_session()
        if not session:
            return False
        
        try:
            update_data = {
                "last_message_content": last_message_content,
                "last_message_timestamp": last_message_timestamp,
                "updated_at": datetime.now()
            }
            
            # If message_count is not provided, try to get it from per-conversation storage
            if message_count is None:
                try:
                    from services.per_conversation_storage_service import PerConversationStorageService
                    storage_service = PerConversationStorageService()
                    await storage_service.initialize()
                    stats = await storage_service.get_conversation_stats(thread_id)
                    message_count = stats.get("message_count", 0)
                except Exception as e:
                    print(f"Error getting message count from per-conversation storage: {str(e)}")
                    message_count = 0
            
            update_data["message_count"] = message_count
            
            result = session.query(Conversation)\
                .filter(Conversation.thread_id == thread_id)\
                .filter(Conversation.is_deleted == False)\
                .update(update_data)
            
            session.commit()
            return result > 0
            
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error updating conversation last message: {str(e)}")
            return False
        except Exception as e:
            session.rollback()
            print(f"Unexpected error updating conversation last message: {str(e)}")
            return False
        finally:
            session.close()
    
    async def delete_conversation(self, thread_id: str) -> bool:
        """Soft delete a conversation."""
        session = self._get_session()
        if not session:
            return False
        
        try:
            result = session.query(Conversation)\
                .filter(Conversation.thread_id == thread_id)\
                .filter(Conversation.is_deleted == False)\
                .update({"is_deleted": True, "updated_at": datetime.now()})
            
            session.commit()
            return result > 0
            
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error deleting conversation: {str(e)}")
            return False
        except Exception as e:
            session.rollback()
            print(f"Unexpected error deleting conversation: {str(e)}")
            return False
        finally:
            session.close()
    
    async def increment_message_count(self, thread_id: str) -> bool:
        """Increment message count for a conversation."""
        session = self._get_session()
        if not session:
            return False
        
        try:
            result = session.query(Conversation)\
                .filter(Conversation.thread_id == thread_id)\
                .filter(Conversation.is_deleted == False)\
                .update({"message_count": Conversation.message_count + 1})
            
            session.commit()
            return result > 0
            
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error incrementing message count: {str(e)}")
            return False
        except Exception as e:
            session.rollback()
            print(f"Unexpected error incrementing message count: {str(e)}")
            return False
        finally:
            session.close()
    
    async def close(self):
        """Close database connection."""
        try:
            if self.engine:
                self.engine.dispose()
            print("[OK] Conversation Service closed")
        except Exception as e:
            print(f"Error closing conversation service: {str(e)}")