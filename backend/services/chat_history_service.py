"""
Simple logs service for Neon Database
"""

import asyncio
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import json
from datetime import datetime

from config import Config
from history.chat_history import Logs, Base

class LogsService:
    """Simple service for managing conversation logs in Neon Database."""
    
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
                        "application_name": "x2d35_logs_service"
                    }
                )
                # Check if logs table exists, if not create it
                try:
                    Base.metadata.create_all(self.engine)
                    print("[OK] Logs Service connected to Neon Database")
                except Exception as e:
                    print(f"WARNING: Table creation warning: {str(e)}")
                    print("[OK] Logs Service connected to existing logs table")
            else:
                print("WARNING: NEON_DATABASE_URL not set - logs will not be saved")
            
            self._initialized = True
            
        except Exception as e:
            print(f"[ERROR] Error initializing logs service: {str(e)}")
            # Don't raise error, just disable logs
            self._initialized = True
    
    def get_session(self) -> Optional[Session]:
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
    
    async def save_message(
        self, 
        thread_id: str, 
        message_type: str, 
        content: str, 
        agent_name: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[int] = None
    ) -> Optional[Logs]:
        """Save a conversation log to database."""
        session = self.get_session()
        if not session:
            return None
        
        try:
            # Use provided timestamp or current timestamp
            if timestamp is None:
                timestamp = Logs.get_current_timestamp()
            
            log_entry = Logs(
                thread_id=thread_id,
                user_id=user_id,
                message_type=message_type,
                content=content,
                agent_name=agent_name,
                meta_info=json.dumps(metadata) if metadata else None,
                timestamp=timestamp
            )
            
            session.add(log_entry)
            session.commit()
            session.refresh(log_entry)
            
            return log_entry
            
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error saving log entry: {str(e)}")
            return None
        except Exception as e:
            session.rollback()
            print(f"Unexpected error saving log entry: {str(e)}")
            return None
        finally:
            session.close()
    
    async def get_chat_history(
        self, 
        thread_id: str, 
        limit: int = 10,
        offset: int = 0
    ) -> List[Logs]:
        """Get conversation logs for a thread."""
        if not self.session:
            return []
        
        try:
            messages = self.session.query(Logs)\
                .filter(Logs.thread_id == thread_id)\
                .filter(Logs.is_deleted == False)\
                .order_by(Logs.timestamp.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
            
            return list(reversed(messages))  # Return in chronological order
            
        except SQLAlchemyError as e:
            print(f"Error getting conversation logs: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error getting conversation logs: {str(e)}")
            return []
    
    async def get_user_chat_history(
        self, 
        user_id: str, 
        limit: int = 20,
        offset: int = 0
    ) -> List[Logs]:
        """Get conversation logs for a specific user."""
        if not self.session:
            return []
        
        try:
            messages = self.session.query(Logs)\
                .filter(Logs.user_id == user_id)\
                .filter(Logs.is_deleted == False)\
                .order_by(Logs.timestamp.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
            
            return list(reversed(messages))  # Return in chronological order
            
        except SQLAlchemyError as e:
            print(f"Error getting user conversation logs: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error getting user conversation logs: {str(e)}")
            return []
    
    async def delete_thread(self, thread_id: str) -> bool:
        """Soft delete all logs in a thread."""
        if not self.session:
            return False
        
        try:
            self.session.query(Logs)\
                .filter(Logs.thread_id == thread_id)\
                .update({"is_deleted": True})
            self.session.commit()
            return True
            
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error deleting thread logs: {str(e)}")
            return False
        except Exception as e:
            print(f"Unexpected error deleting thread logs: {str(e)}")
            return False
    
    async def get_threads_for_user(self, user_id: str) -> List[str]:
        """Get all thread IDs for a user."""
        if not self.session:
            return []
        
        try:
            threads = self.session.query(Logs.thread_id)\
                .filter(Logs.user_id == user_id)\
                .filter(Logs.is_deleted == False)\
                .distinct()\
                .all()
            
            return [thread[0] for thread in threads]
            
        except SQLAlchemyError as e:
            print(f"Error getting user threads: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error getting user threads: {str(e)}")
            return []
    
    async def close(self):
        """Close database connection."""
        try:
            if self.engine:
                self.engine.dispose()
            print("[OK] Logs Service closed")
        except Exception as e:
            print(f"Error closing logs service: {str(e)}")
