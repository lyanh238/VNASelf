from typing import Any
from datetime import datetime, timedelta
import os
import sys
import pickle
import pytz
from mcp.server.fastmcp import FastMCP
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying these scopes, delete the token.pickle file
SCOPES = ['https://www.googleapis.com/auth/calendar']
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Initialize FastMCP server
mcp = FastMCP("google_calendar")

# Timezone setting for Vietnam
TIMEZONE = 'Asia/Ho_Chi_Minh'
VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")
def get_now_vietnam():
    return datetime.now(VN_TZ)

now = get_now_vietnam().isoformat()
def get_calendar_service():
    """Get authenticated Google Calendar service."""
    creds = None
    
    # Token file stores user's access and refresh tokens
    if os.path.exists('token.pickle'):
        try:
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        except Exception as e:
            print(f"Warning: Could not load token.pickle: {e}")
            creds = None
    
    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Warning: Could not refresh token: {e}")
                creds = None
        
        if not creds or not creds.valid:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError(
                    "credentials.json not found. Please download it from Google Cloud Console.\n"
                    "Steps to fix:\n"
                    "1. Go to Google Cloud Console (https://console.cloud.google.com/)\n"
                    "2. Create a new project or select existing one\n"
                    "3. Enable Google Calendar API\n"
                    "4. Create credentials (OAuth 2.0 Client ID)\n"
                    "5. Download credentials.json and place it in the backend folder"
                )
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                raise Exception(f"Failed to authenticate with Google Calendar API: {e}")
        
        # Save credentials for next run
        try:
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        except Exception as e:
            print(f"Warning: Could not save token: {e}")
    
    return build('calendar', 'v3', credentials=creds)

def format_event(event: dict) -> str:
    """Format a calendar event into a readable string."""
    summary = event.get('summary', 'No Title')
    start = event['start'].get('dateTime', event['start'].get('date'))
    end = event['end'].get('dateTime', event['end'].get('date'))
    location = event.get('location', 'No location specified')
    description = event.get('description', 'No description available')
    event_id = event.get('id', 'Unknown ID')
    
    return f"""
Event ID: {event_id}
Event: {summary}
Start: {start}
End: {end}
Location: {location}
Description: {description}
"""


@mcp.tool()
async def list_upcoming_events(max_results: int = 10) -> str:
    """List upcoming events from the primary calendar.
    
    Args:
        max_results: Maximum number of events to return (default: 10)
    """
    try:
        service = get_calendar_service()
        
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=get_now_vietnam().isoformat(),
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return "No upcoming events found."
        
        formatted_events = [format_event(event) for event in events]
        return "\n---\n".join(formatted_events)
        
    except Exception as e:
        return f"Error fetching events: {str(e)}"


@mcp.tool()
async def get_events_for_date(date: str) -> str:
    """Get all events for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format (e.g., 2025-10-17)
    """
    try:
        service = get_calendar_service()
        
        # Parse date and create time range
        target_date = datetime.strptime(date, '%Y-%m-%d')
        target_date = VN_TZ.localize(target_date)  # → "2025-10-18T00:00:00+07:00"
        time_min = target_date.isoformat()
        time_max = (target_date + timedelta(days=1)).isoformat() 
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return f"No events found for {date}."
        
        formatted_events = [format_event(event) for event in events]
        return f"Events for {date}:\n\n" + "\n---\n".join(formatted_events)
        
    except ValueError:
        return "Invalid date format. Please use YYYY-MM-DD format."
    except Exception as e:
        return f"Error fetching events: {str(e)}"
@mcp.tool()
async def check_availability(date: str, start_time: str = "00:00", end_time: str = "23:59") -> str:
    """Check calendar availability for a specific date.
    
    Args:
        date: Date to check in YYYY-MM-DD format (e.g., 2025-10-20)
        start_time: Start time to check (HH:MM, default: 00:00)
        end_time: End time to check (HH:MM, default: 23:59)
    
    Returns:
        List of busy and free time periods for the day
    """
    try:
        service = get_calendar_service()
        
        # Parse datetime
        start_dt = datetime.strptime(f"{date} {start_time}", '%Y-%m-%d %H:%M')
        end_dt = datetime.strptime(f"{date} {end_time}", '%Y-%m-%d %H:%M')
        
        start_dt = VN_TZ.localize(start_dt) 
        end_dt = VN_TZ.localize(end_dt) 
        
        # Get all events in the time range
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_dt.isoformat(),
            timeMax=end_dt.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Create report
        result = f"Calendar report for {date} (from {start_time} to {end_time}):\n\n"
        
        if not events:
            result += "You are completely free during this time period!\n"
            result += f"Free time: {start_time} - {end_time}"
            return result
        
        # List of busy events
        result += f"Found {len(events)} scheduled events:\n\n"
        
        busy_periods = []
        for event in events:
            summary = event.get('summary', 'No Title')
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            location = event.get('location', '')
            
            # Parse time
            if 'T' in start:
                start_time_obj = datetime.fromisoformat(start.replace('Z', '+00:00'))
                end_time_obj = datetime.fromisoformat(end.replace('Z', '+00:00'))
                
                # Convert to Vietnam timezone
                start_time_obj = start_time_obj.astimezone(VN_TZ)
                end_time_obj = end_time_obj.astimezone(VN_TZ)
                
                busy_periods.append((start_time_obj, end_time_obj))
                
                result += f"   {start_time_obj.strftime('%H:%M')} - {end_time_obj.strftime('%H:%M')}: {summary}"
                if location:
                    result += f"  {location}"
                result += "\n"
        
        # Find free time periods
        result += "\nFree time:\n"
        
        if busy_periods:
            # Sort busy periods
            busy_periods.sort(key=lambda x: x[0])
            
            free_periods = []
            current_time = start_dt
            
            for busy_start, busy_end in busy_periods:
                if current_time < busy_start:
                    free_periods.append((current_time, busy_start))
                current_time = max(current_time, busy_end)
            
            # Check time period after last event
            if current_time < end_dt:
                free_periods.append((current_time, end_dt))
            
            if free_periods:
                for free_start, free_end in free_periods:
                    duration_minutes = int((free_end - free_start).total_seconds() / 60)
                    result += f"   {free_start.strftime('%H:%M')} - {free_end.strftime('%H:%M')} ({duration_minutes} minutes)\n"
            else:
                result += "   No free time available in this range\n"
        
        return result
        
    except ValueError as e:
        return f"Format error: {str(e)}\nPlease use YYYY-MM-DD format for date and HH:MM for time."
    except Exception as e:
        return f"Error checking calendar: {str(e)}"
@mcp.tool()
async def search_events(query: str, max_results: int = 10) -> str:
    """Search for events by keyword.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 10)
    """
    try:
        service = get_calendar_service()
        
        # Get current time
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin= get_now_vietnam().isoformat(),
            maxResults=max_results,
            q=query,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return f"No events found matching '{query}'."
        
        formatted_events = [format_event(event) for event in events]
        return f"Events matching '{query}':\n\n" + "\n---\n".join(formatted_events)
        
    except Exception as e:
        return f"Error searching events: {str(e)}"


@mcp.tool()
async def check_conflicts(
    start_datetime: str,
    end_datetime: str
) -> str:
    """Check for scheduling conflicts in a time range.
    
    Args:
        start_datetime: Start date and time in ISO format (e.g., '2025-10-20T10:00:00')
        end_datetime: End date and time in ISO format (e.g., '2025-10-20T11:00:00')
    
    Returns:
        Information about conflicting events or confirmation of no conflicts
    """
    try:
        service = get_calendar_service()
        
        # Ensure datetime strings have timezone information
        if not start_datetime.endswith('+07:00') and not start_datetime.endswith('Z'):
            start_datetime = start_datetime + '+07:00'
        if not end_datetime.endswith('+07:00') and not end_datetime.endswith('Z'):
            end_datetime = end_datetime + '+07:00'
        
        # Get events in the time range
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_datetime,
            timeMax=end_datetime,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return "No conflicts found. Time slot is available."
        
        # Format conflicting events
        conflict_info = f"Found {len(events)} conflicting event(s):\n\n"
        for event in events:
            summary = event.get('summary', 'No Title')
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            event_id = event.get('id', 'Unknown ID')
            location = event.get('location', '')
            
            conflict_info += f"Event ID: {event_id}\n"
            conflict_info += f"Title: {summary}\n"
            conflict_info += f"Time: {start} - {end}\n"
            if location:
                conflict_info += f"Location: {location}\n"
            conflict_info += "\n"
        
        return conflict_info
        
    except Exception as e:
        error_msg = str(e)
        if "HttpError 400" in error_msg:
            return f"Authentication Error: Please check your Google Calendar credentials.\n" \
                   f"Error details: {error_msg}\n\n" \
                   f"To fix this:\n" \
                   f"1. Make sure credentials.json exists in the backend folder\n" \
                   f"2. Delete token.pickle and re-authenticate\n" \
                   f"3. Check if Google Calendar API is enabled in your project"
        else:
            return f"Error checking conflicts: {error_msg}"


@mcp.tool()
async def create_event_with_conflict_check(
    summary: str,
    start_datetime: str,
    end_datetime: str,
    description: str = "",
    location: str = "",
    attendees: str = "",
    force_create: bool = False
) -> str:
    """Create a new calendar event with conflict detection.
    
    Args:
        summary: Event title/summary
        start_datetime: Start date and time in ISO format (e.g., '2025-10-20T10:00:00')
        end_datetime: End date and time in ISO format (e.g., '2025-10-20T11:00:00')
        description: Event description (optional)
        location: Event location (optional)
        attendees: Comma-separated email addresses of attendees (optional)
        force_create: If True, create event even if conflicts exist (default: False)
    """
    try:
        # Check for conflicts first
        conflict_check = await check_conflicts(start_datetime, end_datetime)
        
        if "No conflicts found" not in conflict_check and not force_create:
            return f"CONFLICT DETECTED:\n\n{conflict_check}\nPlease resolve conflicts before creating the event. Use force_create=True to override."
        
        service = get_calendar_service()
        
        # Build event object
        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_datetime,
                'timeZone': TIMEZONE,
            },
            'end': {
                'dateTime': end_datetime,
                'timeZone': TIMEZONE,
            },
        }
        
        # Add attendees if provided
        if attendees:
            attendee_list = [{'email': email.strip()} for email in attendees.split(',')]
            event['attendees'] = attendee_list
        
        # Create the event
        created_event = service.events().insert(
            calendarId='primary',
            body=event,
            sendUpdates='all' if attendees else 'none'
        ).execute()
        
        result = f"Event created successfully!\n{format_event(created_event)}"
        if force_create and "No conflicts found" not in conflict_check:
            result = f"WARNING: Event created despite conflicts!\n\n{conflict_check}\n\n{result}"
        
        return result
        
    except Exception as e:
        return f"Error creating event: {str(e)}"


@mcp.tool()
async def create_event(
    summary: str,
    start_datetime: str,
    end_datetime: str,
    description: str = "",
    location: str = "",
    attendees: str = ""
) -> str:
    """Create a new calendar event (legacy function for backward compatibility).
    
    Args:
        summary: Event title/summary
        start_datetime: Start date and time in ISO format (e.g., '2025-10-20T10:00:00')
        end_datetime: End date and time in ISO format (e.g., '2025-10-20T11:00:00')
        description: Event description (optional)
        location: Event location (optional)
        attendees: Comma-separated email addresses of attendees (optional)
    """
    return await create_event_with_conflict_check(
        summary, start_datetime, end_datetime, description, location, attendees, force_create=True
    )


@mcp.tool()
async def update_event(
    event_id: str,
    summary: str = None,
    start_datetime: str = None,
    end_datetime: str = None,
    description: str = None,
    location: str = None
) -> str:
    """Update an existing calendar event.
    
    Args:
        event_id: The ID of the event to update
        summary: New event title (optional)
        start_datetime: New start time in ISO format (optional)
        end_datetime: New end time in ISO format (optional)
        description: New description (optional)
        location: New location (optional)
    """
    try:
        service = get_calendar_service()
        
        # Get the existing event
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        
        # Update fields if provided
        if summary is not None:
            event['summary'] = summary
        if start_datetime is not None:
            event['start'] = {'dateTime': start_datetime, 'timeZone': TIMEZONE}
        if end_datetime is not None:
            event['end'] = {'dateTime': end_datetime, 'timeZone': TIMEZONE}
        if description is not None:
            event['description'] = description
        if location is not None:
            event['location'] = location
        
        # Update the event
        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event,
            sendUpdates='all'
        ).execute()
        
        return f"Event updated successfully!\n{format_event(updated_event)}"
        
    except Exception as e:
        return f"Error updating event: {str(e)}"


@mcp.tool()
async def resolve_conflict_by_moving_existing(
    existing_event_id: str,
    new_start_datetime: str,
    new_end_datetime: str
) -> str:
    """Move an existing conflicting event to a new time slot.
    
    Args:
        existing_event_id: ID of the existing event to move
        new_start_datetime: New start time in ISO format
        new_end_datetime: New end time in ISO format
    
    Returns:
        Confirmation of the move operation
    """
    try:
        service = get_calendar_service()
        
        # Get the existing event
        event = service.events().get(calendarId='primary', eventId=existing_event_id).execute()
        event_summary = event.get('summary', 'Unknown Event')
        
        # Update the event with new times
        event['start'] = {'dateTime': new_start_datetime, 'timeZone': TIMEZONE}
        event['end'] = {'dateTime': new_end_datetime, 'timeZone': TIMEZONE}
        
        # Update the event
        updated_event = service.events().update(
            calendarId='primary',
            eventId=existing_event_id,
            body=event,
            sendUpdates='all'
        ).execute()
        
        return f"Event '{event_summary}' moved successfully!\n{format_event(updated_event)}"
        
    except Exception as e:
        return f"Error moving event: {str(e)}"


@mcp.tool()
async def resolve_conflict_by_deleting_existing(existing_event_id: str) -> str:
    """Delete an existing conflicting event to resolve conflict.
    
    Args:
        existing_event_id: ID of the existing event to delete
    
    Returns:
        Confirmation of the deletion
    """
    try:
        service = get_calendar_service()
        
        # Get event details before deleting
        event = service.events().get(calendarId='primary', eventId=existing_event_id).execute()
        event_summary = event.get('summary', 'Unknown Event')
        
        # Delete the event
        service.events().delete(
            calendarId='primary',
            eventId=existing_event_id,
            sendUpdates='all'
        ).execute()
        
        return f"Event '{event_summary}' (ID: {existing_event_id}) deleted successfully to resolve conflict!"
        
    except Exception as e:
        return f"Error deleting event: {str(e)}"


@mcp.tool()
async def suggest_alternative_times(
    start_datetime: str,
    end_datetime: str,
    duration_minutes: int = 60,
    days_ahead: int = 7
) -> str:
    """Suggest alternative time slots when conflicts are detected.
    
    Args:
        start_datetime: Original start time in ISO format
        end_datetime: Original end time in ISO format
        duration_minutes: Duration of the event in minutes (default: 60)
        days_ahead: Number of days to look ahead for alternatives (default: 7)
    
    Returns:
        List of suggested alternative time slots
    """
    try:
        service = get_calendar_service()
        
        # Parse original time
        original_start = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
        original_end = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
        duration = timedelta(minutes=duration_minutes)
        
        # Convert to Vietnam timezone
        original_start = original_start.astimezone(VN_TZ)
        original_end = original_end.astimezone(VN_TZ)
        
        suggestions = []
        current_date = original_start.date()
        
        # Look for alternatives in the next few days
        for day_offset in range(days_ahead + 1):
            check_date = current_date + timedelta(days=day_offset)
            
            # Check multiple time slots throughout the day
            time_slots = [
                (9, 0),   # 9:00 AM
                (10, 0),  # 10:00 AM
                (11, 0),  # 11:00 AM
                (14, 0),  # 2:00 PM
                (15, 0),  # 3:00 PM
                (16, 0),  # 4:00 PM
            ]
            
            for hour, minute in time_slots:
                slot_start = VN_TZ.localize(datetime.combine(check_date, datetime.min.time().replace(hour=hour, minute=minute)))
                slot_end = slot_start + duration
                
                # Check if this slot is available
                events_result = service.events().list(
                    calendarId='primary',
                    timeMin=slot_start.isoformat(),
                    timeMax=slot_end.isoformat(),
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                events = events_result.get('items', [])
                
                if not events:
                    suggestions.append({
                        'date': check_date.isoformat(),
                        'start': slot_start.isoformat(),
                        'end': slot_end.isoformat(),
                        'day_name': check_date.strftime('%A'),
                        'time_str': slot_start.strftime('%H:%M')
                    })
                
                if len(suggestions) >= 5:  # Limit to 5 suggestions
                    break
            
            if len(suggestions) >= 5:
                break
        
        if not suggestions:
            return "No alternative time slots found in the next 7 days. Please try a different duration or extend the search period."
        
        # Format suggestions
        result = f"Found {len(suggestions)} alternative time slots:\n\n"
        for i, suggestion in enumerate(suggestions, 1):
            result += f"{i}. {suggestion['day_name']}, {suggestion['date']} at {suggestion['time_str']}\n"
            result += f"   Start: {suggestion['start']}\n"
            result += f"   End: {suggestion['end']}\n\n"
        
        return result
        
    except Exception as e:
        return f"Error finding alternative times: {str(e)}"


@mcp.tool()
async def suggest_optimal_time(
    activity_type: str,
    duration_minutes: int = 60,
    preferred_date: str = None,
    days_ahead: int = 7
) -> str:
    """Suggest optimal time slots for activities based on productivity research.
    
    Args:
        activity_type: Type of activity (meeting, focus work, creative work, etc.)
        duration_minutes: Duration of the activity in minutes (default: 60)
        preferred_date: Preferred date in YYYY-MM-DD format (optional)
        days_ahead: Number of days to look ahead for suggestions (default: 7)
    
    Returns:
        List of optimal time suggestions with productivity reasoning
    """
    try:
        service = get_calendar_service()
        
        # Get current time
        now = get_now_vietnam()
        
        # Determine optimal time ranges based on activity type and productivity research
        optimal_ranges = []
        
        if activity_type.lower() in ['meeting', 'họp', 'cuộc họp', 'team meeting', 'client meeting']:
            # Optimal meeting times: 10:00-11:30 AM or 1:30-3:00 PM
            optimal_ranges = [
                (10, 0, 11, 30),   # 10:00-11:30 AM
                (13, 30, 15, 0),   # 1:30-3:00 PM
            ]
        elif activity_type.lower() in ['focus work', 'deep work', 'coding', 'writing', 'analysis']:
            # Optimal focus work times: 9:00-11:00 AM (peak cognitive performance)
            optimal_ranges = [
                (9, 0, 11, 0),     # 9:00-11:00 AM
                (14, 0, 16, 0),    # 2:00-4:00 PM (secondary peak)
            ]
        elif activity_type.lower() in ['creative work', 'brainstorming', 'planning', 'design']:
            # Creative work: 10:00-12:00 PM (when creativity peaks)
            optimal_ranges = [
                (10, 0, 12, 0),    # 10:00-12:00 PM
                (15, 0, 17, 0),    # 3:00-5:00 PM (afternoon creativity)
            ]
        elif activity_type.lower() in ['admin', 'email', 'routine', 'administrative']:
            # Administrative tasks: 9:00-10:00 AM or 4:00-5:00 PM
            optimal_ranges = [
                (9, 0, 10, 0),     # 9:00-10:00 AM
                (16, 0, 17, 0),    # 4:00-5:00 PM
            ]
        else:
            # Default: general productivity times
            optimal_ranges = [
                (10, 0, 11, 30),   # 10:00-11:30 AM
                (13, 30, 15, 0),   # 1:30-3:00 PM
            ]
        
        # Determine start date
        if preferred_date:
            try:
                start_date = datetime.strptime(preferred_date, '%Y-%m-%d').date()
            except ValueError:
                return f"Invalid date format. Please use YYYY-MM-DD format."
        else:
            start_date = now.date()
        
        suggestions = []
        duration = timedelta(minutes=duration_minutes)
        
        # Look for optimal time slots
        for day_offset in range(days_ahead + 1):
            check_date = start_date + timedelta(days=day_offset)
            
            # Skip weekends for work activities unless specifically requested
            if check_date.weekday() >= 5 and activity_type.lower() in ['meeting', 'focus work', 'admin']:
                continue
            
            for start_hour, start_min, end_hour, end_min in optimal_ranges:
                # Calculate potential start times within the optimal range
                range_start = VN_TZ.localize(datetime.combine(check_date, datetime.min.time().replace(hour=start_hour, minute=start_min)))
                range_end = VN_TZ.localize(datetime.combine(check_date, datetime.min.time().replace(hour=end_hour, minute=end_min)))
                
                # Generate time slots within the range
                current_time = range_start
                while current_time + duration <= range_end:
                    slot_start = current_time
                    slot_end = slot_start + duration
                    
                    # Check if this slot is available
                    events_result = service.events().list(
                        calendarId='primary',
                        timeMin=slot_start.isoformat(),
                        timeMax=slot_end.isoformat(),
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                    
                    events = events_result.get('items', [])
                    
                    if not events:
                        # Calculate productivity score based on time and activity type
                        productivity_score = calculate_productivity_score(
                            slot_start, activity_type, check_date.weekday()
                        )
                        
                        suggestions.append({
                            'date': check_date.isoformat(),
                            'start': slot_start.isoformat(),
                            'end': slot_end.isoformat(),
                            'day_name': check_date.strftime('%A'),
                            'time_str': slot_start.strftime('%H:%M'),
                            'productivity_score': productivity_score,
                            'reasoning': get_productivity_reasoning(slot_start, activity_type)
                        })
                    
                    # Move to next 30-minute slot
                    current_time += timedelta(minutes=30)
                    
                    if len(suggestions) >= 5:  # Limit to 5 suggestions
                        break
                
                if len(suggestions) >= 5:
                    break
            
            if len(suggestions) >= 5:
                break
        
        if not suggestions:
            return f"No optimal time slots found for '{activity_type}' in the next {days_ahead} days. Please try a different activity type or extend the search period."
        
        # Sort by productivity score (highest first)
        suggestions.sort(key=lambda x: x['productivity_score'], reverse=True)
        
        # Format suggestions
        result = f"🎯 Optimal time suggestions for '{activity_type}' ({duration_minutes} minutes):\n\n"
        result += f"Based on productivity research, here are the best time slots:\n\n"
        
        for i, suggestion in enumerate(suggestions, 1):
            result += f"**{i}. {suggestion['day_name']}, {suggestion['date']} at {suggestion['time_str']}**\n"
            result += f"   📅 Start: {suggestion['start']}\n"
            result += f"   📅 End: {suggestion['end']}\n"
            result += f"   ⭐ Productivity Score: {suggestion['productivity_score']}/10\n"
            result += f"   💡 Why this time: {suggestion['reasoning']}\n\n"
        
        result += "💡 **Productivity Tips:**\n"
        result += "• Meetings work best between 10:00-11:30 AM or 1:30-3:00 PM\n"
        result += "• Focus work is most effective 9:00-11:00 AM\n"
        result += "• Avoid scheduling right before lunch or late afternoon\n"
        result += "• Creative work peaks around 10:00 AM-12:00 PM\n\n"
        result += "Would you like me to create an event for any of these times?"
        
        return result
        
    except Exception as e:
        return f"Error finding optimal times: {str(e)}"


def calculate_productivity_score(datetime_obj, activity_type, weekday):
    """Calculate productivity score based on time and activity type."""
    hour = datetime_obj.hour
    score = 5  # Base score
    
    # Time-based scoring
    if 9 <= hour <= 11:
        score += 3  # Peak morning hours
    elif 14 <= hour <= 16:
        score += 2  # Good afternoon hours
    elif 10 <= hour <= 11:
        score += 1  # Excellent meeting time
    elif hour < 9 or hour > 17:
        score -= 2  # Outside work hours
    
    # Activity-specific scoring
    if activity_type.lower() in ['meeting', 'họp']:
        if 10 <= hour <= 11 or 13 <= hour <= 15:
            score += 2  # Optimal meeting times
    elif activity_type.lower() in ['focus work', 'coding']:
        if 9 <= hour <= 11:
            score += 3  # Peak focus time
    elif activity_type.lower() in ['creative work']:
        if 10 <= hour <= 12:
            score += 2  # Creative peak time
    
    # Weekday bonus
    if 0 <= weekday <= 4:  # Monday to Friday
        score += 1
    
    return min(10, max(1, score))  # Clamp between 1-10


def get_productivity_reasoning(datetime_obj, activity_type):
    """Get human-readable reasoning for why a time is optimal."""
    hour = datetime_obj.hour
    day_name = datetime_obj.strftime('%A')
    
    if activity_type.lower() in ['meeting', 'họp']:
        if 10 <= hour <= 11:
            return "Peak meeting time - everyone is alert and focused"
        elif 13 <= hour <= 15:
            return "Good afternoon meeting time - after lunch energy boost"
        else:
            return "Decent time for meetings, though not optimal"
    
    elif activity_type.lower() in ['focus work', 'coding']:
        if 9 <= hour <= 11:
            return "Peak cognitive performance - ideal for deep work"
        elif 14 <= hour <= 16:
            return "Good focus time - afternoon productivity peak"
        else:
            return "Decent time for focused work"
    
    elif activity_type.lower() in ['creative work']:
        if 10 <= hour <= 12:
            return "Creative peak time - when imagination is most active"
        elif 15 <= hour <= 17:
            return "Good creative time - afternoon inspiration"
        else:
            return "Decent time for creative work"
    
    else:
        if 9 <= hour <= 11:
            return "Peak productivity hours - optimal for most tasks"
        elif 14 <= hour <= 16:
            return "Good productivity time - afternoon energy"
        else:
            return "Decent time for work tasks"


@mcp.tool()
async def delete_event(event_id: str) -> str:
    """Delete a calendar event.
    
    Args:
        event_id: The ID of the event to delete
    """
    try:
        service = get_calendar_service()
        
        # Get event details before deleting
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        event_summary = event.get('summary', 'Unknown Event')
        
        # Delete the event
        service.events().delete(
            calendarId='primary',
            eventId=event_id,
            sendUpdates='all'
        ).execute()
        
        return f"Event '{event_summary}' (ID: {event_id}) deleted successfully!"
        
    except Exception as e:
        return f"Error deleting event: {str(e)}"


@mcp.tool()
async def move_event(
    event_id: str,
    new_start_datetime: str,
    new_end_datetime: str
) -> str:
    """Move an event to a new date/time.
    
    Args:
        event_id: The ID of the event to move
        new_start_datetime: New start date and time in ISO format (e.g., '2025-10-21T10:00:00')
        new_end_datetime: New end date and time in ISO format (e.g., '2025-10-21T11:00:00')
    """
    try:
        service = get_calendar_service()
        
        # Get the existing event
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        
        # Update the time
        event['start'] = {'dateTime': new_start_datetime, 'timeZone': TIMEZONE}
        event['end'] = {'dateTime': new_end_datetime, 'timeZone': TIMEZONE}
        
        # Update the event
        moved_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event,
            sendUpdates='all'
        ).execute()
        
        return f"Event moved successfully!\n{format_event(moved_event)}"
        
    except Exception as e:
        return f"Error moving event: {str(e)}"


@mcp.tool()
async def get_event_by_id(event_id: str) -> str:
    """Get detailed information about a specific event.
    
    Args:
        event_id: The ID of the event to retrieve
    """
    try:
        service = get_calendar_service()
        
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        
        return format_event(event)
        
    except Exception as e:
        return f"Error fetching event: {str(e)}"


def main():
    # Initialize and run the server
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()