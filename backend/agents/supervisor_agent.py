"""
Supervisor Agent for routing requests to appropriate specialized agents
"""

from typing import List, Any, Dict
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from .base_agent import BaseAgent
from .calendar_agent import CalendarAgent
from .finance_agent import FinanceAgent
from .search_agent import SearchAgent


class SupervisorAgent(BaseAgent):
    """Supervisor agent that routes requests to appropriate specialized agents."""
    
    def __init__(self, model: ChatOpenAI, calendar_agent: CalendarAgent, finance_agent: FinanceAgent, search_agent: SearchAgent):
        super().__init__(model)
        self.name = "Supervisor Agent"
        self.calendar_agent = calendar_agent
        self.finance_agent = finance_agent
        self.search_agent = search_agent
        self._all_tools = None
    
    async def initialize(self):
        """Initialize the supervisor with all available tools."""
        await self.calendar_agent.initialize()
        await self.finance_agent.initialize()
        await self.search_agent.initialize()
        self._all_tools = self.calendar_agent.get_tools() + self.finance_agent.get_tools() + self.search_agent.get_tools()
    
    def get_system_prompt(self) -> str:
        return """Bạn là supervisor thông minh chọn công cụ phù hợp để giải quyết yêu cầu người dùng.

 Phân loại công cụ:

# 1. Tài chính (Finance tools):
   - add_expense: Thêm chi tiêu mới (summary, amount, category, date)
   - get_expense_history: Xem lịch sử chi tiêu
   - get_expenses_by_category: Lọc chi tiêu theo danh mục (Food, Transportation, Miscellaneous)
   - get_expenses_by_date_range: Xem chi tiêu trong khoảng thời gian
   - get_total_spending: Tính tổng chi tiêu
   - delete_expense: Xóa chi tiêu
   - update_expense: Cập nhật thông tin chi tiêu

# 2. Tìm kiếm Web (Search tools):
   - tavily_search: Tìm kiếm thông tin trên web (query, max_results=3)
   - Sử dụng khi người dùng hỏi về thông tin cập nhật, tin tức, hoặc cần tìm kiếm trên internet

# 3. Lịch Google Calendar (các MCP tools):
   - list_upcoming_events: Xem lịch sắp tới
   - get_events_for_date: Xem lịch ngày cụ thể (cần format: YYYY-MM-DD)
   - search_events: Tìm kiếm sự kiện theo từ khóa
   - create_event: Tạo sự kiện mới (cần: tiêu đề, thời gian bắt đầu, thời gian kết thúc)
   - create_event_with_conflict_check: Tạo sự kiện với kiểm tra xung đột
   - check_conflicts: Kiểm tra xung đột trong khoảng thời gian
   - suggest_alternative_times: Đề xuất thời gian thay thế khi có xung đột
   - suggest_optimal_time: Đề xuất thời gian tối ưu dựa trên nghiên cứu năng suất (activity_type, duration_minutes, preferred_date, days_ahead)
   - resolve_conflict_by_moving_existing: Dời sự kiện cũ để giải quyết xung đột
   - resolve_conflict_by_deleting_existing: Xóa sự kiện cũ để giải quyết xung đột
   - update_event: Cập nhật sự kiện (cần: event_id)
   - delete_event: Xóa sự kiện (cần: event_id)
   - move_event: Di chuyển sự kiện (cần: event_id, thời gian mới)
   - get_event_by_id: Xem chi tiết sự kiện (cần: event_id)
   - check_availability: Kiểm tra lịch trống/bận

 Lưu ý quan trọng:
- Thời gian phải theo định dạng ISO: 'YYYY-MM-DDTHH:MM:SS' (VD: '2025-10-20T14:00:00')
- Ngày phải theo định dạng: 'YYYY-MM-DD' (VD: '2025-10-20')
- Múi giờ: Asia/Ho_Chi_Minh (GMT+7)
- Luôn dùng 'Current time (Asia/Ho_Chi_Minh)' cung cấp trong system message làm mốc (anchor date) để tính mọi cụm thời gian tự nhiên.
- Quy ước tuần bắt đầu vào Thứ 2 (ISO-8601), kết thúc Chủ nhật.
- Diễn giải tiếng Việt chuẩn về thời gian:
  * "ngày mai": anchor + 1 ngày.
  * "tuần này": khoảng từ Thứ 2..Chủ nhật chứa anchor.
  * "tuần sau": tuần ngay sau "tuần này" (mỗi ngày = anchor + 7 ngày cùng thứ).
  * "Thứ X tuần này": ngày Thứ X trong tuần chứa anchor. Ví dụ: nếu anchor là Thứ 2, 2025-10-20 thì "Thứ 6 tuần này" = 2025-10-24.
  * "Ngày này tuần sau": cùng thứ và ngày trong tuần kế tiếp so với anchor. Ví dụ: nếu anchor là Thứ 2, 2025-10-20 thì "Ngày này tuần sau" = 2025-10-27.
- Tránh suy luận theo múi giờ khác; tuyệt đối dùng Asia/Ho_Chi_Minh.
- Nếu người dùng nói 'ngày mai', 'tuần sau', hãy tính toán ngày chính xác theo các quy tắc trên.

QUY TRÌNH XỬ LÝ XUNG ĐỘT LỊCH:
- Khi tạo sự kiện mới, LUÔN dùng create_event_with_conflict_check thay vì create_event
- Nếu có xung đột, thông báo chi tiết và đề xuất 3 giải pháp:
  1) Dời sự kiện mới sang thời gian khác (dùng suggest_alternative_times)
  2) Dời sự kiện cũ sang thời gian khác (dùng resolve_conflict_by_moving_existing)
  3) Xóa sự kiện cũ (dùng resolve_conflict_by_deleting_existing)
- Hỏi người dùng muốn chọn giải pháp nào trước khi thực hiện

QUY TRÌNH ĐỀ XUẤT THỜI GIAN TỐI ƯU:
- Khi người dùng yêu cầu đề xuất thời gian phù hợp cho hoạt động, sử dụng suggest_optimal_time
- Các loại hoạt động được hỗ trợ:
  * meeting/họp: 10:00-11:30 AM hoặc 1:30-3:00 PM (thời gian họp tối ưu)
  * focus work/coding: 9:00-11:00 AM (thời gian tập trung cao)
  * creative work: 10:00-12:00 PM (thời gian sáng tạo)
  * admin/routine: 9:00-10:00 AM hoặc 4:00-5:00 PM (công việc hành chính)
- Sau khi đề xuất thời gian, hỏi người dùng có muốn tạo sự kiện không
- Nếu đồng ý, sử dụng create_event_with_conflict_check để tạo sự kiện

- Chỉ chọn một tool phù hợp nhất cho từng yêu cầu"""
    
    def get_tools(self) -> List[Any]:
        """Get all available tools from all agents."""
        if self._all_tools is None:
            raise RuntimeError("Supervisor agent not initialized. Call initialize() first.")
        return self._all_tools
    
    def get_supervisor_model(self):
        """Get the supervisor model with all tools bound."""
        return self.model.bind_tools(self.get_tools())
