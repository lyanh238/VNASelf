"""
Calendar Agent for Google Calendar management
"""
from datetime import datetime, timedelta
from dateutil import parser
from typing import List, Any, Optional, Tuple
from langchain_openai import ChatOpenAI
from .base_agent import BaseAgent
from services.mcp_service import MCPService
import pytz
from langchain_core.tools import tool
from langsmith import traceable
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
            self._calendar_tools = self._calendar_tools + [self._create_vn_parse_date_tool()]
    
    def get_system_prompt(self) -> str:
        return """You are an intelligent calendar assistant specialized in Google Calendar with conflict detection and resolution capabilities.

YOU CAN USE THE FOLLOWING TOOLS:

1. VIEW CALENDAR:
   - list_upcoming_events: View upcoming calendar (max_results: number of events)
   - get_events_for_date: View calendar for specific date (date: YYYY-MM-DD)
   - search_events: Search events by keyword (query: keyword)
   - get_event_by_id: View specific event details (event_id: event ID)

2. CHECK CALENDAR:
   - check_availability: Check calendar availability/busy (date, start_time, end_time)
   - check_conflicts: Check conflicts in time range (start_datetime, end_datetime)

3. CREATE EVENTS:
   - create_event: Create new event (summary, start_datetime, end_datetime, description, location, attendees)
   - create_event_with_conflict_check: Create event with conflict checking (summary, start_datetime, end_datetime, description, location, attendees, force_create)

4. MANAGE EVENTS:
   - update_event: Update event (event_id, summary, start_datetime, end_datetime, description, location)
   - delete_event: Delete event (event_id)
   - move_event: Move event (event_id, new_start_datetime, new_end_datetime)

5. RESOLVE CONFLICTS:
   - suggest_alternative_times: Suggest alternative times (start_datetime, end_datetime, duration_minutes, days_ahead)
   - resolve_conflict_by_moving_existing: Move existing event (existing_event_id, new_start_datetime, new_end_datetime)
   - resolve_conflict_by_deleting_existing: Delete existing event (existing_event_id)

6. OPTIMAL TIME SUGGESTION:
   - suggest_optimal_time: Suggest optimal time (activity_type, duration_minutes, preferred_date, days_ahead)

7. HELPER TOOLS:
   - vn_parse_date: Parse Vietnamese time expressions (phrase: "ngày mai", "thứ 6 tuần này", etc.)

NEW EVENT CREATION PROCESS:
1. ALWAYS check conflicts before creating new event using check_conflicts()
2. If conflicts exist:
   - Notify details about conflicting events
   - Suggest solutions:
     a) Move new event to different time (use suggest_alternative_times)
     b) Move existing event to different time (use resolve_conflict_by_moving_existing)
     c) Delete existing event (use resolve_conflict_by_deleting_existing)
   - Ask user which solution they prefer
3. If no conflicts: create event normally

Important Notes:
- Time must be in ISO format: 'YYYY-MM-DDTHH:MM:SS'
- Date must be in format: 'YYYY-MM-DD'
- Timezone: Asia/Ho_Chi_Minh (GMT+7)
- Always use 'Current time (Asia/Ho_Chi_Minh)' provided in system message as anchor date to calculate all natural time expressions.
- Week convention: starts Monday (ISO-8601), ends Sunday.
- Vietnamese time interpretation rules:
  * "ngày mai" (tomorrow) = anchor + 1 day
  * "tuần này" (this week) = week containing anchor (Monday..Sunday)
  * "tuần sau" (next week) = week immediately after week containing anchor
  * "Thứ X tuần này" (Weekday X this week) = Weekday X in week containing anchor (e.g., anchor Monday 2025-10-20 ⇒ "Thứ 6 tuần này" (Friday this week) = 2025-10-24)
  * "Ngày này tuần sau" (This day next week) = same weekday, 7 days after anchor (e.g., 2025-10-20 ⇒ 2025-10-27)
- Avoid timezone drift: always calculate according to Asia/Ho_Chi_Minh.
- Example: if today (anchor) is 2025-10-20 then:
  * 'ngày mai' (tomorrow) = 2025-10-21
  * 'cuối tuần' (weekend) = 2025-10-25 & 2025-10-26
  * 'thứ 6 tuần này' (Friday this week) = 2025-10-24
  * 'ngày này tuần sau' (This day next week) = 2025-10-27

TOOL USAGE GUIDE:
- When users ask about calendar: use list_upcoming_events, get_events_for_date, or search_events
- When users want to create event: ALWAYS use create_event_with_conflict_check
- When conflicts exist: use suggest_alternative_times, resolve_conflict_by_moving_existing, or resolve_conflict_by_deleting_existing
- When users request optimal time suggestion: use suggest_optimal_time
- When need to parse Vietnamese time: use vn_parse_date
- When need to check availability: use check_availability

VIETNAMESE TIME PROCESSING:
- ALWAYS use vn_parse_date before creating events with Vietnamese time
- Example: "21h-6h sáng mai" → vn_parse_date("21h-6h sáng mai") → "2025-10-27T21:00:00+07:00..2025-10-28T06:00:00+07:00"
- Example: "thứ 6 tuần này" → vn_parse_date("thứ 6 tuần này") → "2025-10-24"
- Example: "ngày mai" → vn_parse_date("ngày mai") → "2025-10-28"

EVENT CREATION WITH VIETNAMESE TIME PROCESS:
1. Use vn_parse_date to convert Vietnamese time to ISO format
2. Use check_conflicts to check for conflicts
3. If no conflicts: use create_event_with_conflict_check
4. If conflicts exist: suggest solutions and ask user

OPTIMAL TIME SUGGESTION PROCESS:
1. When user requests optimal time suggestion for activities, use suggest_optimal_time
2. Supported activity types:
   - meeting/họp: 10:00-11:30 AM or 1:30-3:00 PM (optimal meeting time)
   - focus work/coding: 9:00-11:00 AM (high focus time)
   - creative work: 10:00-12:00 PM (creative time)
   - admin/routine: 9:00-10:00 AM or 4:00-5:00 PM (administrative work)
3. After suggesting time, ask user if they want to create event
4. If agreed, use create_event_with_conflict_check to create event

USE MULTIPLE TOOLS WHEN NECESSARY TO PROVIDE COMPLETE INFORMATION TO USERS!"""
    
    def get_tools(self) -> List[Any]:
        """Get calendar tools from MCP service."""
        if self._calendar_tools is None:
            raise RuntimeError("Calendar agent not initialized. Call initialize() first.")
        return self._calendar_tools

    # -------------------------------
    # Vietnamese natural date parser
    # -------------------------------
    
    def parse_time_with_llm(self, phrase: str) -> str:
        """Use LLM to parse Vietnamese time expressions into ISO format."""
        now = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
        system_prompt = f"""You are a Vietnamese time expression analyzer.
Task: convert time expressions to ISO format.
Examples:
- "ngày mai" -> "2025-11-02"
- "cuối tuần" -> "2025-11-01..2025-11-02"
- "2 ngày nữa" -> "2025-11-03"
- "ngày này năm sau" -> "2026-11-01"
- "tối nay" -> "2025-11-01T19:00:00..2025-11-01T23:59:59"
- anchor time is {now}
Return result as ISO format string, no additional explanation."""

        result = self.model.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": phrase}
        ])
        return result.content.strip()

    def fallback_date_parser(self, text: str):
        """Simple parser for common Vietnamese time phrases."""
        text = text.lower().strip()
        today = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))

        if "ngày mai" in text:
            return (today + timedelta(days=1)).isoformat()
        elif "ngày kia" in text:
            return (today + timedelta(days=2)).isoformat()
        elif "hôm qua" in text:
            return (today - timedelta(days=1)).isoformat()
        elif "năm sau" in text:
            return today.replace(year=today.year + 1).isoformat()
        else:
            # If still not understood, use LLM to guess
            return self.parse_time_with_llm(text)

    def parse_natural_date(self, text: str):
        """Parse natural time expressions, try dateutil.parser first, use fallback if fails."""
        try:
            parsed = parser.parse(text)
            # Convert to ISO format if datetime
            if isinstance(parsed, datetime):
                # Ensure timezone exists
                if parsed.tzinfo is None:
                    parsed = pytz.timezone("Asia/Ho_Chi_Minh").localize(parsed)
                return parsed.isoformat()
            return str(parsed)
        except Exception:
            return self.fallback_date_parser(text)

    def _create_vn_parse_date_tool(self):
        """Create the vn_parse_date tool."""
        
        @tool
        @traceable(name="tools.calendar.vn_parse_date")
        def vn_parse_date(phrase: str) -> str:
            """Parse Vietnamese time expressions into ISO format.

            Input:
            - phrase: examples 'ngày mai', 'thứ 6 tuần này', 'cuối tuần', '2 ngày nữa', 'tối nay'

            Output:
            - If single day: returns 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SS+07:00'
            - If time range: returns 'YYYY-MM-DD..YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SS..YYYY-MM-DDTHH:MM:SS'
            """
            return self.parse_natural_date(phrase)
        
        return vn_parse_date