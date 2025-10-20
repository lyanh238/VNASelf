"""
Supervisor Agent for routing requests to appropriate specialized agents
"""

from typing import List, Any, Dict
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from .base_agent import BaseAgent
from .health_agent import HealthAgent
from .calendar_agent import CalendarAgent


class SupervisorAgent(BaseAgent):
    """Supervisor agent that routes requests to appropriate specialized agents."""
    
    def __init__(self, model: ChatOpenAI, health_agent: HealthAgent, calendar_agent: CalendarAgent):
        super().__init__(model)
        self.name = "Supervisor Agent"
        self.health_agent = health_agent
        self.calendar_agent = calendar_agent
        self._all_tools = None
    
    async def initialize(self):
        """Initialize the supervisor with all available tools."""
        await self.calendar_agent.initialize()
        self._all_tools = self.health_agent.get_tools() + self.calendar_agent.get_tools()
    
    def get_system_prompt(self) -> str:
        return """Bạn là supervisor thông minh chọn công cụ phù hợp để giải quyết yêu cầu người dùng.

 Phân loại công cụ:

# 1. Sức khỏe (health_consultation_tool):
   - Triệu chứng bệnh, sức khỏe, khám bệnh
   - VD: đau đầu, sốt, ho, mệt mỏi

# 2. Lịch Google Calendar (các MCP tools):
   - list_upcoming_events: Xem lịch sắp tới
   - get_events_for_date: Xem lịch ngày cụ thể (cần format: YYYY-MM-DD)
   - search_events: Tìm kiếm sự kiện theo từ khóa
   - create_event: Tạo sự kiện mới (cần: tiêu đề, thời gian bắt đầu, thời gian kết thúc)
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
- Chỉ chọn một tool phù hợp nhất cho từng yêu cầu"""
    
    def get_tools(self) -> List[Any]:
        """Get all available tools from all agents."""
        if self._all_tools is None:
            raise RuntimeError("Supervisor agent not initialized. Call initialize() first.")
        return self._all_tools
    
    def get_supervisor_model(self):
        """Get the supervisor model with all tools bound."""
        return self.model.bind_tools(self.get_tools())
