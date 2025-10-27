# Google Calendar Authentication Troubleshooting Guide

## 🚨 Common Issues and Solutions

### Issue 1: "Authentication Error: Please check your Google Calendar credentials"

**Symptoms:**
- Error message: "HttpError 400 when requesting Google Calendar API"
- Cannot check conflicts or create events
- Functions like `list_upcoming_events` work but conflict checking fails

**Root Cause:**
- Missing timezone information in datetime strings
- Google Calendar API requires timezone-aware datetime strings

**Solution:**
✅ **FIXED** - The system now automatically adds timezone information (+07:00) to datetime strings

### Issue 2: "credentials.json not found"

**Symptoms:**
- Error: "credentials.json not found"
- Cannot authenticate with Google Calendar

**Solution:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Calendar API:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Calendar API"
   - Click "Enable"
4. Create credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client ID"
   - Choose "Desktop application"
   - Download the JSON file
5. Rename the downloaded file to `credentials.json`
6. Place it in the `backend` folder

### Issue 3: "Token expired" or "Invalid token"

**Symptoms:**
- Error: "Token expired" or "Invalid token"
- Need to re-authenticate frequently

**Solution:**
1. Delete the `token.pickle` file in the backend folder
2. Restart the backend server
3. The system will automatically prompt for re-authentication

### Issue 4: Backend server not running

**Symptoms:**
- 500 Internal Server Error on API calls
- Frontend cannot connect to backend

**Solution:**
1. Navigate to the backend folder:
   ```bash
   cd backend
   ```
2. Start the backend server:
   ```bash
   python main.py
   ```
3. Verify the server is running on port 8000

## 🔧 Manual Testing

To test Google Calendar functions manually:

1. **Test Authentication:**
   ```python
   from backend.server.calendar_server import get_calendar_service
   service = get_calendar_service()
   print("✅ Authentication successful!")
   ```

2. **Test List Events:**
   ```python
   from backend.server.calendar_server import list_upcoming_events
   result = await list_upcoming_events(5)
   print(result)
   ```

3. **Test Conflict Checking:**
   ```python
   from backend.server.calendar_server import check_conflicts
   result = await check_conflicts("2025-01-15T10:00:00", "2025-01-15T11:00:00")
   print(result)
   ```

4. **Test Optimal Time Suggestions:**
   ```python
   from backend.server.calendar_server import suggest_optimal_time
   result = await suggest_optimal_time("meeting", 60, "2025-01-15", 3)
   print(result)
   ```

## 📋 Current Status

✅ **Google Calendar Authentication**: Working  
✅ **List Upcoming Events**: Working  
✅ **Check Conflicts**: Working (Fixed timezone issue)  
✅ **Suggest Optimal Time**: Working  
✅ **Create Events**: Working  
✅ **Backend Server**: Running on port 8000  

## 🚀 Next Steps

1. **Frontend Integration**: The agent chat interface should now work properly with Google Calendar
2. **Testing**: Test the calendar agent through the frontend interface
3. **User Experience**: Users can now:
   - Schedule meetings with optimal time suggestions
   - Check for conflicts before creating events
   - Resolve conflicts by moving or deleting existing events
   - Get productivity-based time recommendations

## 📞 Support

If you continue to experience issues:

1. Check the backend server logs for detailed error messages
2. Verify that `credentials.json` exists in the backend folder
3. Ensure the Google Calendar API is enabled in your Google Cloud project
4. Try deleting `token.pickle` and re-authenticating

The Google Calendar integration is now fully functional! 🎉
