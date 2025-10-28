# VNASelf Setup Guide

This guide provides detailed instructions for setting up the VNASelf multi-agent system with React frontend on different platforms.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Google Calendar Setup](#google-calendar-setup)
5. [Frontend Setup](#frontend-setup)
6. [Running the Application](#running-the-application)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **Node.js**: 18.0 or higher (for React frontend)
- **npm**: 9.0 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 2GB free space
- **Internet**: Required for API calls

### Required Accounts

1. **OpenAI Account**: For GPT model access
   - Sign up at [OpenAI](https://platform.openai.com/)
   - Get API key from [API Keys page](https://platform.openai.com/api-keys)

2. **Google Cloud Account** (Optional): For calendar features
   - Sign up at [Google Cloud Console](https://console.cloud.google.com/)
   - Enable Google Calendar API

3. **Neon Database Account** (Optional): For chat history storage
   - Sign up at [Neon](https://neon.tech/)
   - Create a new database project

## Installation

### Method 1: Standard Installation

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd calendar-mcp-server
   ```

2. **Create Virtual Environment** (Recommended)
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Method 2: Using uv (Faster)

If you have `uv` installed:

```bash
uv sync
```

### Method 3: Development Installation

For development with editable install:

```bash
pip install -e .
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required
OPENAI_API_KEY=your-openai-api-key-here

# Optional
OPENAI_MODEL=gpt-4o-mini
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
NEON_DATABASE_URL=postgresql://username:password@host/database
```

### Alternative: System Environment Variables

**Windows (PowerShell)**:
```powershell
$env:OPENAI_API_KEY="your-openai-api-key-here"
$env:GOOGLE_APPLICATION_CREDENTIALS="path\to\credentials.json"
```

**Windows (Command Prompt)**:
```cmd
set OPENAI_API_KEY=your-openai-api-key-here
set GOOGLE_APPLICATION_CREDENTIALS=path\to\credentials.json
```

**macOS/Linux**:
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
```

### Configuration File

Edit `config.py` if needed:

```python
class Config:
    MODEL_NAME = "gpt-4o-mini"  # Change model if needed
    TIMEZONE = "Asia/Ho_Chi_Minh"  # Change timezone if needed
```

## Google Calendar Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "New Project"
3. Enter project name (e.g., "VNASelf Calendar")
4. Click "Create"

### Step 2: Enable Google Calendar API

1. In the project dashboard, go to "APIs & Services" > "Library"
2. Search for "Google Calendar API"
3. Click on it and press "Enable"

### Step 3: Create Service Account

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in details:
   - Name: `VNASelf-calendar`
   - Description: `Service account for VNASelf calendar integration`
4. Click "Create and Continue"
5. Skip role assignment (click "Continue")
6. Click "Done"

### Step 4: Generate Key

1. In the credentials list, find your service account
2. Click on the service account email
3. Go to "Keys" tab
4. Click "Add Key" > "Create New Key"
5. Choose "JSON" format
6. Download the key file

### Step 5: Share Calendar

1. Open [Google Calendar](https://calendar.google.com/)
2. Go to calendar settings
3. Share your calendar with the service account email
4. Give "Make changes to events" permission

### Step 6: Configure Application

1. Place the downloaded JSON file in your project directory
2. Set the environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/your-credentials.json"
   ```

## Frontend Setup

### Install Node.js Dependencies

1. **Navigate to the deploy directory**
   ```bash
   cd deploy
   ```

2. **Install React dependencies**
   ```bash
   npm install
   ```

3. **Build the frontend** (for production)
   ```bash
   npm run build
   ```

## Running the Application

### Method 1: Using the Startup Script (Recommended)

```bash
# From the project root directory
python start_app.py
```

This will start both the backend API and React frontend automatically.

### Method 2: Manual Setup

1. **Start the Backend API**
   ```bash
   # Terminal 1
   python backend_api.py
   ```

2. **Start the React Frontend**
   ```bash
   # Terminal 2
   cd deploy
   npm run dev
   ```

3. **Access the Application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Method 3: Production Deployment

1. **Build the React app**
   ```bash
   cd deploy
   npm run build
   ```

2. **Start the backend with static file serving**
   ```bash
   python backend_api.py
   ```

3. **Access the application**
   - Application: http://localhost:8000

## Verification

### Test 1: Basic Installation

```bash
python -c "import fastapi, uvicorn, langgraph, langchain_openai; print('All packages installed successfully')"
```

### Test 2: Frontend Dependencies

```bash
cd deploy
npm list --depth=0
```

### Test 3: OpenAI Connection

```bash
python -c "
import os
from langchain_openai import ChatOpenAI
model = ChatOpenAI(model='gpt-4o-mini')
print('OpenAI connection successful')
"
```

### Test 4: Google Calendar (if configured)

```bash
python -c "
from services.mcp_service import MCPService
import asyncio
async def test():
    service = MCPService()
    await service.initialize()
    print('Google Calendar connection successful')
    await service.close()
asyncio.run(test())
"
```

### Test 5: Backend API

```bash
python backend_api.py
# Check http://localhost:8000/docs for API documentation
```

### Test 6: Full System

```bash
python start_app.py
# Access http://localhost:8000 for the full application
```

## Troubleshooting

### Common Issues

#### 1. Python Version Error
```
Error: Python 3.11+ required
```
**Solution**: Install Python 3.11 or higher

#### 2. OpenAI API Key Error
```
Error: OPENAI_API_KEY environment variable not set
```
**Solution**: Set your OpenAI API key as an environment variable

#### 3. Import Errors
```
ModuleNotFoundError: No module named 'langgraph'
```
**Solution**: 
```bash
pip install -r requirements.txt
```

#### 4. Tornado Compatibility Error
```
AttributeError: module 'collections' has no attribute 'MutableMapping'
```
**Solution**: Update tornado
```bash
pip install tornado>=6.1
```

#### 5. Google Calendar Access Error
```
Error: Google Calendar API not accessible
```
**Solution**: 
1. Check your service account credentials
2. Verify calendar sharing permissions
3. Ensure Google Calendar API is enabled

#### 6. Streamlit Port Error
```
Error: Port 8501 already in use
```
**Solution**: 
```bash
streamlit run app.py --server.port 8502
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from main import main
import asyncio
asyncio.run(main())
"
```

### Performance Issues

#### Slow Response Times
1. Check internet connection
2. Verify API key validity
3. Consider using a faster model (gpt-3.5-turbo)

#### Memory Issues
1. Close unused conversation threads
2. Restart the application periodically
3. Increase system memory

### Getting Help

1. Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Review error logs
3. Test individual components
4. Create an issue in the repository

## Platform-Specific Notes

### Windows

- Use PowerShell or Command Prompt
- Ensure Python is in PATH
- Use forward slashes in file paths for environment variables

### macOS

- May need to install Xcode command line tools
- Use `python3` instead of `python` if both versions installed

### Linux

- May need to install additional system packages
- Use `python3` command
- Check firewall settings for web interface

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive data
3. **Restrict service account permissions** to minimum required
4. **Regularly rotate API keys**
5. **Use HTTPS** for production deployments
6. **Monitor API usage** for unusual activity

## Next Steps

After successful setup:

1. Read the [Usage Guide](USAGE.md)
2. Check the [API Documentation](API.md)
3. Try the example interactions
4. Customize the configuration as needed
5. Set up monitoring and logging for production use
