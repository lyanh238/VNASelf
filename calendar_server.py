from typing import Any
from datetime import datetime, timedelta
import os
from mcp.server.fastmcp import FastMCP
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import pytz
mcp = FastMCP("google_calendar")

# If modifying these scopes, delete the token.pickle file
SCOPES = ['https://www.googleapis.com/auth/calendar']

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
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError(
                    "credentials.json not found. Please download it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
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
async def create_event(
    summary: str,
    start_datetime: str,
    end_datetime: str,
    description: str = "",
    location: str = "",
    attendees: str = ""
) -> str:
    """Create a new calendar event.
    
    Args:
        summary: Event title/summary
        start_datetime: Start date and time in ISO format (e.g., '2025-10-20T10:00:00')
        end_datetime: End date and time in ISO format (e.g., '2025-10-20T11:00:00')
        description: Event description (optional)
        location: Event location (optional)
        attendees: Comma-separated email addresses of attendees (optional)
    """
    try:
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
        
        return f"Event created successfully!\n{format_event(created_event)}"
        
    except Exception as e:
        return f"Error creating event: {str(e)}"


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