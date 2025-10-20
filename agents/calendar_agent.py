"""
Calendar Agent for Google Calendar management
"""

from typing import List, Any, Optional, Tuple
from langchain_openai import ChatOpenAI
from .base_agent import BaseAgent
from services.mcp_service import MCPService
import pytz
from datetime import datetime, timedelta
from langchain_core.tools import tool

class CalendarAgent(BaseAgent):
    """Specialized agent for Google Calendar operations."""
    
    def __init__(self, model: ChatOpenAI, mcp_service: MCPService):
        super().__init__(model)
        self.name = "Calendar Agent"
        self.mcp_service = mcp_service
        self._calendar_tools = None
    
    async def initialize(self):
        """Initialize the calendar agent with MCP tools."""
        if self._calendar_tools is None:
            self._calendar_tools = await self.mcp_service.get_calendar_tools()
            # Append local utilities
            self._calendar_tools = self._calendar_tools + [self.vn_parse_date]
    
    def get_system_prompt(self) -> str:
        return """Bạn là trợ lý lịch thông minh chuyên về Google Calendar với khả năng phát hiện và giải quyết xung đột lịch.
        Bạn có thể:
        - Xem lịch sắp tới và ngày cụ thể
        - Tìm kiếm sự kiện
        - Tạo, cập nhật, xóa sự kiện
        - Di chuyển sự kiện
        - Kiểm tra lịch trống/bận
        - Phát hiện xung đột lịch và đề xuất giải pháp
        
        QUY TRÌNH TẠO SỰ KIỆN MỚI:
        1. LUÔN kiểm tra xung đột trước khi tạo sự kiện mới bằng check_conflicts()
        2. Nếu có xung đột:
           - Thông báo chi tiết về sự kiện xung đột
           - Đề xuất các giải pháp:
             a) Dời sự kiện mới sang thời gian khác (dùng suggest_alternative_times)
             b) Dời sự kiện cũ sang thời gian khác (dùng resolve_conflict_by_moving_existing)
             c) Xóa sự kiện cũ (dùng resolve_conflict_by_deleting_existing)
           - Hỏi người dùng muốn chọn giải pháp nào
        3. Nếu không có xung đột: tạo sự kiện bình thường
        
        Lưu ý quan trọng:
        - Thời gian phải theo định dạng ISO: 'YYYY-MM-DDTHH:MM:SS'
        - Ngày phải theo định dạng: 'YYYY-MM-DD'
        - Múi giờ: Asia/Ho_Chi_Minh (GMT+7)
        - Luôn dùng 'Current time (Asia/Ho_Chi_Minh)' cung cấp trong system message làm mốc (anchor date) để tính tất cả cụm thời gian tự nhiên.
        - Quy ước tuần bắt đầu Thứ 2 (ISO-8601), kết thúc Chủ nhật.
        - Quy tắc diễn giải tiếng Việt:
          * "ngày mai" = anchor + 1 ngày
          * "tuần này" = tuần chứa anchor (Thứ 2..Chủ nhật)
          * "tuần sau" = tuần ngay sau tuần chứa anchor
          * "Thứ X tuần này" = ngày Thứ X trong tuần chứa anchor (VD: anchor Thứ 2 2025-10-20 ⇒ "Thứ 6 tuần này" = 2025-10-24)
          * "Ngày này tuần sau" = cùng thứ, 7 ngày sau anchor (VD: 2025-10-20 ⇒ 2025-10-27)
        - Tránh lệch múi giờ: luôn tính theo Asia/Ho_Chi_Minh.
        - Ví dụ: nếu hôm nay (anchor) là 2025-10-20 thì:
          * 'ngày mai' = 2025-10-21
          * 'cuối tuần' = 2025-10-25 & 2025-10-26
          * 'thứ 6 tuần này' = 2025-10-24
          * 'ngày này tuần sau' = 2025-10-27
        
        CÔNG CỤ XUNG ĐỘT:
        - check_conflicts(): Kiểm tra xung đột trong khoảng thời gian
        - create_event_with_conflict_check(): Tạo sự kiện với kiểm tra xung đột
        - suggest_alternative_times(): Đề xuất thời gian thay thế
        - resolve_conflict_by_moving_existing(): Dời sự kiện cũ
        - resolve_conflict_by_deleting_existing(): Xóa sự kiện cũ
        """
    
    def get_tools(self) -> List[Any]:
        """Get calendar tools from MCP service."""
        if self._calendar_tools is None:
            raise RuntimeError("Calendar agent not initialized. Call initialize() first.")
        return self._calendar_tools

    # -------------------------------
    # Vietnamese natural date parser
    # -------------------------------
    @tool
    def vn_parse_date(phrase: str, anchor_iso: Optional[str] = None) -> str:
        """Diễn giải cụm thời gian tiếng Việt theo Asia/Ho_Chi_Minh.

        Input:
        - phrase: ví dụ 'Thứ 6 tuần này', 'ngày mai', 'ngày này tuần sau', 'tuần này', 'tuần sau', 'cuối tuần'
        - anchor_iso (optional): ISO datetime làm mốc. Nếu không có, dùng current time VN.

        Output:
        - Nếu là 1 ngày: trả 'YYYY-MM-DD'
        - Nếu là khoảng tuần/cuối tuần: trả 'YYYY-MM-DD..YYYY-MM-DD' (start..end)
        """
        vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")
        now_vn = datetime.now(vn_tz) if anchor_iso is None else datetime.fromisoformat(anchor_iso).astimezone(vn_tz)

        # Anchor date (strip time)
        anchor_date = now_vn.date()

        def week_bounds(d: datetime.date) -> Tuple[datetime.date, datetime.date]:
            # ISO week: Monday=0 .. Sunday=6
            weekday = d.weekday()
            start = d - timedelta(days=weekday)  # Monday
            end = start + timedelta(days=6)      # Sunday
            return start, end

        p = phrase.strip().lower()

        # Simple phrases
        if p == "ngày mai":
            return (anchor_date + timedelta(days=1)).isoformat()

        if p == "ngày này tuần sau":
            return (anchor_date + timedelta(days=7)).isoformat()

        if p in ["tuần này", "trong tuần này"]:
            start, end = week_bounds(anchor_date)
            return f"{start.isoformat()}..{end.isoformat()}"

        if p in ["tuần sau", "tuần tới"]:
            start, end = week_bounds(anchor_date + timedelta(days=7))
            return f"{start.isoformat()}..{end.isoformat()}"

        if p in ["cuối tuần", "weekend"]:
            start, end = week_bounds(anchor_date)
            sat = start + timedelta(days=5)
            sun = start + timedelta(days=6)
            return f"{sat.isoformat()}..{sun.isoformat()}"

        # Weekday mapping for Vietnamese
        weekday_map = {
            "thứ 2": 0,
            "thứ hai": 0,
            "thứ 3": 1,
            "thứ ba": 1,
            "thứ 4": 2,
            "thứ tư": 2,
            "thứ 5": 3,
            "thứ năm": 3,
            "thứ 6": 4,
            "thứ sáu": 4,
            "thứ 7": 5,
            "thứ bảy": 5,
            "chủ nhật": 6,
        }

        # Patterns: "thứ X tuần này" or "thứ X tuần sau"
        # Normalize spaces
        p_norm = " ".join(p.split())
        for key, target_idx in weekday_map.items():
            if f"{key} tuần này" == p_norm:
                start, _ = week_bounds(anchor_date)
                date_val = start + timedelta(days=target_idx)
                return date_val.isoformat()
            if f"{key} tuần sau" == p_norm:
                start, _ = week_bounds(anchor_date + timedelta(days=7))
                date_val = start + timedelta(days=target_idx)
                return date_val.isoformat()

        # Fallback: return anchor date to avoid hallucination
        return anchor_date.isoformat()
