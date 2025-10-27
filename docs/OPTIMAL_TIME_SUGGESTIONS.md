# Optimal Time Suggestions Feature

## Overview

The system now includes intelligent time suggestion capabilities based on productivity research. When users ask for suitable times to schedule activities, the agent can suggest optimal time slots and automatically create calendar events when users agree.

## Key Features

### 🎯 Productivity-Based Time Suggestions
- **Meeting Times**: 10:00-11:30 AM or 1:30-3:00 PM (peak focus and engagement)
- **Focus Work**: 9:00-11:00 AM (peak cognitive performance)
- **Creative Work**: 10:00-12:00 PM (when creativity peaks)
- **Administrative Tasks**: 9:00-10:00 AM or 4:00-5:00 PM (routine work times)

### 🧠 Smart Activity Recognition
The system recognizes various activity types in both English and Vietnamese:
- `meeting`, `họp`, `cuộc họp`, `team meeting`, `client meeting`
- `focus work`, `deep work`, `coding`, `writing`, `analysis`
- `creative work`, `brainstorming`, `planning`, `design`
- `admin`, `email`, `routine`, `administrative`

### ⭐ Productivity Scoring
Each suggested time slot includes:
- **Productivity Score** (1-10): Based on time of day and activity type
- **Reasoning**: Human-readable explanation of why the time is optimal
- **Availability Check**: Automatically verifies no conflicts exist

## Usage Examples

### Basic Time Suggestion
```
User: "I need to schedule a team meeting for 1 hour"
Agent: Uses suggest_optimal_time with activity_type="meeting", duration_minutes=60
```

### Specific Date Request
```
User: "What's the best time for creative work tomorrow?"
Agent: Uses suggest_optimal_time with activity_type="creative work", preferred_date="2025-01-15"
```

### Automatic Event Creation
```
User: "Suggest a good time for focus work and create the event"
Agent: 1. Uses suggest_optimal_time to find optimal slots
       2. Presents suggestions with productivity scores
       3. Asks user to confirm
       4. Uses create_event_with_conflict_check to create the event
```

## System Integration

### New Tool: `suggest_optimal_time`
- **Location**: `backend/server/calendar_server.py`
- **Parameters**:
  - `activity_type`: Type of activity (required)
  - `duration_minutes`: Duration in minutes (default: 60)
  - `preferred_date`: Specific date in YYYY-MM-DD format (optional)
  - `days_ahead`: Search window in days (default: 7)

### Updated Agent Prompts
- **Supervisor Agent**: Added optimal time suggestion workflow
- **Calendar Agent**: Added tool documentation and usage guidelines

## Productivity Research Basis

The time suggestions are based on established productivity research:

1. **Peak Cognitive Performance**: 9:00-11:00 AM
   - Highest alertness and focus
   - Best for complex, analytical tasks

2. **Optimal Meeting Times**: 10:00-11:30 AM or 1:30-3:00 PM
   - Avoids pre-lunch energy dip
   - Avoids late afternoon fatigue
   - Ensures maximum engagement

3. **Creative Peak**: 10:00 AM-12:00 PM
   - When imagination and creativity are highest
   - Ideal for brainstorming and design work

4. **Administrative Windows**: 9:00-10:00 AM or 4:00-5:00 PM
   - Good for routine, low-cognitive tasks
   - Doesn't interfere with peak performance periods

## Workflow

1. **User Request**: User asks for suitable time for an activity
2. **Activity Analysis**: System identifies activity type and requirements
3. **Time Search**: System searches for optimal time slots based on productivity research
4. **Conflict Check**: System verifies availability and checks for conflicts
5. **Scoring**: Each available slot gets a productivity score (1-10)
6. **Presentation**: System presents ranked suggestions with reasoning
7. **User Choice**: User selects preferred time slot
8. **Event Creation**: System creates calendar event using `create_event_with_conflict_check`

## Error Handling

- **No Available Slots**: Suggests extending search period or changing duration
- **Invalid Date Format**: Provides clear error message with correct format
- **API Errors**: Graceful fallback with helpful error messages
- **Authentication Issues**: Clear instructions for credential setup

## Future Enhancements

- **Personal Preferences**: Learn from user's scheduling patterns
- **Team Availability**: Consider team members' calendars
- **Time Zone Support**: Handle multiple time zones for remote teams
- **Recurring Events**: Suggest optimal patterns for recurring activities
- **Energy Levels**: Factor in individual energy patterns

## Testing

Run the test script to verify functionality:
```bash
python test_optimal_time.py
```

This will test various activity types and show sample suggestions (requires Google Calendar API setup).
