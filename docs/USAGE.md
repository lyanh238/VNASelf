# NekHealth Usage Guide

This guide provides comprehensive instructions on how to use the NekHealth multi-agent system effectively.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Web Interface](#web-interface)
3. [Command Line Interface](#command-line-interface)
4. [Health Consultation](#health-consultation)
5. [Calendar Management](#calendar-management)
6. [Advanced Features](#advanced-features)
7. [Best Practices](#best-practices)
8. [Examples](#examples)

## Getting Started

### Launching the Application

#### Web Interface (Recommended)
```bash
streamlit run app.py
```
Open your browser to `http://localhost:8501`

#### Command Line Interface
```bash
python main.py
```

### First Interaction

When you first open the application, you'll see:

1. **Welcome Screen**: With example suggestions
2. **Chat Input**: Where you can type your questions
3. **Suggestion Buttons**: Quick access to common tasks

## Web Interface

### Interface Overview

The web interface provides a clean, chat-based experience:

- **Header**: NekHealth logo and restart button
- **Chat Area**: Conversation history
- **Input Field**: Type your questions here
- **Suggestions**: Quick action buttons

### Navigation

#### Starting a New Conversation
1. Click the "Restart" button (🔄) in the top right
2. Or refresh the page
3. This clears conversation history and starts fresh

#### Using Suggestions
Click any suggestion button to quickly start with common tasks:
- "Đặt lịch khám bệnh" (Schedule medical appointment)
- "Kiểm tra lịch trống" (Check available times)
- "Hủy lịch hẹn" (Cancel appointment)
- "Cập nhật lịch hẹn" (Update appointment)
- "Tư vấn sức khỏe" (Health consultation)
- "Theo dõi huyết áp" (Blood pressure tracking)

### Chat Features

#### Real-time Processing
- Messages are processed in real-time
- "Meowing..." spinner shows when AI is thinking
- Responses appear immediately when ready

#### Conversation Memory
- The system remembers your conversation history
- Context is maintained across multiple exchanges
- Previous questions and answers influence future responses

## Command Line Interface

### Interactive Mode

When you run `python main.py`, you'll see:

```
Choose mode:
1. Run example demonstrations
2. Interactive chat
```

#### Option 1: Examples
Runs predefined examples to demonstrate functionality:
- Health consultation example
- Calendar viewing example
- Event creation example
- Event search example

#### Option 2: Interactive Chat
Starts a command-line chat session:

```
============================================================
Multi-Agent System (Health + Calendar)
============================================================
Special commands:
  - 'exit' or 'quit': Exit
  - 'clear': Clear chat history
============================================================

You: I have a headache
Processing...

Assistant: Based on your headache symptoms, here are some recommendations...
```

### Special Commands

- `exit` or `quit`: Exit the application
- `clear`: Clear chat history and start fresh
- `thoát`: Vietnamese version of exit

## Health Consultation

### Types of Health Queries

#### Symptom Analysis
```
"I have a headache and fever"
"My stomach hurts after eating"
"I feel dizzy when I stand up"
```

#### General Health Questions
```
"What should I eat for better health?"
"How much water should I drink daily?"
"What exercises are good for back pain?"
```

#### Medical Advice
```
"I have diabetes, what should I avoid?"
"I'm pregnant, what supplements should I take?"
"My child has a fever, when should I worry?"
```

### Health Response Features

- **Symptom Analysis**: AI analyzes your symptoms
- **Recommendations**: Personalized health advice
- **Warning Signs**: When to seek immediate medical attention
- **Lifestyle Tips**: Diet, exercise, and wellness suggestions
- **Follow-up Questions**: AI may ask clarifying questions

### Example Health Interaction

```
User: I have a headache and mild fever, what should I do?

Assistant: Based on your symptoms of headache and mild fever, here are some recommendations:

1. **Immediate Care**:
   - Rest in a cool, dark room
   - Stay hydrated with water or clear fluids
   - Take over-the-counter pain relievers (if not allergic)

2. **Monitor Symptoms**:
   - Check temperature regularly
   - Watch for worsening symptoms
   - Note any additional symptoms

3. **When to Seek Medical Attention**:
   - Fever above 101.3°F (38.5°C)
   - Severe headache with neck stiffness
   - Confusion or difficulty speaking
   - Rash or difficulty breathing

4. **General Advice**:
   - Get plenty of rest
   - Avoid screens and bright lights
   - Eat light, easy-to-digest foods

If symptoms worsen or persist beyond 2-3 days, please consult a healthcare professional.
```

## Calendar Management

### Calendar Operations

#### Viewing Events
```
"Show me my upcoming appointments"
"What's on my calendar today?"
"List my events for this week"
```

#### Creating Events
```
"Create a doctor appointment for tomorrow at 2 PM"
"Schedule a meeting with John on Friday at 10 AM"
"Add a reminder for my medication at 8 AM daily"
```

#### Managing Events
```
"Cancel my 3 PM appointment"
"Move my meeting to 4 PM"
"Update my doctor appointment to next Tuesday"
```

#### Searching Events
```
"Find all my doctor appointments"
"Show me meetings with 'project' in the title"
"When is my next dental checkup?"
```

### Date and Time Formats

The system understands various date/time formats:

#### Natural Language
- "tomorrow", "next week", "next Monday"
- "in 2 hours", "at 3 PM", "this afternoon"
- "next month", "in 2 days"

#### Specific Formats
- Dates: "2025-10-25", "October 25, 2025"
- Times: "2:00 PM", "14:00", "2 PM"
- Combined: "2025-10-25 14:00"

### Calendar Response Examples

#### Viewing Events
```
User: Show me my upcoming appointments

Assistant: Here are your upcoming events:

📅 **Today (October 20, 2025)**
- 10:00 AM - Team Meeting (1 hour)
- 2:00 PM - Doctor Appointment (30 minutes)

📅 **Tomorrow (October 21, 2025)**
- 9:00 AM - Project Review (2 hours)
- 3:30 PM - Dentist Checkup (1 hour)

📅 **This Week**
- Wednesday: 11:00 AM - Client Call
- Friday: 1:00 PM - Lunch Meeting
```

#### Creating Events
```
User: Create a doctor appointment for tomorrow at 2 PM

Assistant: I'll create a doctor appointment for tomorrow at 2 PM.

✅ **Event Created Successfully**
- **Title**: Doctor Appointment
- **Date**: October 21, 2025
- **Time**: 2:00 PM - 3:00 PM
- **Event ID**: abc123def456

The appointment has been added to your calendar. You'll receive a reminder 15 minutes before the appointment.
```

## Advanced Features

### Multi-Agent Routing

The system automatically routes your requests to the appropriate agent:

- **Health-related queries** → Health Agent
- **Calendar-related queries** → Calendar Agent
- **Mixed queries** → Supervisor Agent coordinates both

### Conversation Context

The system maintains context across interactions:

```
User: I have a headache
Assistant: [Provides headache advice]

User: Should I schedule a doctor appointment?
Assistant: Based on your headache symptoms, I recommend scheduling an appointment if...
```

### Error Handling

The system provides helpful error messages:

```
User: Create an event yesterday at 2 PM
Assistant: I can't create events in the past. Would you like to schedule this for today or tomorrow instead?
```

### Timezone Handling

All times are handled in Asia/Ho_Chi_Minh timezone (GMT+7):

- Times are automatically converted
- Date calculations respect timezone
- Event times are displayed in local timezone

## Best Practices

### For Health Queries

1. **Be Specific**: Provide detailed symptom descriptions
2. **Include Context**: Mention duration, severity, triggers
3. **Ask Follow-ups**: Don't hesitate to ask clarifying questions
4. **Seek Professional Help**: For serious symptoms, consult healthcare providers

### For Calendar Management

1. **Use Clear Dates**: Specify exact dates when possible
2. **Include Duration**: Mention how long events should last
3. **Add Descriptions**: Provide context for events
4. **Check Availability**: Verify times before creating events

### General Tips

1. **Be Natural**: Use conversational language
2. **Ask Questions**: The AI can help clarify your needs
3. **Use Suggestions**: Click suggestion buttons for quick actions
4. **Restart When Needed**: Use restart button for new topics

## Examples

### Complete Health Consultation

```
User: I've been having headaches for the past week, usually in the afternoon. They're not severe but persistent.

Assistant: I understand you've been experiencing persistent afternoon headaches for a week. Let me help you with this.

**Questions to better understand your situation:**
1. Do the headaches occur at the same time each day?
2. Are they associated with any triggers (stress, screen time, hunger)?
3. Have you noticed any changes in your sleep or stress levels recently?

**General recommendations for persistent headaches:**
- Maintain regular sleep schedule
- Stay hydrated throughout the day
- Take breaks from screens every hour
- Consider stress management techniques

**When to seek medical attention:**
- If headaches worsen or change pattern
- If you experience vision changes or nausea
- If headaches interfere with daily activities

Would you like me to help you schedule a doctor appointment to discuss these headaches?
```

### Complete Calendar Management

```
User: I need to schedule a series of follow-up appointments for my treatment.

Assistant: I'd be happy to help you schedule your follow-up appointments. Let me first check your current schedule to find available times.

**Current upcoming appointments:**
- October 22: 10:00 AM - Initial Consultation
- October 25: 2:00 PM - Lab Work

**Questions to help schedule your follow-ups:**
1. How many follow-up appointments do you need?
2. What's the recommended interval between appointments?
3. Do you have any time preferences (morning, afternoon, specific days)?
4. How long should each appointment be?

**Suggested scheduling approach:**
- Week 1: First follow-up (1 week after initial)
- Week 2: Second follow-up (2 weeks after initial)
- Month 1: Monthly check-in
- Month 3: 3-month review

Would you like me to create these appointments based on your initial consultation date?
```

### Mixed Health and Calendar Query

```
User: I have a doctor appointment tomorrow, but I'm feeling worse today. Should I go or reschedule?

Assistant: I understand you're feeling worse today and have a doctor appointment tomorrow. Let me help you decide.

**Health Assessment:**
Since you're feeling worse, it's important to consider:
- Are your symptoms getting significantly worse?
- Do you have any emergency symptoms (severe pain, difficulty breathing, high fever)?
- Can you wait until tomorrow, or do you need immediate attention?

**Appointment Options:**
1. **Keep tomorrow's appointment** if symptoms are manageable
2. **Reschedule to today** if you need earlier attention
3. **Seek immediate care** if symptoms are severe

**Current appointment details:**
- Date: Tomorrow at 2:00 PM
- Duration: 30 minutes
- Doctor: Dr. Smith

Would you like me to:
1. Help you find an earlier appointment today?
2. Keep your current appointment?
3. Help you identify if you need immediate medical attention?

What are your current symptoms, and how do they compare to when you scheduled the appointment?
```

## Troubleshooting Usage Issues

### Common Problems

#### Slow Responses
- Check your internet connection
- The AI may be processing complex requests
- Try breaking down complex questions

#### Incorrect Understanding
- Be more specific in your requests
- Use the restart button to clear context
- Try rephrasing your question

#### Calendar Access Issues
- Verify Google Calendar permissions
- Check if the calendar is shared with the service account
- Ensure you're using the correct calendar

### Getting Help

1. Use the restart button to clear any issues
2. Try the suggestion buttons for common tasks
3. Be specific about what you need help with
4. Check the troubleshooting guide for technical issues
