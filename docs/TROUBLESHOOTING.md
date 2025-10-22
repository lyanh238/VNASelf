# ViCare Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the ViCare multi-agent system.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Configuration Problems](#configuration-problems)
3. [Runtime Errors](#runtime-errors)
4. [Performance Issues](#performance-issues)
5. [API Connection Problems](#api-connection-problems)
6. [Calendar Integration Issues](#calendar-integration-issues)
7. [Web Interface Problems](#web-interface-problems)
8. [Debugging Tools](#debugging-tools)

## Installation Issues

### Python Version Compatibility

#### Error: Python Version Too Old
```
Error: Python 3.11+ required, but you have Python 3.10.x
```

**Solution**:
1. Install Python 3.11 or higher
2. Update your PATH environment variable
3. Verify installation: `python --version`

#### Error: Python Not Found
```
'python' is not recognized as an internal or external command
```

**Solution**:
1. Install Python from [python.org](https://python.org)
2. Check "Add Python to PATH" during installation
3. Restart your terminal/command prompt

### Package Installation Failures

#### Error: pip install fails
```
ERROR: Could not find a version that satisfies the requirement
```

**Solutions**:
1. Update pip: `python -m pip install --upgrade pip`
2. Use specific versions: `pip install package==version`
3. Check internet connection
4. Try using a virtual environment

#### Error: Permission Denied
```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

**Solutions**:
1. Use virtual environment: `python -m venv venv`
2. Activate virtual environment: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Unix)
3. Install packages in virtual environment

### Tornado Compatibility Issues

#### Error: collections.MutableMapping
```
AttributeError: module 'collections' has no attribute 'MutableMapping'
```

**Solution**:
```bash
pip uninstall tornado
pip install tornado>=6.1
```

This is a Python 3.11 compatibility issue with older tornado versions.

## Configuration Problems

### OpenAI API Key Issues

#### Error: Missing API Key
```
Error: OPENAI_API_KEY environment variable not set
```

**Solutions**:
1. Set environment variable:
   ```bash
   # Windows
   set OPENAI_API_KEY=your-key-here
   
   # macOS/Linux
   export OPENAI_API_KEY=your-key-here
   ```
2. Create `.env` file in project root:
   ```
   OPENAI_API_KEY=your-key-here
   ```
3. Verify key is set: `echo $OPENAI_API_KEY` (Unix) or `echo %OPENAI_API_KEY%` (Windows)

#### Error: Invalid API Key
```
Error: Invalid API key provided
```

**Solutions**:
1. Check API key format (starts with `sk-`)
2. Verify key is active in OpenAI dashboard
3. Check for extra spaces or characters
4. Generate new key if needed

#### Error: Insufficient Credits
```
Error: You exceeded your current quota
```

**Solutions**:
1. Add credits to your OpenAI account
2. Check usage limits in OpenAI dashboard
3. Consider using a different model (gpt-3.5-turbo)

### Google Calendar Configuration

#### Error: Google Calendar API Not Enabled
```
Error: Google Calendar API has not been used in project
```

**Solutions**:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Enable Google Calendar API
4. Wait a few minutes for activation

#### Error: Service Account Issues
```
Error: The caller does not have permission
```

**Solutions**:
1. Check service account permissions
2. Verify calendar sharing with service account
3. Regenerate service account key
4. Check project billing status

## Runtime Errors

### Import Errors

#### Error: Module Not Found
```
ModuleNotFoundError: No module named 'langgraph'
```

**Solutions**:
1. Install missing package: `pip install langgraph`
2. Install all requirements: `pip install -r requirements.txt`
3. Check virtual environment activation
4. Verify Python path

#### Error: Version Conflicts
```
ImportError: cannot import name 'X' from 'Y'
```

**Solutions**:
1. Check package versions: `pip list`
2. Update conflicting packages
3. Use virtual environment to isolate dependencies
4. Check compatibility matrix

### Initialization Errors

#### Error: Multi-Agent System Initialization Failed
```
Error: Failed to initialize multi-agent system
```

**Solutions**:
1. Check all environment variables
2. Verify API connections
3. Check system resources (memory, disk space)
4. Review error logs for specific issues

#### Error: MCP Service Connection Failed
```
Error: MCP service connection failed
```

**Solutions**:
1. Check Google Calendar API credentials
2. Verify internet connection
3. Check firewall settings
4. Restart the application

## Performance Issues

### Slow Response Times

#### Symptoms
- Long delays between user input and response
- "Meowing..." spinner runs for extended periods
- Timeout errors

**Solutions**:
1. Check internet connection speed
2. Verify API key validity and limits
3. Use faster model (gpt-3.5-turbo instead of gpt-4)
4. Check system resources (CPU, memory)
5. Close other applications

#### Memory Issues
```
MemoryError: Unable to allocate array
```

**Solutions**:
1. Close unused conversation threads
2. Restart the application periodically
3. Increase system memory
4. Use smaller batch sizes
5. Clear conversation history

### High API Usage

#### Symptoms
- Rapid API quota consumption
- Unexpected charges
- Rate limiting errors

**Solutions**:
1. Monitor API usage in OpenAI dashboard
2. Implement request caching
3. Use more efficient prompts
4. Set usage limits
5. Consider batch processing

## API Connection Problems

### OpenAI API Issues

#### Error: Connection Timeout
```
requests.exceptions.ConnectTimeout: HTTPSConnectionPool
```

**Solutions**:
1. Check internet connection
2. Verify OpenAI service status
3. Try again after a few minutes
4. Check firewall/proxy settings
5. Use different network if available

#### Error: Rate Limiting
```
Error: Rate limit exceeded
```

**Solutions**:
1. Wait before making more requests
2. Implement exponential backoff
3. Reduce request frequency
4. Upgrade to higher tier API plan
5. Use request queuing

### Google Calendar API Issues

#### Error: Quota Exceeded
```
Error: Quota exceeded for quota metric
```

**Solutions**:
1. Check Google Cloud Console quotas
2. Request quota increase if needed
3. Implement request caching
4. Optimize API calls
5. Use batch requests

#### Error: Authentication Failed
```
Error: Invalid credentials
```

**Solutions**:
1. Regenerate service account key
2. Check key file path and permissions
3. Verify service account permissions
4. Check calendar sharing settings
5. Test credentials with Google API Explorer

## Calendar Integration Issues

### Event Creation Problems

#### Error: Invalid Date Format
```
Error: Invalid date format provided
```

**Solutions**:
1. Use ISO format: YYYY-MM-DDTHH:MM:SS
2. Check timezone settings
3. Verify date is not in the past
4. Use natural language dates when possible

#### Error: Calendar Not Found
```
Error: Calendar not found
```

**Solutions**:
1. Check calendar ID
2. Verify calendar sharing permissions
3. Use primary calendar if unsure
4. Check service account access

### Event Access Issues

#### Error: Permission Denied
```
Error: Insufficient permissions
```

**Solutions**:
1. Check calendar sharing settings
2. Verify service account permissions
3. Regenerate service account key
4. Check project permissions

## Web Interface Problems

### Streamlit Issues

#### Error: Port Already in Use
```
Error: Port 8501 is already in use
```

**Solutions**:
1. Use different port: `streamlit run app.py --server.port 8502`
2. Kill existing process: `taskkill /f /im streamlit.exe` (Windows)
3. Find and kill process: `lsof -ti:8501 | xargs kill` (Unix)
4. Restart your computer

#### Error: Streamlit Not Found
```
'streamlit' is not recognized as an internal or external command
```

**Solutions**:
1. Install streamlit: `pip install streamlit`
2. Use python module: `python -m streamlit run app.py`
3. Check virtual environment activation
4. Verify PATH environment variable

### Browser Issues

#### Error: Page Won't Load
- Browser shows "This site can't be reached"

**Solutions**:
1. Check if Streamlit is running
2. Verify correct URL: `http://localhost:8501`
3. Try different browser
4. Check firewall settings
5. Clear browser cache

#### Error: JavaScript Errors
- Console shows JavaScript errors
- Interface doesn't respond

**Solutions**:
1. Refresh the page
2. Clear browser cache
3. Disable browser extensions
4. Try different browser
5. Check browser console for specific errors

## Debugging Tools

### Enable Debug Mode

#### Environment Variables
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export LOG_LEVEL=DEBUG
```

#### Python Debugging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Your code here
```

### Log Analysis

#### Check Logs
```bash
# Streamlit logs
streamlit run app.py --logger.level debug

# Python logs
python main.py 2>&1 | tee debug.log
```

#### Common Log Patterns
- `ERROR`: Critical issues requiring immediate attention
- `WARNING`: Potential issues that may cause problems
- `INFO`: General information about system operation
- `DEBUG`: Detailed information for troubleshooting

### Testing Individual Components

#### Test OpenAI Connection
```python
from langchain_openai import ChatOpenAI
model = ChatOpenAI(model="gpt-4o-mini")
response = model.invoke("Hello")
print(response)
```

#### Test Google Calendar
```python
from services.mcp_service import MCPService
import asyncio

async def test():
    service = MCPService()
    await service.initialize()
    # Test calendar operations
    await service.close()

asyncio.run(test())
```

#### Test Multi-Agent System
```python
from core import MultiAgentSystem
import asyncio

async def test():
    system = MultiAgentSystem()
    await system.initialize()
    response = await system.process_message("Hello")
    print(response)
    await system.close()

asyncio.run(test())
```

### System Diagnostics

#### Check System Resources
```bash
# Memory usage
free -h  # Linux
system_profiler SPHardwareDataType  # macOS
wmic memorychip  # Windows

# Disk space
df -h  # Linux/macOS
dir  # Windows
```

#### Check Network Connectivity
```bash
# Test internet connection
ping google.com

# Test API endpoints
curl -I https://api.openai.com/v1/models
```

### Getting Help

#### Before Asking for Help

1. **Check this troubleshooting guide**
2. **Enable debug mode and collect logs**
3. **Test individual components**
4. **Check system requirements**
5. **Verify configuration**

#### When Reporting Issues

Include the following information:

1. **Operating System**: Windows/macOS/Linux version
2. **Python Version**: `python --version`
3. **Error Message**: Complete error text
4. **Steps to Reproduce**: What you did before the error
5. **Logs**: Debug logs if available
6. **Configuration**: Environment variables (without sensitive data)

#### Support Channels

1. **GitHub Issues**: Create an issue in the repository
2. **Documentation**: Check all documentation files
3. **Community**: Check for similar issues in the repository
4. **Stack Overflow**: Search for related questions

### Prevention Tips

1. **Keep Dependencies Updated**: Regularly update packages
2. **Use Virtual Environments**: Isolate project dependencies
3. **Monitor API Usage**: Track quota and costs
4. **Backup Configuration**: Save working configurations
5. **Test Regularly**: Run tests after changes
6. **Document Changes**: Keep track of modifications

### Emergency Recovery

#### Complete Reset
```bash
# Remove virtual environment
rm -rf venv

# Recreate virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall everything
pip install -r requirements.txt

# Test installation
python -c "import streamlit, langgraph; print('OK')"
```

#### Configuration Reset
```bash
# Remove configuration files
rm .env
rm token.pickle
rm token.json

# Reconfigure
# Set environment variables
# Re-authenticate with Google Calendar
```

This troubleshooting guide should help you resolve most common issues. If you encounter problems not covered here, please create an issue in the repository with detailed information about your problem.
