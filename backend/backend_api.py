"""
Backend API for React frontend integration with Multi-Agent System
"""

import asyncio
import json
import uuid
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

from core import MultiAgentSystem

# Initialize FastAPI app
app = FastAPI(title="VNASelf API", version="1.0.0")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global multi-agent system instance
multi_agent_system = None

# Account file path
ACCOUNT_FILE_PATH = "account.json"

# Pydantic models
class ChatMessage(BaseModel):
    content: str
    thread_id: Optional[str] = None
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    content: str
    agent_name: str
    thread_id: str
    timestamp: int

class ChatHistory(BaseModel):
    thread_id: str
    messages: List[Dict[str, Any]]

class ThreadSummary(BaseModel):
    thread_id: str
    title: str
    last_message: str
    timestamp: int

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

@app.on_event("startup")
async def startup_event():
    """Initialize the multi-agent system on startup."""
    global multi_agent_system
    try:
        multi_agent_system = MultiAgentSystem()
        await multi_agent_system.initialize()
        print("[OK] Multi-Agent System initialized successfully!")
    except Exception as e:
        print(f"[ERROR] Error initializing Multi-Agent System: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global multi_agent_system
    if multi_agent_system:
        await multi_agent_system.close()

@app.get("/")
async def root():
    """Serve the React app."""
    return FileResponse("../frontend/dist/index.html")

@app.post("/api/chat", response_model=ChatResponse)
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
            user_id=user_id
        )
        
        # Extract agent name from response
        agent_name = "Assistant"
        if response.startswith("[") and "]" in response:
            agent_name = response.split("]")[0][1:]
            response = response.split("]", 1)[1].strip()
        
        return ChatResponse(
            content=response,
            agent_name=agent_name,
            thread_id=thread_id,
            timestamp=int(datetime.now().timestamp() * 1000)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.get("/api/chat/history/{thread_id}", response_model=ChatHistory)
async def get_chat_history(thread_id: str, limit: int = 50):
    """Get chat history for a specific thread."""
    if not multi_agent_system:
        raise HTTPException(status_code=500, detail="Multi-agent system not initialized")
    
    try:
        messages = await multi_agent_system.get_chat_history(thread_id, limit)
        return ChatHistory(thread_id=thread_id, messages=messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting chat history: {str(e)}")

@app.get("/api/chat/threads/{user_id}", response_model=List[ThreadSummary])
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

@app.websocket("/ws/{client_id}")
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
app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(
        "backend_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

