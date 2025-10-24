# VNASelf API Documentation

## Overview

VNASelf provides a multi-agent system for calendar management with both programmatic and web interfaces. This document covers the API structure, agent interactions, and integration methods.

## Core Components

### MultiAgentSystem

The main orchestrator that manages all agents and handles user requests.

```python
from core import MultiAgentSystem

# Initialize the system
system = MultiAgentSystem()
await system.initialize()

# Process a message
response = await system.process_message("I have a headache")
```

#### Methods

##### `initialize()`
Initializes the multi-agent system, MCP service, and all agents.

**Returns**: `None`

**Example**:
```python
await system.initialize()
```

##### `process_message(message: str, thread_id: Optional[str] = None)`
Processes a user message through the multi-agent system.

**Parameters**:
- `message` (str): User input message
- `thread_id` (Optional[str]): Conversation thread ID

**Returns**: `str` - Agent response

**Example**:
```python
response = await system.process_message("Show me my upcoming events")
```

##### `chat_interactive()`
Starts an interactive command-line chat session.

**Returns**: `None`

**Example**:
```python
await system.chat_interactive()
```

##### `run_examples()`
Runs predefined example queries to demonstrate functionality.

**Returns**: `None`

**Example**:
```python
await system.run_examples()
```

##### `close()`
Closes the system and cleans up resources.

**Returns**: `None`

**Example**:
```python
await system.close()
```

## Agents

### SupervisorAgent

Routes user requests to appropriate specialized agents.

#### Tools Available

The supervisor agent has access to all tools from calendar agents:

**Calendar Tools**:
- `list_upcoming_events`: Lists upcoming calendar events
- `get_events_for_date`: Gets events for a specific date
- `search_events`: Searches events by keywords
- `create_event`: Creates new calendar events
- `update_event`: Updates existing events
- `delete_event`: Deletes events
- `move_event`: Moves events to different times
- `get_event_by_id`: Gets event details by ID
- `check_availability`: Checks calendar availability

### CalendarAgent

Manages Google Calendar integration through MCP service.

#### Tools

##### `list_upcoming_events`
Lists upcoming calendar events.

**Parameters**:
- `max_results` (int): Maximum number of events to return (default: 10)

**Returns**: `str` - Formatted list of upcoming events

##### `get_events_for_date`
Gets events for a specific date.

**Parameters**:
- `date` (str): Date in YYYY-MM-DD format

**Returns**: `str` - Events for the specified date

##### `search_events`
Searches events by keywords.

**Parameters**:
- `query` (str): Search keywords
- `max_results` (int): Maximum results to return

**Returns**: `str` - Matching events

##### `create_event`
Creates a new calendar event (legacy function).

**Parameters**:
- `title` (str): Event title
- `start_time` (str): Start time in ISO format (YYYY-MM-DDTHH:MM:SS)
- `end_time` (str): End time in ISO format
- `description` (str, optional): Event description

**Returns**: `str` - Confirmation of event creation

##### `create_event_with_conflict_check`
Creates a new calendar event with conflict detection.

**Parameters**:
- `title` (str): Event title
- `start_time` (str): Start time in ISO format
- `end_time` (str): End time in ISO format
- `description` (str, optional): Event description
- `force_create` (bool, optional): Force creation even with conflicts

**Returns**: `str` - Confirmation of event creation or conflict information

##### `check_conflicts`
Checks for scheduling conflicts in a time range.

**Parameters**:
- `start_time` (str): Start time in ISO format
- `end_time` (str): End time in ISO format

**Returns**: `str` - Information about conflicting events or confirmation of no conflicts

##### `suggest_alternative_times`
Suggests alternative time slots when conflicts are detected.

**Parameters**:
- `start_time` (str): Original start time in ISO format
- `end_time` (str): Original end time in ISO format
- `duration_minutes` (int, optional): Duration in minutes (default: 60)
- `days_ahead` (int, optional): Days to look ahead (default: 7)

**Returns**: `str` - List of suggested alternative time slots

##### `resolve_conflict_by_moving_existing`
Moves an existing conflicting event to a new time slot.

**Parameters**:
- `existing_event_id` (str): ID of the existing event to move
- `new_start_time` (str): New start time in ISO format
- `new_end_time` (str): New end time in ISO format

**Returns**: `str` - Confirmation of the move operation

##### `resolve_conflict_by_deleting_existing`
Deletes an existing conflicting event to resolve conflict.

**Parameters**:
- `existing_event_id` (str): ID of the existing event to delete

**Returns**: `str` - Confirmation of the deletion

##### `update_event`
Updates an existing event.

**Parameters**:
- `event_id` (str): Event ID to update
- `title` (str, optional): New title
- `start_time` (str, optional): New start time
- `end_time` (str, optional): New end time
- `description` (str, optional): New description

**Returns**: `str` - Confirmation of update

##### `delete_event`
Deletes an event.

**Parameters**:
- `event_id` (str): Event ID to delete

**Returns**: `str` - Confirmation of deletion

##### `move_event`
Moves an event to a different time.

**Parameters**:
- `event_id` (str): Event ID to move
- `new_start_time` (str): New start time in ISO format
- `new_end_time` (str): New end time in ISO format

**Returns**: `str` - Confirmation of move

##### `get_event_by_id`
Gets detailed information about a specific event.

**Parameters**:
- `event_id` (str): Event ID

**Returns**: `str` - Event details

##### `check_availability`
Checks calendar availability for a time range.

**Parameters**:
- `start_time` (str): Start time in ISO format
- `end_time` (str): End time in ISO format

**Returns**: `str` - Availability status

## State Management

### StateManager

Manages conversation state and memory.

#### Methods

##### `get_config()`
Gets the current configuration for the agent system.

**Returns**: `Dict[str, Any]` - Configuration with thread ID

##### `create_new_thread()`
Creates a new conversation thread.

**Returns**: `str` - New thread ID

##### `get_memory()`
Gets the memory saver instance.

**Returns**: `MemorySaver` - LangGraph memory instance

## Web Interface API

### Streamlit Integration

The web interface provides a REST-like API through Streamlit's session state.

#### Session State Variables

- `messages`: List of conversation messages
- `initial_question`: Initial user question
- `multi_agent_system`: MultiAgentSystem instance

#### Functions

##### `send_to_agent(user_input: str)`
Synchronous wrapper for async multi-agent calls.

**Parameters**:
- `user_input` (str): User input message

**Returns**: `str` - Agent response

##### `clear_conversation()`
Clears conversation history and resets the multi-agent system.

**Returns**: `None`

## Error Handling

### Common Error Types

1. **Initialization Errors**
   - Missing OpenAI API key
   - Google Calendar API access issues
   - MCP service connection problems

2. **Processing Errors**
   - Invalid date formats
   - Missing required parameters
   - API rate limiting

3. **State Errors**
   - Thread ID conflicts
   - Memory access issues

### Error Response Format

```python
{
    "error": "Error type",
    "message": "Human-readable error message",
    "details": "Technical details (optional)"
}
```

## Integration Examples

### Basic Integration

```python
import asyncio
from core import MultiAgentSystem

async def main():
    system = MultiAgentSystem()
    await system.initialize()
    
    response = await system.process_message("Show me my calendar for today")
    print(response)
    
    await system.close()

asyncio.run(main())
```

### Custom Thread Management

```python
async def process_with_thread(user_input, thread_id):
    system = MultiAgentSystem()
    await system.initialize()
    
    response = await system.process_message(user_input, thread_id)
    return response
```

### Health Consultation Only

```python
from agents import HealthAgent
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o-mini")
health_agent = HealthAgent(model)

# Use health consultation tool directly
response = health_agent.health_consultation_tool(
    symptoms="headache and fever",
    question="What should I do?"
)
```

## Rate Limits and Best Practices

### Rate Limits
- OpenAI API: Follow OpenAI's rate limits
- Google Calendar API: 1,000,000 queries per day per project

### Best Practices
1. Always initialize the system before use
2. Use appropriate thread IDs for conversation continuity
3. Handle errors gracefully
4. Close the system when done
5. Use specific date formats (YYYY-MM-DD, ISO datetime)

## Security Considerations

1. **API Keys**: Store securely, never commit to version control
2. **Google Credentials**: Use service accounts with minimal permissions
3. **User Data**: Conversation history is stored in memory only
4. **Input Validation**: All inputs are validated before processing

## Performance Optimization

1. **Async Operations**: Use async/await for better performance
2. **Connection Pooling**: MCP service maintains connection pools
3. **Memory Management**: Regular cleanup of conversation threads
4. **Caching**: Tool results are cached when appropriate
