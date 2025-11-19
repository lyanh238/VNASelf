"""
Backend API for React frontend integration with Multi-Agent System
"""

import asyncio
import json
import uuid
import os
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
import shutil
import aiofiles

# Load .env file from project root before importing other modules
# override=True ensures .env file values take precedence over system environment variables
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path, override=True)

from contextlib import asynccontextmanager
from core import MultiAgentSystem
from langsmith import traceable
from services.conversation_service import ConversationService
from services.conversation_title_service import ConversationTitleService
from services.payment_history_service import PaymentHistoryService

# Note: FastAPI app will be created after lifespan function is defined

# Global multi-agent system instance
multi_agent_system = None
conversation_service = None
conversation_title_service = None
payment_history_service: Optional[PaymentHistoryService] = None

# Account file path
ACCOUNT_FILE_PATH = "account.json"

# Upload directory
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# OCR output directory
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Pydantic models
class ChatMessage(BaseModel):
    content: str
    thread_id: Optional[str] = None
    user_id: Optional[str] = None
    model_name: Optional[str] = "gpt-4o"
    locale: Optional[str] = None

class ChatResponse(BaseModel):
    content: str
    agent_name: str
    thread_id: str
    timestamp: int

class TimeSeriesResponse(BaseModel):
    labels: List[str]
    values: List[float]
    unit: str = "VND"

class ForecastResponse(BaseModel):
    history: Dict[str, Any]
    forecast: Dict[str, Any]
    unit: str = "VND"

class TimeSeriesByCategoryResponse(BaseModel):
    labels: List[str]
    series: List[Dict[str, Any]]  # [{category, values}]
    unit: str = "VND"

class ChatHistory(BaseModel):
    thread_id: str
    messages: List[Dict[str, Any]]

class ThreadSummary(BaseModel):
    thread_id: str
    title: str
    last_message: str
    timestamp: int

class ConversationData(BaseModel):
    thread_id: str
    title: str
    summary: Optional[str] = None
    message_count: int = 0
    last_message_content: Optional[str] = None
    last_message_timestamp: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None

class AccountData(BaseModel):
    name: str
    email: str
    password: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

def load_accounts() -> List[Dict[str, Any]]:
    """Load accounts from account.json file"""
    try:
        if os.path.exists(ACCOUNT_FILE_PATH):
            with open(ACCOUNT_FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading accounts: {e}")
        return []

def save_accounts(accounts: List[Dict[str, Any]]) -> bool:
    """Save accounts to account.json file"""
    try:
        with open(ACCOUNT_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(accounts, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving accounts: {e}")
        return False

def add_or_update_account(account_data: AccountData) -> bool:
    """Add or update account in account.json"""
    try:
        accounts = load_accounts()
        
        # Check if account exists
        existing_index = None
        for i, acc in enumerate(accounts):
            if acc.get('email') == account_data.email:
                existing_index = i
                break
        
        # Prepare account data
        account_dict = {
            "name": account_data.name,
            "email": account_data.email,
            "password": account_data.password,
            "created_at": account_data.created_at or datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        if existing_index is not None:
            # Update existing account
            accounts[existing_index] = account_dict
        else:
            # Add new account
            accounts.append(account_dict)
        
        return save_accounts(accounts)
    except Exception as e:
        print(f"Error adding/updating account: {e}")
        return False

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()
multi_agent_system : Optional[MultiAgentSystem] = None
conversation_service : Optional[ConversationService] = None
conversation_title_service : Optional[ConversationTitleService] = None
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown lifecycle for FastAPI app."""
    global multi_agent_system, conversation_service, conversation_title_service, payment_history_service

    # --- Startup logic ---
    try:
        # Initialize multi-agent system
        multi_agent_system = MultiAgentSystem()
        await multi_agent_system.initialize()
        print("[OK] Multi-Agent System initialized successfully!")

        # Initialize conversation services
        conversation_service = ConversationService()
        await conversation_service.initialize()

        conversation_title_service = ConversationTitleService()
        await conversation_title_service.initialize()

        payment_history_service = PaymentHistoryService()
        await payment_history_service.initialize()

    except Exception as e:
        print(f"[ERROR] Error initializing services: {str(e)}")
        raise

    # Yield control to FastAPI runtime (app runs while suspended here)
    yield

    # --- Shutdown logic ---
    if multi_agent_system:
        await multi_agent_system.close()
    if conversation_service:
        await conversation_service.close()
    # if conversation_title_service:
    #     await conversation_title_service.close()

# Initialize FastAPI app with lifespan
app = FastAPI(title="VNASelf API", version="1.0.0", lifespan=lifespan)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Serve the React app."""
    return FileResponse("../frontend/dist/index.html")

@app.post("/api/chat", response_model=ChatResponse)
@traceable(name="api.chat_endpoint")
async def chat_endpoint(message: ChatMessage):
    """Process a chat message through the multi-agent system."""
    if not multi_agent_system:
        raise HTTPException(status_code=500, detail="Multi-agent system not initialized")
    
    try:
        # Generate thread_id if not provided
        thread_id = message.thread_id or str(uuid.uuid4())
        user_id = message.user_id or "default_user"
        
        # Process the message
        response = await multi_agent_system.process_message(
            message.content,
            thread_id=thread_id,
            user_id=user_id,
            model_name=message.model_name,
            locale=message.locale
        )
        
        # Extract agent name from response
        agent_name = "Assistant"
        if response.startswith("[") and "]" in response:
            agent_name = response.split("]")[0][1:]
            response = response.split("]", 1)[1].strip()
        
        # Handle conversation metadata
        if conversation_service:
            # Check if this is a new conversation
            existing_conversation = await conversation_service.get_conversation_by_thread_id(thread_id)
            
            if not existing_conversation:
                # Generate title from the first message
                title = "New conversation"
                if conversation_title_service:
                    title = await conversation_title_service.generate_title_from_content(message.content)
                
                # Create new conversation
                await conversation_service.create_conversation(
                    thread_id=thread_id,
                    user_id=user_id,
                    title=title
                )
            else:
                # Update existing conversation
                await conversation_service.increment_message_count(thread_id)
            
            # Update last message info
            await conversation_service.update_conversation_last_message(
                thread_id=thread_id,
                last_message_content=response,
                last_message_timestamp=int(datetime.now().timestamp() * 1000)
            )
        
        return ChatResponse(
            content=response,
            agent_name=agent_name,
            thread_id=thread_id,
            timestamp=int(datetime.now().timestamp() * 1000)
        )
        
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"[ERROR] Error processing message: {str(e)}")
        print(f"[ERROR] Traceback:\n{error_traceback}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.get("/api/chat/history/{thread_id}", response_model=ChatHistory)
@traceable(name="api.get_chat_history")
async def get_chat_history(thread_id: str, limit: int = 50):
    """Get chat history for a specific thread."""
    if not multi_agent_system:
        raise HTTPException(status_code=500, detail="Multi-agent system not initialized")
    
    try:
        # Get all messages for the conversation (no pagination for full restoration)
        messages = await multi_agent_system.get_all_conversation_messages(thread_id)
        return ChatHistory(thread_id=thread_id, messages=messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting chat history: {str(e)}")

@app.get("/api/chat/threads/{user_id}", response_model=List[ThreadSummary])
@traceable(name="api.get_user_threads")
async def get_user_threads(user_id: str):
    """Get all conversation threads for a user."""
    if not multi_agent_system:
        raise HTTPException(status_code=500, detail="Multi-agent system not initialized")
    
    try:
        thread_ids = await multi_agent_system.get_user_threads(user_id)
        summaries = []
        
        for thread_id in thread_ids:
            # Get recent messages for summary
            messages = await multi_agent_system.get_chat_history(thread_id, limit=1)
            if messages:
                last_message = messages[-1]
                # Create a simple title from the first user message
                first_user_message = next(
                    (msg for msg in messages if msg.get("message_type") == "user"), 
                    last_message
                )
                title = first_user_message.get("content", "New conversation")[:50]
                if len(title) == 50:
                    title += "..."
                
                summaries.append(ThreadSummary(
                    thread_id=thread_id,
                    title=title,
                    last_message=last_message.get("content", ""),
                    timestamp=last_message.get("timestamp", 0),
                    message_count=len(messages)
                ))
        
        # Sort by timestamp (most recent first)
        summaries.sort(key=lambda x: x.timestamp, reverse=True)
        return summaries
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user threads: {str(e)}")

# Finance analytics endpoints for charts
@app.get("/api/finance/timeseries", response_model=TimeSeriesResponse)
@traceable(name="api.finance_timeseries")
async def get_finance_timeseries(user_id: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None):
    if not payment_history_service:
        raise HTTPException(status_code=500, detail="Payment history service not initialized")
    try:
        from datetime import datetime as dt
        sd = dt.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        ed = dt.strptime(end_date, "%Y-%m-%d").date() if end_date else None
        series = await payment_history_service.get_daily_timeseries(user_id=user_id, start_date=sd, end_date=ed)
        labels = [p["date"] for p in series]
        values = [p["amount"] for p in series]
        return TimeSeriesResponse(labels=labels, values=values)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating timeseries: {str(e)}")

@app.get("/api/finance/forecast", response_model=ForecastResponse)
@traceable(name="api.finance_forecast")
async def get_finance_forecast(user_id: Optional[str] = None, days_ahead: int = 14):
    if not payment_history_service:
        raise HTTPException(status_code=500, detail="Payment history service not initialized")
    try:
        # Reuse agent tool logic via light inline import to avoid duplication
        from agents.finance_agent import forecast_spending
        result = forecast_spending.invoke({"user_id": user_id, "days_ahead": days_ahead})
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Forecast failed"))
        return ForecastResponse(history=result["history"], forecast=result["forecast"], unit=result.get("unit", "VND"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating forecast: {str(e)}")

@app.get("/api/finance/chart/spending")
@traceable(name="api.finance_chart_spending")
async def get_spending_chart(start_date: Optional[str] = None, end_date: Optional[str] = None, user_id: Optional[str] = None):
    """API endpoint để tạo biểu đồ chi tiêu tương tác"""
    if not payment_history_service:
        raise HTTPException(status_code=500, detail="Payment history service not initialized")
    try:
        from datetime import datetime as dt
        
        # Parse dates
        sd = dt.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        ed = dt.strptime(end_date, "%Y-%m-%d").date() if end_date else None
        
        # Get timeseries data directly from payment service (ignore user_id per request)
        series = await payment_history_service.get_daily_timeseries(
            user_id=None,
            start_date=sd,
            end_date=ed
        )
        
        if not series:
            # Return 200 with a friendly message so UI can render empty state gracefully
            return {
                "success": False,
                "chart_type": "line",
                "title": f"Biểu đồ chi tiêu từ {start_date or 'đầu'} đến {end_date or 'cuối'}",
                "data": {"labels": [], "datasets": []},
                "options": {},
                "error": "Không có dữ liệu chi tiêu trong khoảng thời gian này"
            }
        
        # Format data for interactive chart
        chart_data = {
            "labels": [point["date"] for point in series],
            "datasets": [{
                "label": "Chi tiêu (VND)",
                "data": [point["amount"] for point in series],
                "borderColor": "rgb(75, 192, 192)",
                "backgroundColor": "rgba(75, 192, 192, 0.1)",
                "tension": 0.1,
                "fill": True
            }]
        }
        
        # Create chart options
        chart_options = {
            "responsive": True,
            "interaction": {
                "intersect": False,
                "mode": "index"
            },
            "plugins": {
                "title": {
                    "display": True,
                    "text": f"Biểu đồ chi tiêu từ {start_date or 'đầu'} đến {end_date or 'cuối'}"
                },
                "tooltip": {
                    "callbacks": {
                        "label": "function(context) { return 'Chi tiêu: ' + context.parsed.y.toLocaleString('vi-VN') + ' VND'; }"
                    }
                }
            },
            "scales": {
                "y": {
                    "beginAtZero": True,
                    "ticks": {
                        "callback": "function(value) { return value.toLocaleString('vi-VN') + ' VND'; }"
                    }
                }
            }
        }
        
        return {
            "success": True,
            "chart_type": "line",
            "title": f"Biểu đồ chi tiêu từ {start_date or 'đầu'} đến {end_date or 'cuối'}",
            "data": chart_data,
            "options": chart_options
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating spending chart: {str(e)}")

@app.get("/api/finance/chart/forecast")
@traceable(name="api.finance_chart_forecast")
async def get_forecast_chart(days_ahead: int = 7, user_id: Optional[str] = None):
    """API endpoint để tạo biểu đồ dự báo chi tiêu"""
    if not payment_history_service:
        raise HTTPException(status_code=500, detail="Payment history service not initialized")
    try:
        from datetime import datetime as dt, timedelta
        import pandas as pd
        from prophet import Prophet
        
        # Get historical data (ignore user_id per request)
        series = await payment_history_service.get_daily_timeseries(user_id=None)
        
        if len(series) < 7:
            return {
                "success": False,
                "chart_type": "line",
                "title": f"Biểu đồ dự báo chi tiêu {days_ahead} ngày tới",
                "data": {"labels": [], "datasets": []},
                "options": {},
                "error": "Không có đủ dữ liệu để dự báo (cần ít nhất 7 ngày)"
            }
        
        # Prepare data for Prophet
        df = pd.DataFrame(series)
        df['ds'] = pd.to_datetime(df['date'])
        df['y'] = df['amount']
        df = df[['ds', 'y']].dropna()
        
        # Train Prophet model
        model = Prophet(daily_seasonality=True, weekly_seasonality=True)
        model.fit(df)
        
        # Create future dataframe
        future = model.make_future_dataframe(periods=days_ahead)
        forecast = model.predict(future)
        
        # Get historical and forecast data
        historical_data = forecast[forecast['ds'] <= df['ds'].max()]
        forecast_data = forecast[forecast['ds'] > df['ds'].max()]
        
        # Format data for chart
        all_dates = pd.concat([historical_data['ds'], forecast_data['ds']])
        all_dates = all_dates.dt.strftime('%Y-%m-%d').tolist()
        
        chart_data = {
            "labels": all_dates,
            "datasets": [
                {
                    "label": "Chi tiêu thực tế",
                    "data": historical_data['yhat'].tolist() + [None] * len(forecast_data),
                    "borderColor": "rgb(75, 192, 192)",
                    "backgroundColor": "rgba(75, 192, 192, 0.1)",
                    "tension": 0.1,
                    "fill": False
                },
                {
                    "label": f"Dự báo {days_ahead} ngày tới",
                    "data": [None] * len(historical_data) + forecast_data['yhat'].tolist(),
                    "borderColor": "rgb(255, 99, 132)",
                    "backgroundColor": "rgba(255, 99, 132, 0.1)",
                    "tension": 0.1,
                    "fill": False,
                    "borderDash": [5, 5]
                }
            ]
        }
        
        # Create chart options
        chart_options = {
            "responsive": True,
            "interaction": {
                "intersect": False,
                "mode": "index"
            },
            "plugins": {
                "title": {
                    "display": True,
                    "text": f"Biểu đồ dự báo chi tiêu {days_ahead} ngày tới"
                },
                "tooltip": {
                    "callbacks": {
                        "label": "function(context) { return context.dataset.label + ': ' + (context.parsed.y ? context.parsed.y.toLocaleString('vi-VN') + ' VND' : 'N/A'); }"
                    }
                }
            },
            "scales": {
                "y": {
                    "beginAtZero": True,
                    "ticks": {
                        "callback": "function(value) { return value.toLocaleString('vi-VN') + ' VND'; }"
                    }
                }
            }
        }
        
        return {
            "success": True,
            "chart_type": "line",
            "title": f"Biểu đồ dự báo chi tiêu {days_ahead} ngày tới",
            "data": chart_data,
            "options": chart_options
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating forecast chart: {str(e)}")

@app.get("/api/finance/timeseries-by-category", response_model=TimeSeriesByCategoryResponse)
@traceable(name="api.finance_timeseries_by_category")
async def get_finance_timeseries_by_category(user_id: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None):
    if not payment_history_service:
        raise HTTPException(status_code=500, detail="Payment history service not initialized")
    try:
        from datetime import datetime as dt
        sd = dt.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        ed = dt.strptime(end_date, "%Y-%m-%d").date() if end_date else None
        cat_map = await payment_history_service.get_daily_timeseries_by_category(user_id=user_id, start_date=sd, end_date=ed)
        # unify labels
        label_set = set()
        for series in cat_map.values():
            for p in series:
                label_set.add(p["date"])
        labels = sorted(label_set)
        series_list = []
        for cat, series in cat_map.items():
            values_map = {p["date"]: p["amount"] for p in series}
            values = [values_map.get(d, 0) for d in labels]
            series_list.append({"category": cat, "values": values})
        return TimeSeriesByCategoryResponse(labels=labels, series=series_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating timeseries by category: {str(e)}")

@app.delete("/api/chat/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """Delete a conversation thread."""
    if not multi_agent_system:
        raise HTTPException(status_code=500, detail="Multi-agent system not initialized")
    
    try:
        success = await multi_agent_system.delete_thread(thread_id)
        if success:
            return {"message": "Thread deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Thread not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting thread: {str(e)}")

# Conversation management endpoints
@app.get("/api/conversations/{user_id}", response_model=List[ConversationData])
async def get_user_conversations(user_id: str, limit: int = 50, offset: int = 0):
    """Get all conversations for a user."""
    if not conversation_service:
        raise HTTPException(status_code=500, detail="Conversation service not initialized")
    
    try:
        conversations = await conversation_service.get_user_conversations(user_id, limit, offset)
        return [ConversationData(**conv.to_dict()) for conv in conversations]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting conversations: {str(e)}")

@app.get("/api/conversations/{user_id}/{thread_id}", response_model=ConversationData)
async def get_conversation(user_id: str, thread_id: str):
    """Get a specific conversation."""
    if not conversation_service:
        raise HTTPException(status_code=500, detail="Conversation service not initialized")
    
    try:
        conversation = await conversation_service.get_conversation_by_thread_id(thread_id)
        if not conversation or conversation.user_id != user_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return ConversationData(**conversation.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting conversation: {str(e)}")

@app.put("/api/conversations/{user_id}/{thread_id}")
async def update_conversation(user_id: str, thread_id: str, update_data: ConversationUpdate):
    """Update conversation title or summary."""
    if not conversation_service:
        raise HTTPException(status_code=500, detail="Conversation service not initialized")
    
    try:
        # Verify conversation exists and belongs to user
        conversation = await conversation_service.get_conversation_by_thread_id(thread_id)
        if not conversation or conversation.user_id != user_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        success = True
        
        # Update title if provided
        if update_data.title:
            success &= await conversation_service.update_conversation_title(thread_id, update_data.title)
        
        # Update summary if provided
        if update_data.summary:
            success &= await conversation_service.update_conversation_summary(thread_id, update_data.summary)
        
        if success:
            return {"message": "Conversation updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update conversation")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating conversation: {str(e)}")

@app.delete("/api/conversations/{user_id}/{thread_id}")
async def delete_conversation(user_id: str, thread_id: str):
    """Delete a conversation."""
    if not conversation_service:
        raise HTTPException(status_code=500, detail="Conversation service not initialized")
    
    try:
        # Verify conversation exists and belongs to user
        conversation = await conversation_service.get_conversation_by_thread_id(thread_id)
        if not conversation or conversation.user_id != user_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Delete conversation metadata
        success = await conversation_service.delete_conversation(thread_id)
        
        # Also delete the thread messages if multi-agent system is available
        if multi_agent_system:
            await multi_agent_system.delete_thread(thread_id)
        
        if success:
            return {"message": "Conversation deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete conversation")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")

@app.post("/api/conversations/{user_id}/{thread_id}/regenerate-title")
async def regenerate_conversation_title(user_id: str, thread_id: str):
    """Regenerate conversation title using LLM."""
    if not conversation_service or not conversation_title_service:
        raise HTTPException(status_code=500, detail="Services not initialized")
    
    try:
        # Verify conversation exists and belongs to user
        conversation = await conversation_service.get_conversation_by_thread_id(thread_id)
        if not conversation or conversation.user_id != user_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get conversation messages
        if not multi_agent_system:
            raise HTTPException(status_code=500, detail="Multi-agent system not initialized")
        
        messages = await multi_agent_system.get_chat_history(thread_id, limit=10)
        
        # Generate new title
        new_title = await conversation_title_service.generate_title_from_messages(messages)
        
        # Update conversation title
        success = await conversation_service.update_conversation_title(thread_id, new_title)
        
        if success:
            return {"title": new_title, "message": "Title regenerated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update title")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error regenerating title: {str(e)}")

# Account management endpoints
@app.post("/api/accounts/save")
async def save_account(account_data: AccountData):
    """Save account data to account.json file"""
    try:
        success = add_or_update_account(account_data)
        if success:
            return {"success": True, "message": "Account saved successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save account")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving account: {str(e)}")

@app.get("/api/accounts")
async def get_accounts():
    """Get all accounts from account.json file"""
    try:
        accounts = load_accounts()
        return {"success": True, "accounts": accounts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading accounts: {str(e)}")

@app.get("/api/accounts/{email}")
async def get_account_by_email(email: str):
    """Get specific account by email"""
    try:
        accounts = load_accounts()
        account = next((acc for acc in accounts if acc.get('email') == email), None)
        if account:
            return {"success": True, "account": account}
        else:
            raise HTTPException(status_code=404, detail="Account not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading account: {str(e)}")

@app.delete("/api/accounts/{email}")
async def delete_account(email: str):
    """Delete account by email"""
    try:
        accounts = load_accounts()
        filtered_accounts = [acc for acc in accounts if acc.get('email') != email]
        
        if len(filtered_accounts) == len(accounts):
            raise HTTPException(status_code=404, detail="Account not found")
        
        success = save_accounts(filtered_accounts)
        if success:
            return {"success": True, "message": "Account deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete account")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting account: {str(e)}")

@app.post("/api/upload")
@traceable(name="api.upload_file")
async def upload_file(file: UploadFile = File(...), user_id: Optional[str] = Form(None)):
    """Upload a file (image or PDF) for OCR processing."""
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}{file_ext}"
        file_path = UPLOAD_DIR / safe_filename
        
        # Save uploaded file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Return file path for OCR processing
        return JSONResponse({
            "success": True,
            "file_path": str(file_path),
            "filename": file.filename,
            "file_type": "pdf" if file_ext == ".pdf" else "image",
            "message": "File uploaded successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"[ERROR] Error uploading file: {str(e)}")
        print(f"[ERROR] Traceback:\n{error_traceback}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@app.get("/api/ocr/markdown/{filename}")
async def get_ocr_markdown(filename: str):
    """Download the generated markdown file after OCR processing."""
    safe_name = Path(filename).name
    file_path = OUTPUT_DIR / safe_name
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Markdown file not found")
    
    return FileResponse(file_path, media_type="text/markdown", filename=safe_name)

@app.post("/api/upload-and-process")
@traceable(name="api.upload_and_process")
async def upload_and_process(
    file: UploadFile = File(...), 
    user_id: Optional[str] = Form(None),
    thread_id: Optional[str] = Form(None)
):
    """Upload a file and immediately process it with OCR."""
    try:
        if not multi_agent_system:
            raise HTTPException(status_code=500, detail="Multi-agent system not initialized")
        
        # Validate file type
        allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}{file_ext}"
        file_path = UPLOAD_DIR / safe_filename
        
        # Save uploaded file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Determine file type
        file_type = "pdf" if file_ext == ".pdf" else "image"
        
        # Generate thread_id if not provided
        current_thread_id = thread_id or str(uuid.uuid4())
        current_user_id = user_id or "default_user"
        
        # Process directly with OCR agent
        ocr_agent = multi_agent_system.ocr_agent
        if not ocr_agent:
            raise HTTPException(status_code=500, detail="OCR agent not available")
        
        # Ensure OCR agent is initialized
        if not ocr_agent._tools:
            await ocr_agent.initialize()
        
        # Get the process_document tool
        tools = ocr_agent.get_tools()
        process_tool = None
        for tool in tools:
            # Check if this is the process_document tool by checking name attribute
            tool_name = getattr(tool, 'name', '') or str(tool)
            if 'process_document' in tool_name.lower():
                process_tool = tool
                break
        
        if not process_tool:
            # Fallback: use supervisor to route
            process_message = f"Xử lý file OCR: {str(file_path)} (loại: {file_type})"
            result = await multi_agent_system.process_message(
                process_message,
                thread_id=current_thread_id,
                user_id=current_user_id
            )
        else:
            # Call tool directly - tools accept dict with parameter names
            try:
                result = await process_tool.ainvoke({
                    "file_path": str(file_path),
                    "file_type": file_type
                })
            except Exception as e:
                # If direct call fails, try with supervisor
                print(f"[WARNING] Direct tool call failed: {e}, using supervisor routing")
                process_message = f"Xử lý file OCR: {str(file_path)} (loại: {file_type})"
                result = await multi_agent_system.process_message(
                    process_message,
                    thread_id=current_thread_id,
                    user_id=current_user_id
                )
        
        # Save user message about file upload
        if conversation_service:
            existing_conversation = await conversation_service.get_conversation_by_thread_id(current_thread_id)
            
            if not existing_conversation:
                title = f"OCR: {file.filename}"
                await conversation_service.create_conversation(
                    thread_id=current_thread_id,
                    user_id=current_user_id,
                    title=title
                )
        
        # Extract content from result (remove agent name prefix if present)
        result_content = result
        if isinstance(result, str) and result.startswith("[") and "]" in result:
            result_content = result.split("]", 1)[1].strip()
        
        markdown_filename = f"{Path(file_path).stem}.md"
        markdown_path = OUTPUT_DIR / markdown_filename
        markdown_exists = markdown_path.exists()
        markdown_url = f"/api/ocr/markdown/{markdown_filename}" if markdown_exists else None
        
        return JSONResponse({
            "success": True,
            "file_path": str(file_path),
            "filename": file.filename,
            "file_type": file_type,
            "result": result_content,
            "thread_id": current_thread_id,
            "message": "File processed successfully",
            "markdown_file": markdown_filename if markdown_exists else None,
            "markdown_url": markdown_url
        })
        
    except HTTPException:
        raise
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"[ERROR] Error processing uploaded file: {str(e)}")
        print(f"[ERROR] Traceback:\n{error_traceback}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.websocket("/ws/{client_id}")
@traceable(name="api.websocket_chat")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time chat."""
    await manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if not multi_agent_system:
                await manager.send_personal_message(
                    json.dumps({"error": "Multi-agent system not initialized"}),
                    websocket
                )
                continue
            
            try:
                # Process the message
                response = await multi_agent_system.process_message(
                    message_data.get("content", ""),
                    thread_id=message_data.get("thread_id"),
                    user_id=message_data.get("user_id", client_id)
                )
                
                # Send response back
                await manager.send_personal_message(
                    json.dumps({
                        "content": response,
                        "thread_id": message_data.get("thread_id"),
                        "timestamp": int(datetime.now().timestamp() * 1000)
                    }),
                    websocket
                )
                
            except Exception as e:
                await manager.send_personal_message(
                    json.dumps({"error": f"Error processing message: {str(e)}"}),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Mount static files for React app
import os
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import sys
    # Disable reload on Windows to avoid multiprocessing spawn issues
    # On Windows, reload can cause KeyboardInterrupt during process spawning
    use_reload = sys.platform != "win32"
    uvicorn.run(
        "backend_api:app",
        host="0.0.0.0",
        port=8000,
        reload=use_reload,
        log_level="info"
    )

