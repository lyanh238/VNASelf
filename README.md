# VNASelf - Multi-Agent Personal Assistant

<p align="center">
  <img src="change/qai_gen.png" alt="VNASelf Logo" width="200" height="200"/>
</p>

A sophisticated multi-agent system for personal finance management and Google Calendar integration, featuring both web interface and command-line access.

## Features

### Finance Management
- **Expense Tracking**: Add, view, and manage your spending history
- **Category Management**: Organize expenses by Food, Transportation, and Miscellaneous
- **Spending Analysis**: Calculate total spending and view expense history
- **Date-based Filtering**: Filter expenses by date ranges
- **Vietnamese Language Support**: Full support for Vietnamese queries

### Calendar Management
- **Event Creation**: Schedule appointments and meetings with conflict detection
- **Event Management**: Update, delete, and move calendar events
- **Availability Check**: Check free/busy times
- **Event Search**: Find events by keywords or dates
- **Upcoming Events**: View scheduled appointments
- **Conflict Resolution**: Intelligent handling of scheduling conflicts

### Multi-Agent Architecture
- **Intelligent Routing**: Automatic routing to appropriate specialized agents
- **Agent Detection**: Clear indication of which agent processed your request
- **Conversation Memory**: Maintains context across interactions
- **Real-time Processing**: Fast response times with async processing
- **Error Handling**: Robust error handling and user feedback

## Architecture

```
VNASelf Application
├── Web Interface (Streamlit)
│   ├── User Input Processing
│   ├── Real-time Chat Interface
│   └── State Management
├── Multi-Agent System
│   ├── Supervisor Agent (Intelligent Routing)
│   ├── Finance Agent (Expense Management)
│   └── Calendar Agent (Google Calendar Integration)
└── Services
    ├── MCP Service (Model Context Protocol)
    ├── Payment History Service (Database)
    └── State Manager (Conversation Memory)
```

## Prerequisites

- Python 3.11+
- OpenAI API Key
- Google Calendar API credentials (for calendar features)
- NeonDB connection (for finance data storage)
- Internet connection

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd calendar-mcp-server
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables
```bash
# Required
export OPENAI_API_KEY="your-openai-api-key"

# Optional (for calendar features)
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"

# Optional (for finance data storage)
export NEON_DATABASE_URL="your-neon-database-url"
```

### 4. Google Calendar Setup (Optional)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Calendar API
4. Create credentials (Service Account)
5. Download the JSON key file
6. Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable

## Usage

### Web Interface (Recommended)
```bash
streamlit run app.py
```
Then open your browser to `http://localhost:8501`

### Command Line Interface
```bash
python main.py
```

### Example Interactions

#### Finance Management
```
User: "Thêm chi tiêu: Ăn trưa tại nhà hàng, 150000 VND, Food, 2024-01-15"
Assistant: [Finance Agent] Chi tiêu đã được thêm thành công...

User: "Xem lịch sử chi tiêu của tôi"
Assistant: [Finance Agent] Dưới đây là lịch sử chi tiêu của bạn...

User: "Tính tổng chi tiêu trong tháng này"
Assistant: [Finance Agent] Tổng chi tiêu trong tháng này là 580,000 VND
```

#### Calendar Management
```
User: "Xem lịch sắp tới"
Assistant: [Calendar Agent] Dưới đây là lịch sắp tới của bạn...

User: "Tạo cuộc họp lúc 15:00 hôm nay"
Assistant: [Calendar Agent] Cuộc họp đã được tạo thành công...
```

## Project Structure

```
calendar-mcp-server/
├── app.py                 # Streamlit web interface
├── main.py               # Command-line interface
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── agents/               # Agent implementations
│   ├── base_agent.py
│   ├── finance_agent.py
│   ├── calendar_agent.py
│   └── supervisor_agent.py
├── core/                 # Core system components
│   ├── multi_agent_system.py
│   └── state_manager.py
├── services/             # External services
│   ├── mcp_service.py
│   ├── payment_history_service.py
│   └── chat_history_service.py
├── models/               # Database models
│   ├── chat_history.py
│   └── payment_history.py
└── docs/                 # Documentation
    ├── API.md
    ├── SETUP.md
    ├── USAGE.md
    └── FINANCE_AGENT.md
```

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to Google service account JSON (optional)
- `NEON_DATABASE_URL`: NeonDB connection string (optional)
- `OPENAI_MODEL`: OpenAI model to use (default: gpt-4o-mini)

### Model Settings
The system uses GPT-4o-mini by default for optimal performance and cost. You can change this in `config.py` or by setting the `OPENAI_MODEL` environment variable.

## Testing

### Run Examples
```bash
python main.py
# Choose option 1 to run example demonstrations
```

### Test Individual Components
```bash
python test_agent_detection.py
```

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**
   ```
   Error: OPENAI_API_KEY environment variable not set
   ```
   **Solution**: Set your OpenAI API key as an environment variable

2. **Google Calendar Access Error**
   ```
   Error: Google Calendar API not accessible
   ```
   **Solution**: Check your Google Calendar API credentials and permissions

3. **Database Connection Error**
   ```
   Error: NEON_DATABASE_URL not set
   ```
   **Solution**: Set your NeonDB connection string or the system will work without database features

4. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'langgraph'
   ```
   **Solution**: Install all dependencies with `pip install -r requirements.txt`

### Getting Help

1. Check the [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
2. Review the [API Documentation](docs/API.md)
3. Check the [Setup Guide](docs/SETUP.md) for detailed installation steps
4. Read the [Finance Agent Guide](docs/FINANCE_AGENT.md) for finance features

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for the GPT models
- Google for the Calendar API
- Streamlit for the web interface framework
- LangGraph for the multi-agent orchestration
- NeonDB for database services

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation in the `docs/` folder
- Review the troubleshooting guide

---

**Made with love for better personal management**