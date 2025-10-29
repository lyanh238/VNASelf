"""
Note Agent for recording and managing user notes
"""

from typing import List, Any, Optional, Dict
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from .base_agent import BaseAgent
from datetime import datetime
import pytz

from services.note_service import NoteService
from services.note_storage_service import NoteStorageService


VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")


def _now_iso_vietnam() -> str:
    return datetime.now(VN_TZ).isoformat()


# Globals for tools to access services
_note_db_service: Optional[NoteService] = None
_note_storage_service: Optional[NoteStorageService] = None


def _classify_note_category(content: str) -> str:
    """Lightweight keyword-based classifier for note categories."""
    text = content.lower()
    categories = [
        ("Finance", ["expense", "invoice", "budget", "payment", "vnd", "usd", "cost"]),
        ("Meeting", ["meeting", "call", "zoom", "agenda", "minutes"]),
        ("Task", ["todo", "to-do", "task", "deadline", "due", "follow up", "follow-up"]),
        ("Reminder", ["remind", "remember", "alarm", "at ", "on ", "tomorrow", "next week"]),
        ("Idea", ["idea", "brainstorm", "concept", "inspiration"]),
        ("Shopping", ["buy", "purchase", "order", "shopping", "cart", "groceries"]),
        ("Health", ["exercise", "gym", "run", "med", "medicine", "doctor"]),
        ("Learning", ["learn", "course", "lecture", "study", "read", "book"]),
        ("Work", ["project", "sprint", "release", "deploy", "ticket", "jira", "pr"]),
        ("Personal", ["family", "friend", "birthday", "party", "vacation", "travel"]),
    ]
    for cat, keys in categories:
        if any(k in text for k in keys):
            return cat
    return "Other"


@tool
def record_note(
    content: str,
    category: Optional[str] = None,
    user_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    request_context: Optional[str] = None
) -> Dict[str, Any]:
    """Ghi lại một ghi chú của người dùng.

    Args:
        content: Nội dung ghi chú
        category: Danh mục ghi chú (tự phân loại nếu không cung cấp)
        user_id: ID người dùng (optional)
        thread_id: ID cuộc trò chuyện (optional)
        request_context: Ngữ cảnh yêu cầu ban đầu (optional)

    Returns:
        Dict chứa thông tin ghi chú đã lưu cùng metadata
    """
    try:
        if not content or not content.strip():
            return {"success": False, "error": "Content is required"}

        resolved_category = category or _classify_note_category(content)
        created_at = _now_iso_vietnam()

        note_payload = {
            "user_id": user_id,
            "thread_id": thread_id,
            "content": content.strip(),
            "category": resolved_category,
            "request_context": request_context,
            "created_at": created_at,
            "updated_at": created_at,
            "timestamp": int(datetime.now().timestamp() * 1000)
        }

        # Persist to JSON storage
        saved_json = False
        if _note_storage_service:
            import asyncio
            saved_json = asyncio.run(_note_storage_service.add_note(note_payload))

        # Persist to NeonDB
        db_result = None
        if _note_db_service:
            import asyncio
            db_result = asyncio.run(_note_db_service.create_note(
                content=note_payload["content"],
                category=note_payload["category"],
                user_id=user_id,
                thread_id=thread_id,
                request_context=request_context
            ))

        return {
            "success": True,
            "message": "Ghi chú đã được lưu",
            "note": {
                **note_payload,
                "id": db_result.id if db_result else None
            },
            "storage": {
                "json": bool(saved_json),
                "database": bool(db_result)
            }
        }

    except Exception as e:
        return {"success": False, "error": f"Lỗi khi lưu ghi chú: {str(e)}"}


@tool
def list_notes(
    user_id: Optional[str] = None,
    limit: int = 20,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """Liệt kê các ghi chú gần đây. Có thể lọc theo danh mục.

    Args:
        user_id: ID người dùng (optional)
        limit: số lượng tối đa
        category: danh mục để lọc (optional)
    """
    try:
        import asyncio
        notes_json: List[Dict[str, Any]] = []
        notes_db: List[Dict[str, Any]] = []

        if _note_storage_service:
            notes_json = asyncio.run(_note_storage_service.list_notes(user_id=user_id, limit=limit, category=category))

        if _note_db_service:
            db_notes = asyncio.run(_note_db_service.get_notes(user_id=user_id, limit=limit, category=category))
            notes_db = [n.to_dict() for n in db_notes]

        return {
            "success": True,
            "notes": notes_db or notes_json,
            "source": "database" if notes_db else "json",
            "count": len(notes_db or notes_json)
        }

    except Exception as e:
        return {"success": False, "error": f"Lỗi khi lấy danh sách ghi chú: {str(e)}"}


class NoteAgent(BaseAgent):
    """Agent chuyên ghi chép và quản lý ghi chú của người dùng."""
    
    def __init__(self, model: ChatOpenAI, note_db_service: NoteService, note_storage_service: NoteStorageService):
        super().__init__(model)
        self.name = "Note Agent"
        self._tools: Optional[List[Any]] = None
        global _note_db_service, _note_storage_service
        _note_db_service = note_db_service
        _note_storage_service = note_storage_service
    
    async def initialize(self):
        """Initialize tools for the note agent."""
        if self._tools is None:
            self._tools = [
                record_note,
                list_notes
            ]
    
    def get_system_prompt(self) -> str:
        return """Bạn là Note Agent. Nhiệm vụ của bạn là GHI LẠI và QUẢN LÝ ghi chú theo yêu cầu.

NHIỆM VỤ:
- Khi người dùng nói "ghi chú", "note", hoặc mô tả thông tin cần lưu, hãy dùng tool record_note
- Tự động phân loại ghi chú theo chủ đề nếu người dùng không cung cấp category
- Lưu ghi chú với metadata: timestamp, category, user_id, thread_id, request_context
- Có thể liệt kê ghi chú theo danh mục hoặc gần đây bằng tool list_notes

LƯU Ý:
- Luôn tôn trọng ngôn ngữ tiếng Việt tự nhiên của người dùng
- Không bịa thông tin; chỉ lưu đúng nội dung người dùng yêu cầu
- Category hợp lý: Work, Personal, Finance, Reminder, Idea, Meeting, Task, Shopping, Health, Learning, Other
"""
    
    def get_tools(self) -> List[Any]:
        if self._tools is None:
            raise RuntimeError("Note agent not initialized. Call initialize() first.")
        return self._tools


