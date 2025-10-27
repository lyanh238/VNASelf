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

BẠN CÓ THỂ SỬ DỤNG CÁC CÔNG CỤ SAU:

1. XEM LỊCH:
   - list_upcoming_events: Xem lịch sắp tới (max_results: số lượng sự kiện)
   - get_events_for_date: Xem lịch ngày cụ thể (date: YYYY-MM-DD)
   - search_events: Tìm kiếm sự kiện theo từ khóa (query: từ khóa)
   - get_event_by_id: Xem chi tiết sự kiện cụ thể (event_id: ID sự kiện)

2. KIỂM TRA LỊCH:
   - check_availability: Kiểm tra lịch trống/bận (date, start_time, end_time)
   - check_conflicts: Kiểm tra xung đột trong khoảng thời gian (start_datetime, end_datetime)

3. TẠO SỰ KIỆN:
   - create_event: Tạo sự kiện mới (summary, start_datetime, end_datetime, description, location, attendees)
   - create_event_with_conflict_check: Tạo sự kiện với kiểm tra xung đột (summary, start_datetime, end_datetime, description, location, attendees, force_create)

4. QUẢN LÝ SỰ KIỆN:
   - update_event: Cập nhật sự kiện (event_id, summary, start_datetime, end_datetime, description, location)
   - delete_event: Xóa sự kiện (event_id)
   - move_event: Di chuyển sự kiện (event_id, new_start_datetime, new_end_datetime)

5. GIẢI QUYẾT XUNG ĐỘT:
   - suggest_alternative_times: Đề xuất thời gian thay thế (start_datetime, end_datetime, duration_minutes, days_ahead)
   - resolve_conflict_by_moving_existing: Dời sự kiện cũ (existing_event_id, new_start_datetime, new_end_datetime)
   - resolve_conflict_by_deleting_existing: Xóa sự kiện cũ (existing_event_id)

6. ĐỀ XUẤT THỜI GIAN TỐI ƯU:
   - suggest_optimal_time: Đề xuất thời gian tối ưu (activity_type, duration_minutes, preferred_date, days_ahead)

7. CÔNG CỤ HỖ TRỢ:
   - vn_parse_date: Diễn giải thời gian tiếng Việt (phrase: "ngày mai", "thứ 6 tuần này", etc.)

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

HƯỚNG DẪN SỬ DỤNG CÔNG CỤ:
- Khi người dùng hỏi về lịch: sử dụng list_upcoming_events, get_events_for_date, hoặc search_events
- Khi người dùng muốn tạo sự kiện: LUÔN dùng create_event_with_conflict_check
- Khi có xung đột: sử dụng suggest_alternative_times, resolve_conflict_by_moving_existing, hoặc resolve_conflict_by_deleting_existing
- Khi người dùng yêu cầu đề xuất thời gian phù hợp: sử dụng suggest_optimal_time
- Khi cần diễn giải thời gian tiếng Việt: sử dụng vn_parse_date
- Khi cần kiểm tra lịch trống: sử dụng check_availability

XỬ LÝ THỜI GIAN TIẾNG VIỆT:
- LUÔN sử dụng vn_parse_date trước khi tạo sự kiện với thời gian tiếng Việt
- Ví dụ: "21h-6h sáng mai" → vn_parse_date("21h-6h sáng mai") → "2025-10-27T21:00:00+07:00..2025-10-28T06:00:00+07:00"
- Ví dụ: "thứ 6 tuần này" → vn_parse_date("thứ 6 tuần này") → "2025-10-24"
- Ví dụ: "ngày mai" → vn_parse_date("ngày mai") → "2025-10-28"

QUY TRÌNH TẠO SỰ KIỆN VỚI THỜI GIAN TIẾNG VIỆT:
1. Sử dụng vn_parse_date để chuyển đổi thời gian tiếng Việt sang ISO format
2. Sử dụng check_conflicts để kiểm tra xung đột
3. Nếu không có xung đột: sử dụng create_event_with_conflict_check
4. Nếu có xung đột: đề xuất giải pháp và hỏi người dùng

QUY TRÌNH ĐỀ XUẤT THỜI GIAN TỐI ƯU:
1. Khi người dùng yêu cầu đề xuất thời gian phù hợp cho hoạt động, sử dụng suggest_optimal_time
2. Các loại hoạt động được hỗ trợ:
   - meeting/họp: 10:00-11:30 AM hoặc 1:30-3:00 PM (thời gian họp tối ưu)
   - focus work/coding: 9:00-11:00 AM (thời gian tập trung cao)
   - creative work: 10:00-12:00 PM (thời gian sáng tạo)
   - admin/routine: 9:00-10:00 AM hoặc 4:00-5:00 PM (công việc hành chính)
3. Sau khi đề xuất thời gian, hỏi người dùng có muốn tạo sự kiện không
4. Nếu đồng ý, sử dụng create_event_with_conflict_check để tạo sự kiện

HÃY SỬ DỤNG NHIỀU CÔNG CỤ KHI CẦN THIẾT ĐỂ CUNG CẤP THÔNG TIN ĐẦY ĐỦ CHO NGƯỜI DÙNG!"""
    
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
        - phrase: ví dụ 'Thứ 6 tuần này', 'ngày mai', 'ngày này tuần sau', 'tuần này', 'tuần sau', 'cuối tuần', '21h-6h sáng mai'
        - anchor_iso (optional): ISO datetime làm mốc. Nếu không có, dùng current time VN.

        Output:
        - Nếu là 1 ngày: trả 'YYYY-MM-DD'
        - Nếu là khoảng tuần/cuối tuần: trả 'YYYY-MM-DD..YYYY-MM-DD' (start..end)
        - Nếu là khoảng thời gian trong ngày: trả 'YYYY-MM-DDTHH:MM:SS..YYYY-MM-DDTHH:MM:SS'
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

        # Handle time ranges like "21h-6h sáng mai"
        import re
        
        # Pattern for time ranges: "Xh-Yh sáng mai" or "Xh-Yh mai"
        time_range_pattern = r'(\d{1,2})h-(\d{1,2})h\s*(sáng\s+)?mai'
        match = re.search(time_range_pattern, p)
        if match:
            start_hour = int(match.group(1))
            end_hour = int(match.group(2))
            is_next_day = match.group(3) is not None  # "sáng mai" means next day
            
            if is_next_day:
                # "21h-6h sáng mai" means 21h today to 6h tomorrow
                start_date = anchor_date
                end_date = anchor_date + timedelta(days=1)
            else:
                # "21h-6h mai" means 21h tomorrow to 6h day after tomorrow
                start_date = anchor_date + timedelta(days=1)
                end_date = anchor_date + timedelta(days=2)
            
            start_datetime = vn_tz.localize(datetime.combine(start_date, datetime.min.time().replace(hour=start_hour)))
            end_datetime = vn_tz.localize(datetime.combine(end_date, datetime.min.time().replace(hour=end_hour)))
            
            return f"{start_datetime.isoformat()}..{end_datetime.isoformat()}"

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
