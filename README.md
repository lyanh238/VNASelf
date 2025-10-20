# NekHealth - Multi-Agent Health & Calendar Assistant

![NekHealth Logo](https://www.creativefabrica.com/wp-content/uploads/2023/06/19/Cute-Adorable-Little-Doctor-Kitten-With-Chibi-Dreamy-Eyes-Wearing-72527736-1.png)

A sophisticated multi-agent system that combines AI-powered health consultation with Google Calendar integration, featuring both web interface and command-line access.

## 🚀 Features

### Health Consultation
- **Symptom Analysis**: AI-powered analysis of health symptoms
- **Health Advice**: Personalized health recommendations
- **Medical Guidance**: General medical information and guidance
- **Wellness Tips**: Diet, exercise, and lifestyle recommendations

### Calendar Management
- **Event Creation**: Schedule appointments and meetings
- **Event Management**: Update, delete, and move calendar events
- **Availability Check**: Check free/busy times
- **Event Search**: Find events by keywords or dates
- **Upcoming Events**: View scheduled appointments

### Multi-Agent Architecture
- **Intelligent Routing**: Automatic routing to appropriate specialized agents
- **Conversation Memory**: Maintains context across interactions
- **Real-time Processing**: Fast response times with async processing
- **Error Handling**: Robust error handling and user feedback

## 🏗️ Architecture

```
NekHealth Application
├── Web Interface (Streamlit)
│   ├── User Input Processing
│   ├── Real-time Chat Interface
│   └── State Management
├── Multi-Agent System
│   ├── Supervisor Agent (Routing)
│   ├── Health Agent (Medical Consultation)
│   └── Calendar Agent (Google Calendar Integration)
└── Services
    ├── MCP Service (Model Context Protocol)
    └── State Manager (Conversation Memory)
```

## 📋 Prerequisites

- Python 3.11+
- OpenAI API Key
- Google Calendar API credentials (for calendar features)
- Internet connection

## 🛠️ Installation

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
```

### 4. Google Calendar Setup (Optional)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Calendar API
4. Create credentials (Service Account)
5. Download the JSON key file
6. Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable

## 🚀 Usage

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

#### Health Consultation
```
User: "I have a headache and mild fever, what should I do?"
Assistant: "Based on your symptoms of headache and mild fever, here are some recommendations..."
```

#### Calendar Management
```
User: "Show me my upcoming appointments"
Assistant: "Here are your upcoming events: [lists events]"

User: "Create a doctor appointment for tomorrow at 2 PM"
Assistant: "I'll create a doctor appointment for tomorrow at 2 PM..."
```

## 📁 Project Structure

```
calendar-mcp-server/
├── app.py                 # Streamlit web interface
├── main.py               # Command-line interface
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── agents/               # Agent implementations
│   ├── base_agent.py
│   ├── health_agent.py
│   ├── calendar_agent.py
│   └── supervisor_agent.py
├── core/                 # Core system components
│   ├── multi_agent_system.py
│   └── state_manager.py
├── services/             # External services
│   └── mcp_service.py
└── docs/                 # Documentation
    ├── API.md
    ├── SETUP.md
    └── USAGE.md
```

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to Google service account JSON (optional)
- `OPENAI_MODEL`: OpenAI model to use (default: gpt-4o-mini)

### Model Settings
The system uses GPT-4o-mini by default for optimal performance and cost. You can change this in `config.py` or by setting the `OPENAI_MODEL` environment variable.

## 🧪 Testing

### Run Examples
```bash
python main.py
# Choose option 1 to run example demonstrations
```

### Test Individual Components
```bash
python test_multi_agent.py
```

## 🐛 Troubleshooting

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

3. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'langgraph'
   ```
   **Solution**: Install all dependencies with `pip install -r requirements.txt`

4. **Tornado Compatibility Error**
   ```
   AttributeError: module 'collections' has no attribute 'MutableMapping'
   ```
   **Solution**: This is a Python 3.11 compatibility issue. Update tornado:
   ```bash
   pip install tornado>=6.1
   ```

### Getting Help

1. Check the [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
2. Review the [API Documentation](docs/API.md)
3. Check the [Setup Guide](docs/SETUP.md) for detailed installation steps

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for the GPT models
- Google for the Calendar API
- Streamlit for the web interface framework
- LangGraph for the multi-agent orchestration

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the documentation in the `docs/` folder
- Review the troubleshooting guide

---

**Made with ❤️ for better health management**
