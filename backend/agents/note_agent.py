"""
Note Agent for managing user notes with automatic categorization
"""

from typing import List, Any, Dict, Optional
from langchain_openai import ChatOpenAI
from .base_agent import BaseAgent
from langchain_core.tools import tool
from services.note_service import NoteService
import re
import json

class NoteAgent(BaseAgent):
    """Specialized agent for note management with automatic categorization."""
        
    def __init__(self, model: ChatOpenAI, note_service: NoteService):
        super().__init__(model)
        self.name = "Note Agent"
        self.note_service = note_service
        self._note_tools = None
        
        # Predefined categories for automatic classification
        self.categories = {
            'work': ['công việc', 'work', 'job', 'meeting', 'họp', 'project', 'dự án', 'task', 'nhiệm vụ'],
            'personal': ['cá nhân', 'personal', 'riêng tư', 'private', 'family', 'gia đình', 'friend', 'bạn bè'],
            'study': ['học tập', 'study', 'education', 'giáo dục', 'course', 'khóa học', 'book', 'sách', 'research', 'nghiên cứu'],
            'finance': ['tài chính', 'finance', 'money', 'tiền', 'budget', 'ngân sách', 'expense', 'chi tiêu', 'investment', 'đầu tư'],
            'health': ['sức khỏe', 'health', 'medical', 'y tế', 'doctor', 'bác sĩ', 'medicine', 'thuốc', 'exercise', 'tập thể dục'],
            'travel': ['du lịch', 'travel', 'trip', 'chuyến đi', 'vacation', 'nghỉ', 'hotel', 'khách sạn', 'flight', 'chuyến bay'],
            'shopping': ['mua sắm', 'shopping', 'buy', 'mua', 'purchase', 'mua hàng', 'store', 'cửa hàng', 'product', 'sản phẩm'],
            'ideas': ['ý tưởng', 'ideas', 'thoughts', 'suy nghĩ', 'inspiration', 'cảm hứng', 'creative', 'sáng tạo', 'brainstorm', 'động não'],
            'reminders': ['nhắc nhở', 'reminder', 'alarm', 'báo thức', 'deadline', 'hạn chót', 'urgent', 'khẩn cấp', 'important', 'quan trọng'],
            'general': ['chung', 'general', 'misc', 'khác', 'other', 'tổng quát']
        }
    
    async def initialize(self):
        """Initialize the note agent with tools."""
        if self._note_tools is None:
            self._note_tools = [
                self._create_record_note_tool(),
                self._create_get_note_tool(),
                self._create_update_note_tool(),
                self._create_delete_note_tool(),
                self._create_list_notes_tool(),
                self._create_search_notes_tool(),
                self._create_categorize_note_tool()
            ]
    
    def _categorize_note(self, title: str, content: str) -> str:
        """Automatically categorize a note based on title and content."""
        text = f"{title} {content}".lower()
        
        # Check each category
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        
        return 'general'
    
    def _extract_tags(self, content: str) -> List[str]:
        """Extract potential tags from note content."""
        # Simple tag extraction - look for words starting with # or common patterns
        tags = []
        
        # Extract hashtags
        hashtags = re.findall(r'#(\w+)', content)
        tags.extend(hashtags)
        
        # Extract potential keywords (words that appear multiple times)
        words = re.findall(r'\b\w+\b', content.lower())
        word_count = {}
        for word in words:
            if len(word) > 3:  # Only consider words longer than 3 characters
                word_count[word] = word_count.get(word, 0) + 1
        
        # Add frequently mentioned words as tags
        for word, count in word_count.items():
            if count > 1 and word not in ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'man', 'oil', 'sit', 'try', 'use', 'why']:
                tags.append(word)
        
        return list(set(tags))[:5]  # Limit to 5 tags
    
    def _determine_priority(self, title: str, content: str) -> str:
        """Determine note priority based on content."""
        text = f"{title} {content}".lower()
        
        high_priority_keywords = ['urgent', 'khẩn cấp', 'important', 'quan trọng', 'asap', 'immediately', 'ngay lập tức', 'deadline', 'hạn chót']
        low_priority_keywords = ['someday', 'maybe', 'có thể', 'later', 'sau', 'optional', 'tùy chọn', 'idea', 'ý tưởng']
        
        for keyword in high_priority_keywords:
            if keyword in text:
                return 'high'
        
        for keyword in low_priority_keywords:
            if keyword in text:
                return 'low'
        
        return 'medium'
    
    def _create_record_note_tool(self):
        """Create the record note tool (alias for add_note)."""
        
        @tool
        async def record_note(
            content: str,
            user_id: str = "default_user",
            category: str = None,
            thread_id: str = None,
            request_context: str = None
        ) -> Dict[str, Any]:
            """
            Record a new note with automatic categorization.
            
            Args:
                content: Note content (required)
                user_id: User ID (default: default_user)
                category: Note category (optional, will be auto-detected if not provided)
                thread_id: Thread ID for context (optional)
                request_context: Context of the request (optional)
            
            Returns:
                Dict containing the created note information
            """
            try:
                # Auto-categorize if not provided
                if not category:
                    category = self._categorize_note("", content)
                
                # Save to Neon DB only (removed JSON storage)
                note = await self.note_service.create_note(
                    content=content,
                    category=category,
                    user_id=user_id,
                    thread_id=thread_id,
                    request_context=request_context
                )
                
                return {
                    "success": True,
                    "message": f"Note created successfully",
                    "note": note
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Error creating note: {str(e)}"
                }
        
        return record_note
    
    def _create_get_note_tool(self):
        """Create the get note tool."""
        
        @tool
        async def get_note(note_id: int, user_id: str = "default_user") -> Dict[str, Any]:
            """
            Get a specific note by ID.
            
            Args:
                note_id: Note ID
                user_id: User ID (default: default_user)
            
            Returns:
                Dict containing the note information
            """
            try:
                note = await self.note_service.get_note(note_id, user_id)
                
                if note:
                    return {
                        "success": True,
                        "note": note
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Note with ID {note_id} not found"
                    }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Error retrieving note: {str(e)}"
                }
        
        return get_note
    
    def _create_update_note_tool(self):
        """Create the update note tool."""
        
        @tool
        async def update_note(
            note_id: int,
            user_id: str = "default_user",
            title: str = None,
            content: str = None,
            category: str = None,
            tags: str = None,
            priority: str = None,
            is_archived: bool = None,
            is_pinned: bool = None
        ) -> Dict[str, Any]:
            """
            Update an existing note.
            
            Args:
                note_id: Note ID to update
                user_id: User ID (default: default_user)
                title: New title (optional)
                content: New content (optional)
                category: New category (optional)
                tags: Comma-separated tags (optional)
                priority: New priority - low, medium, high (optional)
                is_archived: Archive status (optional)
                is_pinned: Pin status (optional)
            
            Returns:
                Dict containing the updated note information
            """
            try:
                # Convert tags string to list if provided
                tags_list = None
                if tags:
                    tags_list = [tag.strip() for tag in tags.split(',')]
                
                # Update note
                updated_note = await self.note_service.update_note(
                    note_id=note_id,
                    user_id=user_id,
                    title=title,
                    content=content,
                    category=category,
                    tags=tags_list,
                    priority=priority,
                    is_archived=is_archived,
                    is_pinned=is_pinned
                )
                
                if updated_note:
                    return {
                        "success": True,
                        "message": f"Note '{updated_note['title']}' updated successfully",
                        "note": updated_note
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Note with ID {note_id} not found"
                    }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Error updating note: {str(e)}"
                }
        
        return update_note
    
    def _create_delete_note_tool(self):
        """Create the delete note tool."""
        
        @tool
        async def delete_note(note_id: int, user_id: str = "default_user") -> Dict[str, Any]:
            """
            Delete a note.
            
            Args:
                note_id: Note ID to delete
                user_id: User ID (default: default_user)
            
            Returns:
                Dict containing the deletion result
            """
            try:
                success = await self.note_service.delete_note(note_id, user_id)
                
                if success:
                    return {
                        "success": True,
                        "message": f"Note with ID {note_id} deleted successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Note with ID {note_id} not found"
                    }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Error deleting note: {str(e)}"
                }
        
        return delete_note
    
    def _create_list_notes_tool(self):
        """Create the list notes tool."""
        
        @tool
        async def list_notes(
            user_id: str = "default_user",
            limit: int = 10,
            category: str = None
        ) -> Dict[str, Any]:
            """
            List notes for a user with optional category filter.
            
            Args:
                user_id: User ID (default: default_user)
                limit: Maximum number of notes to return (default: 10)
                category: Category filter (optional)
            
            Returns:
                Dict containing the list of notes
            """
            try:
                # NoteService exposes get_notes(user_id, limit, category)
                notes = await self.note_service.get_notes(user_id, limit, category)
                
                return {
                    "success": True,
                    "notes": notes,
                    "total": len(notes)
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Error retrieving note list: {str(e)}"
                }
        
        return list_notes
    
    def _create_search_notes_tool(self):
        """Create the search notes tool."""
        
        @tool
        async def search_notes(
            query: str,
            user_id: str = "default_user",
            category: str = None
        ) -> Dict[str, Any]:
            """
            Search notes by query and optional category.
            
            Args:
                query: Search query
                user_id: User ID (default: default_user)
                category: Category filter (optional)
            
            Returns:
                Dict containing the search results
            """
            try:
                notes = await self.note_service.search_notes(user_id, query, category)
                
                return {
                    "success": True,
                    "notes": notes,
                    "total": len(notes),
                    "query": query
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Error searching notes: {str(e)}"
                }
        
        return search_notes
    
    def _create_categorize_note_tool(self):
        """Create the categorize note tool."""
        
        @tool
        async def categorize_note(
            title: str,
            content: str
        ) -> Dict[str, Any]:
            """
            Analyze and suggest category, tags, and priority for a note.
            
            Args:
                title: Note title
                content: Note content
            
            Returns:
                Dict containing categorization suggestions
            """
            try:
                category = self._categorize_note(title, content)
                tags = self._extract_tags(content)
                priority = self._determine_priority(title, content)
                
                return {
                    "success": True,
                    "suggestions": {
                        "category": category,
                        "tags": tags,
                        "priority": priority
                    }
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Error categorizing note: {str(e)}"
                }
        
        return categorize_note
    
    def get_system_prompt(self) -> str:
        return """You are a Note Agent specialized in intelligent note management.

LANGUAGE RULES:
- By default, respond in Vietnamese.
- If user uses a different language, respond in that same language.

MAIN TASKS:
- Create, read, update, delete notes
- Automatically categorize notes into appropriate categories
- Extract tags from note content
- Determine note priority level
- Search and filter notes by multiple criteria

AUTOMATIC CATEGORIES:
- work: Work, meetings, projects, tasks
- personal: Personal, family, friends
- study: Study, education, research
- finance: Finance, money, investment
- health: Health, medical, medicine
- travel: Travel, trips, vacation
- shopping: Shopping, products, stores
- ideas: Ideas, thoughts, creativity
- reminders: Reminders, deadlines, urgent
- general: General, miscellaneous

PRIORITY LEVELS:
- high: Urgent, important, deadlines
- medium: Normal (default)
- low: Ideas, maybe, later

WORKFLOW:
1. Analyze user request
2. Determine operation type (create/update/delete/search)
3. Automatically categorize and assign tags if needed
4. Execute operation with database
5. Return clear and useful results

IMPORTANT NOTES:
- Always use Vietnamese for communication
- Automatically categorize notes when not specified
- Intelligently extract tags from content
- Provide clear feedback on operation results
- Support flexible search by keywords and categories"""
    
    def get_tools(self) -> List[Any]:
        """Get note management tools."""
        if self._note_tools is None:
            raise RuntimeError("Note agent not initialized. Call initialize() first.")
        return self._note_tools
