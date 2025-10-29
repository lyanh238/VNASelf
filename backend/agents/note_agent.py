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
                self._create_add_note_tool(),
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
    
    def _create_add_note_tool(self):
        """Create the add note tool."""
        
        @tool
        async def add_note(
            title: str,
            content: str,
            user_id: str = "default_user",
            category: str = None,
            tags: str = None,
            priority: str = None,
            is_pinned: bool = False
        ) -> Dict[str, Any]:
            """
            Add a new note with automatic categorization.
            
            Args:
                title: Note title
                content: Note content
                user_id: User ID (default: default_user)
                category: Note category (optional, will be auto-detected if not provided)
                tags: Comma-separated tags (optional, will be auto-extracted if not provided)
                priority: Note priority - low, medium, high (optional, will be auto-determined if not provided)
                is_pinned: Whether to pin the note (default: False)
            
            Returns:
                Dict containing the created note information
            """
            try:
                # Auto-categorize if not provided
                if not category:
                    category = self._categorize_note(title, content)
                
                # Auto-extract tags if not provided
                if not tags:
                    extracted_tags = self._extract_tags(content)
                    tags = extracted_tags
                else:
                    tags = [tag.strip() for tag in tags.split(',')]
                
                # Auto-determine priority if not provided
                if not priority:
                    priority = self._determine_priority(title, content)
                
                # Add note to service
                note = await self.note_service.add_note(
                    user_id=user_id,
                    title=title,
                    content=content,
                    category=category,
                    tags=tags,
                    priority=priority,
                    is_pinned=is_pinned
                )
                
                return {
                    "success": True,
                    "message": f"Đã tạo ghi chú '{title}' thành công",
                    "note": note
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Lỗi khi tạo ghi chú: {str(e)}"
                }
        
        return add_note
    
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
                        "error": f"Không tìm thấy ghi chú với ID {note_id}"
                    }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Lỗi khi lấy ghi chú: {str(e)}"
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
                        "message": f"Đã cập nhật ghi chú '{updated_note['title']}' thành công",
                        "note": updated_note
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Không tìm thấy ghi chú với ID {note_id}"
                    }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Lỗi khi cập nhật ghi chú: {str(e)}"
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
                        "message": f"Đã xóa ghi chú với ID {note_id} thành công"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Không tìm thấy ghi chú với ID {note_id}"
                    }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Lỗi khi xóa ghi chú: {str(e)}"
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
                notes = await self.note_service.get_notes_by_user(user_id, limit, category)
                
                return {
                    "success": True,
                    "notes": notes,
                    "total": len(notes)
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Lỗi khi lấy danh sách ghi chú: {str(e)}"
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
                    "error": f"Lỗi khi tìm kiếm ghi chú: {str(e)}"
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
                    "error": f"Lỗi khi phân loại ghi chú: {str(e)}"
                }
        
        return categorize_note
    
    def get_system_prompt(self) -> str:
        return """Bạn là Note Agent chuyên về quản lý ghi chú thông minh.

QUY TẮC NGÔN NGỮ:
- Mặc định trả lời bằng tiếng Việt.
- Nếu người dùng sử dụng ngôn ngữ khác, trả lời bằng đúng ngôn ngữ đó.

NHIỆM VỤ CHÍNH:
- Tạo, đọc, cập nhật, xóa ghi chú
- Tự động phân loại ghi chú theo danh mục phù hợp
- Trích xuất tags từ nội dung ghi chú
- Xác định mức độ ưu tiên của ghi chú
- Tìm kiếm và lọc ghi chú theo nhiều tiêu chí

DANH MỤC TỰ ĐỘNG:
- work: Công việc, họp, dự án, nhiệm vụ
- personal: Cá nhân, gia đình, bạn bè
- study: Học tập, giáo dục, nghiên cứu
- finance: Tài chính, tiền bạc, đầu tư
- health: Sức khỏe, y tế, thuốc men
- travel: Du lịch, chuyến đi, nghỉ dưỡng
- shopping: Mua sắm, sản phẩm, cửa hàng
- ideas: Ý tưởng, suy nghĩ, sáng tạo
- reminders: Nhắc nhở, hạn chót, khẩn cấp
- general: Chung, tổng quát

MỨC ĐỘ ƯU TIÊN:
- high: Khẩn cấp, quan trọng, hạn chót
- medium: Bình thường (mặc định)
- low: Ý tưởng, có thể, sau này

QUY TRÌNH LÀM VIỆC:
1. Phân tích yêu cầu người dùng
2. Xác định loại thao tác (tạo/sửa/xóa/tìm)
3. Tự động phân loại và gán tags nếu cần
4. Thực hiện thao tác với cơ sở dữ liệu
5. Trả về kết quả rõ ràng và hữu ích

LƯU Ý QUAN TRỌNG:
- Luôn sử dụng tiếng Việt để giao tiếp
- Tự động phân loại ghi chú khi không được chỉ định
- Trích xuất tags từ nội dung một cách thông minh
- Cung cấp phản hồi rõ ràng về kết quả thao tác
- Hỗ trợ tìm kiếm linh hoạt theo từ khóa và danh mục"""
    
    def get_tools(self) -> List[Any]:
        """Get note management tools."""
        if self._note_tools is None:
            raise RuntimeError("Note agent not initialized. Call initialize() first.")
        return self._note_tools
