"""
Per-Conversation Message Storage Service
Stores each conversation's messages in separate JSON files for better organization and performance
"""

import asyncio
import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
import aiofiles

class PerConversationStorageService:
    """Service for managing individual conversation message storage."""
    
    def __init__(self, storage_dir: str = "conversations"):
        self.storage_dir = storage_dir
        self._initialized = False
    
    async def initialize(self):
        """Initialize the storage service."""
        if self._initialized:
            return
        
        try:
            # Create storage directory if it doesn't exist
            if not os.path.exists(self.storage_dir):
                os.makedirs(self.storage_dir)
                print(f"[OK] Created conversation storage directory: {self.storage_dir}")
            
            self._initialized = True
            print("[OK] Per-Conversation Storage Service initialized")
            
        except Exception as e:
            print(f"[ERROR] Error initializing per-conversation storage: {str(e)}")
            self._initialized = True
    
    def _get_conversation_file_path(self, thread_id: str) -> str:
        """Get the file path for a conversation's messages."""
        # Sanitize thread_id for filename
        safe_thread_id = thread_id.replace('/', '_').replace('\\', '_')
        return os.path.join(self.storage_dir, f"{safe_thread_id}.json")
    
    async def save_message(
        self,
        thread_id: str,
        message_type: str,
        content: str,
        agent_name: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[int] = None
    ) -> bool:
        """Save a message to the conversation's file."""
        if not self._initialized:
            return False
        
        try:
            file_path = self._get_conversation_file_path(thread_id)
            
            # Load existing messages
            messages = await self._load_messages_from_file(file_path)
            
            # Create new message
            if timestamp is None:
                timestamp = int(datetime.now().timestamp() * 1000)
            
            new_message = {
                "id": len(messages) + 1,
                "thread_id": thread_id,
                "user_id": user_id,
                "message_type": message_type,
                "content": content,
                "agent_name": agent_name,
                "metadata": metadata,
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat()
            }
            
            # Add message to list
            messages.append(new_message)
            
            # Save back to file
            await self._save_messages_to_file(file_path, messages)
            
            return True
            
        except Exception as e:
            print(f"Error saving message to conversation file: {str(e)}")
            return False
    
    async def get_conversation_messages(
        self,
        thread_id: str,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get messages for a specific conversation."""
        if not self._initialized:
            return []
        
        try:
            file_path = self._get_conversation_file_path(thread_id)
            
            if not os.path.exists(file_path):
                return []
            
            messages = await self._load_messages_from_file(file_path)
            
            # Apply pagination if specified
            if limit is not None:
                messages = messages[offset:offset + limit]
            elif offset > 0:
                messages = messages[offset:]
            
            return messages
            
        except Exception as e:
            print(f"Error loading conversation messages: {str(e)}")
            return []
    
    async def get_all_conversation_messages(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a conversation (no pagination)."""
        return await self.get_conversation_messages(thread_id)
    
    async def delete_conversation_messages(self, thread_id: str) -> bool:
        """Delete all messages for a conversation."""
        if not self._initialized:
            return False
        
        try:
            file_path = self._get_conversation_file_path(thread_id)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting conversation messages: {str(e)}")
            return False
    
    async def get_conversation_stats(self, thread_id: str) -> Dict[str, Any]:
        """Get statistics about a conversation."""
        try:
            messages = await self.get_all_conversation_messages(thread_id)
            
            if not messages:
                return {
                    "message_count": 0,
                    "last_message_timestamp": None,
                    "last_message_content": None,
                    "user_message_count": 0,
                    "assistant_message_count": 0
                }
            
            user_messages = [msg for msg in messages if msg.get("message_type") == "user"]
            assistant_messages = [msg for msg in messages if msg.get("message_type") == "assistant"]
            
            last_message = messages[-1] if messages else None
            
            return {
                "message_count": len(messages),
                "last_message_timestamp": last_message.get("timestamp") if last_message else None,
                "last_message_content": last_message.get("content") if last_message else None,
                "user_message_count": len(user_messages),
                "assistant_message_count": len(assistant_messages)
            }
            
        except Exception as e:
            print(f"Error getting conversation stats: {str(e)}")
            return {
                "message_count": 0,
                "last_message_timestamp": None,
                "last_message_content": None,
                "user_message_count": 0,
                "assistant_message_count": 0
            }
    
    async def _load_messages_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Load messages from a JSON file."""
        try:
            if not os.path.exists(file_path):
                return []
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                if content.strip():
                    return json.loads(content)
                return []
                
        except Exception as e:
            print(f"Error loading messages from file {file_path}: {str(e)}")
            return []
    
    async def _save_messages_to_file(self, file_path: str, messages: List[Dict[str, Any]]) -> bool:
        """Save messages to a JSON file."""
        try:
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(messages, indent=2, ensure_ascii=False))
            return True
            
        except Exception as e:
            print(f"Error saving messages to file {file_path}: {str(e)}")
            return False
    
    async def list_conversation_files(self) -> List[str]:
        """List all conversation files."""
        try:
            if not os.path.exists(self.storage_dir):
                return []
            
            files = []
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    # Extract thread_id from filename
                    thread_id = filename[:-5].replace('_', '/')  # Reverse sanitization
                    files.append(thread_id)
            
            return files
            
        except Exception as e:
            print(f"Error listing conversation files: {str(e)}")
            return []
    
    async def close(self):
        """Close the storage service."""
        print("[OK] Per-Conversation Storage Service closed")

