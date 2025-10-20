"""
Enhanced Calendar Agent with real-life constraints
"""

from typing import List, Any, Dict, Optional
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

from agents.base_agent import BaseAgent
from services.calendar_service import CalendarService


class CalendarAgent(BaseAgent):
    """Enhanced calendar agent with real-life constraints and conflict resolution"""
    
    def __init__(self, model: ChatOpenAI, calendar_service: CalendarService):
        super().__init__(model)
        self.name = "Calendar Agent"
        self.calendar_service = calendar_service
        self._tools = None
    
    async def initialize(self):
        """Initialize the calendar agent with MCP tools"""
        if self._tools is None:
            self._tools = await self.calendar_service.get_calendar_tools()
        self.set_initialized(True)
    
    def get_system_prompt(self) -> str:
        return """You are an intelligent calendar assistant with advanced scheduling capabilities.

CORE CAPABILITIES:
- View upcoming events and specific dates
- Search events by keywords
- Create, update, delete, and move events
- Check availability and detect conflicts
- Resolve scheduling conflicts intelligently

REAL-LIFE CONSTRAINTS:
1. NO PAST BOOKING: Never create events in the past
2. AVAILABILITY CHECK: Always check availability before creating events
3. CONFLICT DETECTION: Detect overlapping events and suggest alternatives
4. SMART SUGGESTIONS: Provide alternative time slots when conflicts occur

TIME FORMATS:
- ISO DateTime: 'YYYY-MM-DDTHH:MM:SS' (e.g., '2025-10-20T14:00:00')
- Date: 'YYYY-MM-DD' (e.g., '2025-10-20')
- Timezone: Asia/Ho_Chi_Minh (GMT+7)

CONFLICT RESOLUTION:
- If overlap detected, suggest alternative times
- Offer to replace existing events if user confirms
- Provide multiple time slot options
- Consider user preferences and constraints

RESPONSE FORMAT:
- Always explain what you're doing
- Show available time slots when suggesting alternatives
- Confirm actions before executing
- Provide clear error messages with solutions"""
    
    def get_tools(self) -> List[Any]:
        """Get calendar tools with enhanced functionality"""
        if self._tools is None:
            raise RuntimeError("Calendar agent not initialized. Call initialize() first.")
        return self._tools
    
    @tool
    def check_availability_with_constraints(self, start_time: str, end_time: str) -> str:
        """
        Check availability with real-life constraints.
        
        Args:
            start_time: Start time in ISO format
            end_time: End time in ISO format
        """
        try:
            # Parse times
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            current_time = datetime.now()
            
            # Check if trying to book in the past
            if start_dt < current_time:
                return f"ERROR: Cannot book events in the past. Requested time {start_time} is before current time {current_time.isoformat()}"
            
            # Check availability using calendar service
            availability = self.calendar_service.check_availability(start_time, end_time)
            
            if availability['available']:
                return f"Time slot {start_time} to {end_time} is available for booking."
            else:
                conflicts = availability.get('conflicts', [])
                conflict_info = "\n".join([f"- {conflict['title']} ({conflict['start']} to {conflict['end']})" 
                                         for conflict in conflicts])
                return f"CONFLICT DETECTED: Time slot {start_time} to {end_time} is not available.\nConflicting events:\n{conflict_info}"
        
        except Exception as e:
            return f"Error checking availability: {str(e)}"
    
    @tool
    def suggest_alternative_times(self, preferred_start: str, preferred_end: str, 
                                 duration_hours: int = 1) -> str:
        """
        Suggest alternative time slots when conflicts occur.
        
        Args:
            preferred_start: Preferred start time in ISO format
            preferred_end: Preferred end time in ISO format
            duration_hours: Duration in hours
        """
        try:
            # Parse preferred time
            pref_start = datetime.fromisoformat(preferred_start.replace('Z', '+00:00'))
            
            # Generate alternative suggestions
            alternatives = []
            current_time = datetime.now()
            
            # Suggest same day alternatives (morning, afternoon, evening)
            for hour_offset in [9, 14, 19]:  # 9 AM, 2 PM, 7 PM
                alt_start = pref_start.replace(hour=hour_offset, minute=0, second=0, microsecond=0)
                alt_end = alt_start + timedelta(hours=duration_hours)
                
                if alt_start > current_time:
                    # Check if this time is available
                    availability = self.calendar_service.check_availability(
                        alt_start.isoformat(), alt_end.isoformat()
                    )
                    if availability['available']:
                        alternatives.append({
                            'start': alt_start.isoformat(),
                            'end': alt_end.isoformat(),
                            'description': f"{hour_offset}:00 {'AM' if hour_offset < 12 else 'PM'}"
                        })
            
            # Suggest next day alternatives
            next_day = pref_start + timedelta(days=1)
            for hour_offset in [9, 14, 19]:
                alt_start = next_day.replace(hour=hour_offset, minute=0, second=0, microsecond=0)
                alt_end = alt_start + timedelta(hours=duration_hours)
                
                availability = self.calendar_service.check_availability(
                    alt_start.isoformat(), alt_end.isoformat()
                )
                if availability['available']:
                    alternatives.append({
                        'start': alt_start.isoformat(),
                        'end': alt_end.isoformat(),
                        'description': f"Next day at {hour_offset}:00 {'AM' if hour_offset < 12 else 'PM'}"
                    })
            
            if alternatives:
                alt_text = "\n".join([
                    f"- {alt['description']}: {alt['start']} to {alt['end']}"
                    for alt in alternatives[:5]  # Limit to 5 suggestions
                ])
                return f"ALTERNATIVE TIME SLOTS AVAILABLE:\n{alt_text}"
            else:
                return "No alternative time slots found. Please try a different date or time."
        
        except Exception as e:
            return f"Error generating alternatives: {str(e)}"
    
    @tool
    def create_event_with_validation(self, title: str, start_time: str, end_time: str, 
                                   description: str = "") -> str:
        """
        Create event with comprehensive validation and conflict resolution.
        
        Args:
            title: Event title
            start_time: Start time in ISO format
            end_time: End time in ISO format
            description: Event description
        """
        try:
            # Validate times
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            current_time = datetime.now()
            
            # Check if trying to book in the past
            if start_dt < current_time:
                return f"ERROR: Cannot create events in the past. Requested time {start_time} is before current time {current_time.isoformat()}"
            
            # Check availability first
            availability = self.calendar_service.check_availability(start_time, end_time)
            
            if not availability['available']:
                conflicts = availability.get('conflicts', [])
                conflict_info = "\n".join([f"- {conflict['title']} ({conflict['start']} to {conflict['end']})" 
                                         for conflict in conflicts])
                
                return f"CONFLICT DETECTED: Cannot create event due to scheduling conflicts.\nConflicting events:\n{conflict_info}\n\nPlease use suggest_alternative_times to find available slots."
            
            # Create the event
            event_data = {
                'title': title,
                'start_time': start_time,
                'end_time': end_time,
                'description': description
            }
            
            result = self.calendar_service.create_event(event_data)
            
            if result['success']:
                return f"SUCCESS: Event '{title}' created successfully for {start_time} to {end_time}."
            else:
                return f"ERROR: Failed to create event: {result.get('error', 'Unknown error')}"
        
        except Exception as e:
            return f"Error creating event: {str(e)}"
    
    @tool
    def replace_conflicting_event(self, new_title: str, new_start: str, new_end: str,
                                conflicting_event_id: str, new_description: str = "") -> str:
        """
        Replace a conflicting event with a new one.
        
        Args:
            new_title: Title for the new event
            new_start: Start time for the new event
            new_end: End time for the new event
            conflicting_event_id: ID of the event to replace
            new_description: Description for the new event
        """
        try:
            # First delete the conflicting event
            delete_result = self.calendar_service.delete_event(conflicting_event_id)
            
            if not delete_result['success']:
                return f"ERROR: Could not delete conflicting event: {delete_result.get('error', 'Unknown error')}"
            
            # Create the new event
            event_data = {
                'title': new_title,
                'start_time': new_start,
                'end_time': new_end,
                'description': new_description
            }
            
            create_result = self.calendar_service.create_event(event_data)
            
            if create_result['success']:
                return f"SUCCESS: Replaced conflicting event with '{new_title}' for {new_start} to {new_end}."
            else:
                return f"ERROR: Failed to create replacement event: {create_result.get('error', 'Unknown error')}"
        
        except Exception as e:
            return f"Error replacing event: {str(e)}"


