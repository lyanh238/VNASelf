"""
Backend API for React frontend integration with Multi-Agent System
"""

import asyncio
import json
import uuid
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
    message_count: int

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
    return FileResponse("deploy/dist/index.html")

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
app.mount("/", StaticFiles(directory="deploy/dist", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(
        "backend_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

