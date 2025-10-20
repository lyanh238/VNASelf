# NekHealth - Integrated Multi-Agent System

This application integrates a Streamlit web interface with a multi-agent system for health consultation and calendar management.

## Features

- **Health Consultation**: AI-powered health advice and symptom analysis
- **Calendar Management**: Google Calendar integration for appointment scheduling
- **Multi-Agent System**: Intelligent routing between health and calendar agents
- **Web Interface**: User-friendly Streamlit interface

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

3. **Google Calendar Setup** (for calendar features):
   - Follow the Google Calendar API setup instructions
   - Place your credentials file in the project directory

## Running the Application

### Option 1: Using the startup script
```bash
python run_app.py
```

### Option 2: Direct Streamlit command
```bash
streamlit run app.py
```

### Option 3: Command line interface (original)
```bash
python main.py
```

## Usage

1. **Web Interface**: Open your browser to `http://localhost:8501`
2. **Health Queries**: Ask about symptoms, health advice, or medical concerns
3. **Calendar Operations**: 
   - View upcoming events
   - Create new appointments
   - Search for specific events
   - Update or delete existing events

## Architecture

- **app.py**: Streamlit web interface
- **main.py**: Command-line interface
- **core/multi_agent_system.py**: Main orchestrator
- **agents/**: Specialized agents (health, calendar, supervisor)
- **services/**: MCP service for Google Calendar integration

## Key Changes Made

1. **Integrated Multi-Agent System**: Replaced webhook communication with direct multi-agent system calls
2. **Async Support**: Added proper async/await handling for Streamlit
3. **State Management**: Integrated conversation state with multi-agent memory
4. **Error Handling**: Improved error handling and user feedback

## Troubleshooting

- Ensure `OPENAI_API_KEY` is set
- Check Google Calendar API credentials if using calendar features
- Verify all dependencies are installed correctly
- Check console output for detailed error messages
