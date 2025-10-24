
import asyncio
import sys
import os
from typing import Dict, Any, List, TypedDict
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langsmith import Client
from langchain_core.tracers.langchain import LangChainTracer
from typing_extensions import TypedDict
# Import full multi-agents system
from agents import CalendarAgent, SupervisorAgent
from services import MCPService
from services.chat_history_service import LogsService
from core.state_manager import StateManager
from config import Config
from agents.supervisor_agent import SupervisorAgent
# State definition for langgraph dev
class State(TypedDict):
    messages: List[Any]
    current_agent: str
    user_input: str
    response: str

# Initialize full multi-agents system
model = ChatOpenAI(model="gpt-4o-mini")
mcp_service = MCPService()
logs_service = LogsService()
state_manager = StateManager()

# Initialize agents
calendar_agent_instance = CalendarAgent(model, mcp_service)
supervisor_agent = SupervisorAgent(model, calendar_agent_instance)

# Initialize LangSmith tracing
tracer = None
try:
    tracer = LangChainTracer()
except Exception as e:
    print(f"LangChainTracer initialization failed: {e}")
# Initialize services
async def initialize_services():
    """Initialize all services"""
    print("Initializing services...")
    
    try:
        # Initialize logs service
        await logs_service.initialize()
        print("✓ Logs service initialized")
    except Exception as e:
        print(f"⚠ Logs service initialization failed: {e}")
    
    try:
        # Initialize MCP service with calendar server
        print("Initializing MCP service with calendar server...")
        await mcp_service.initialize()
        print("✓ MCP service initialized with calendar server")
        
        # Test calendar tools retrieval
        try:
            calendar_tools = await mcp_service.get_calendar_tools()
            print(f"✓ Successfully loaded {len(calendar_tools)} calendar tools from calendar_server.py")
        except Exception as e:
            print(f"⚠ Failed to load calendar tools: {e}")
            
    except Exception as e:
        print(f"⚠ MCP service initialization failed: {e}")
    
    try:
        # Initialize supervisor agent
        await supervisor_agent.initialize()
        print("✓ Supervisor agent initialized")
    except Exception as e:
        print(f"⚠ Supervisor agent initialization failed: {e}")
    
    try:
        # Initialize calendar agent with MCP tools
        await calendar_agent_instance.initialize()
        print("✓ Calendar agent initialized with MCP tools")
    except Exception as e:
        print(f"⚠ Calendar agent initialization failed: {e}")
    
    print("Service initialization completed!")

# Lazy initialization function
def ensure_services_initialized():
    """Ensure services are initialized when needed"""
    # This will be called by nodes when they need services
    pass

# 1️⃣ Node definitions with full multi-agents system
def input_processor(state: State):
    """Process input messages with logging"""
    print("Input Processor Node activated.")
    
    if state.get("messages"):
        last_message = state["messages"][-1]
        if isinstance(last_message, HumanMessage):
            print(f"Received user message: {last_message.content}")
            
            # Log to database
            if logs_service and logs_service.session:
                asyncio.create_task(logs_service.save_message(
                    thread_id="default_thread",
                    message_type="user_input",
                    content=last_message.content,
                    agent_name="input_processor"
                ))
            
            return {
                "user_input": last_message.content,
                "current_agent": "supervisor"
            }
    
    return state

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

# Dùng model nhỏ, nhanh cho routing
router_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def supervisor(state: State):
    """Supervisor Agent with intelligent intent classification and routing"""
    print("Supervisor Node activated.")
    user_input = state.get("user_input", "").strip()
    
    try:
        # Use supervisor agent for intelligent routing
        current_time = supervisor_agent.get_current_time_iso()
        system_prompt = supervisor_agent.get_system_prompt()
        
        full_prompt = f"{system_prompt}\n\nCurrent time (Asia/Ho_Chi_Minh): {current_time}"
        
        messages = [
            SystemMessage(content=full_prompt),
            HumanMessage(content=user_input)
        ]
        
        print(f"Analyzing user input: {user_input}")
        
        # Use supervisor agent with tools for intelligent routing
        try:
            supervisor_model_with_tools = supervisor_agent.get_supervisor_model()
            response = supervisor_model_with_tools.invoke(messages)
            
            # Extract intent from response content
            response_content = response.content.lower()
            
            # Enhanced intent detection
            if any(keyword in response_content for keyword in ['calendar', 'event', 'meeting', 'schedule', 'appointment', 'reminder', 'time', 'date']):
                intent = "CALENDAR"
            else:
                intent = "GENERAL"
                
        except Exception as e:
            print(f"Supervisor tools error: {e}, falling back to basic classification")
            # Fallback to basic LLM classification
            system_prompt = SystemMessage(content=(
                "You are an intelligent intent classifier. Analyze the user's message and classify it into one of these categories:\n\n"
                "1. CALENDAR - Scheduling, meetings, events, appointments, time, dates, reminders, calendar operations\n"
                "2. GENERAL - General questions, conversations, information, help, greetings, other topics\n\n"
                "Examples:\n"
                "- 'Schedule a meeting tomorrow' → CALENDAR\n"
                "- 'What is the weather?' → GENERAL\n"
                "- 'Create an event' → CALENDAR\n"
                "- 'Hello, how are you?' → GENERAL\n\n"
                "Respond with ONLY one word: CALENDAR or GENERAL"
            ))
            
            human_prompt = HumanMessage(content=user_input)
            response = router_llm.invoke([system_prompt, human_prompt])
            intent = response.content.strip().upper()

        print(f"→ Intent classification: {intent}")

        if intent == "CALENDAR":
            print("   → Routing to Calendar Agent")
            return {"current_agent": "calendar_agent"}
        else:
            print("   → Routing to General Agent")
            return {"current_agent": "general"}

    except Exception as e:
        print(f"Supervisor error: {str(e)}")
        return {"current_agent": "general"}



import asyncio
from langchain_core.messages import SystemMessage, HumanMessage

async def calendar_agent(state: State):
    """Calendar Agent with MCP Google Calendar integration"""
    print("Calendar Agent Node")
    
    user_input = state.get("user_input", "")
    
    try:
        # Ensure MCP service is initialized first
        try:
            await mcp_service.initialize()
            print("✓ MCP service initialized successfully")
        except Exception as e:
            print(f"MCP service initialization failed: {e}")
            return {
                "response": "Không thể kết nối đến Google Calendar. Vui lòng thử lại sau.",
                "current_agent": "calendar_agent"
            }
        
        # Initialize calendar agent with MCP tools
        try:
            await calendar_agent_instance.initialize()
            print("✓ Calendar agent initialized with MCP tools")
        except Exception as e:  
            print(f"Calendar agent initialization failed: {e}")
            return {
                "response": "Không thể khởi tạo calendar agent. Vui lòng thử lại sau.",
                "current_agent": "calendar_agent"
            }
        
        # Use calendar agent's system prompt
        system_prompt = calendar_agent_instance.get_system_prompt()
        current_time = calendar_agent_instance.get_current_time_iso()
        full_prompt = f"{system_prompt}\n\nThời gian hiện tại (Asia/Ho_Chi_Minh): {current_time}"

        messages = [
            SystemMessage(content=full_prompt),
            HumanMessage(content=user_input)
        ]

        # ✅ Non-blocking model invocation with MCP tools
        try:
            calendar_model_with_tools = calendar_agent_instance.model.bind_tools(
                calendar_agent_instance.get_tools()
            )

            # Run blocking model.invoke() in a thread-safe way
            response = await asyncio.to_thread(calendar_model_with_tools.invoke, messages)
            print("✓ Calendar agent used MCP tools successfully")

        except Exception as e:
            print(f"Failed to use MCP tools, fallback to base model: {e}")
            response = await asyncio.to_thread(calendar_agent_instance.model.invoke, messages)

        print(f"Calendar response: {response.content[:100]}...")

        # ✅ Logging non-blocking
        if logs_service and logs_service.session:
            asyncio.create_task(logs_service.save_message(
                thread_id="default_thread",
                message_type="agent_response",
                content=response.content,
                agent_name="calendar_agent"
            ))

        return {
            "response": response.content,
            "current_agent": "calendar_agent"
        }

    except Exception as e:
        print(f"Calendar Agent error: {str(e)}")
        error_response = f"Xin lỗi, tôi gặp lỗi khi xử lý yêu cầu lịch của bạn: {str(e)}"
        return {
            "response": error_response,
            "current_agent": "calendar_agent"
        }


async def mcp_tools(state: State):
    """MCP Tools node for direct Google Calendar operations"""
    print("MCP Tools Node")
    
    user_input = state.get("user_input", "")
    
    try:
        # Ensure MCP service is initialized
        try:
            print("Initializing MCP service with calendar server...")
            await mcp_service.initialize()
            print("✓ MCP service initialized successfully with calendar server")
        except Exception as e:
            print(f"MCP service initialization failed: {e}")
            return {
                "response": "MCP service không khả dụng. Vui lòng thử lại sau.",
                "current_agent": "mcp_tools"
            }
        
        # Get calendar tools from MCP service (calendar_server.py)
        try:
            print("Retrieving calendar tools from MCP server...")
            calendar_tools = await mcp_service.get_calendar_tools()
            print(f"✓ Retrieved {len(calendar_tools)} calendar tools from MCP server")
            
            # List available tools for debugging
            for i, tool in enumerate(calendar_tools, 1):
                print(f"  {i}. {tool.name}: {tool.description[:100]}...")
                
        except Exception as e:
            print(f"Failed to get calendar tools: {e}")
            return {
                "response": "Không thể kết nối đến Google Calendar. Vui lòng thử lại sau.",
                "current_agent": "mcp_tools"
            }
        
        # Use calendar agent's system prompt for consistency
        system_prompt = calendar_agent_instance.get_system_prompt()
        current_time = calendar_agent_instance.get_current_time_iso()
        full_prompt = f"{system_prompt}\n\nThời gian hiện tại (Asia/Ho_Chi_Minh): {current_time}"

        messages = [
            SystemMessage(content=full_prompt),
            HumanMessage(content=user_input)
        ]
        
        # Use calendar agent with MCP tools bound for Google Calendar operations
        try:
            print("Binding MCP calendar tools to model...")
            calendar_model_with_tools = calendar_agent_instance.model.bind_tools(calendar_tools)
            
            # Execute with MCP tools in thread-safe way
            response = await asyncio.to_thread(calendar_model_with_tools.invoke, messages)
            print("✓ MCP tools executed successfully")
            
        except Exception as e:
            print(f"Failed to execute MCP tools: {e}")
            print("Falling back to basic model...")
            # Fallback to basic response
            response = await asyncio.to_thread(calendar_agent_instance.model.invoke, messages)
        
        print(f"MCP Tools response: {response.content[:100]}...")
        
        # Log to database
        if logs_service and logs_service.session:
            asyncio.create_task(logs_service.save_message(
                thread_id="default_thread",
                message_type="mcp_tools_response",
                content=response.content,
                agent_name="mcp_tools"
            ))
        
        return {
            "response": response.content,
            "current_agent": "mcp_tools"
        }
        
    except Exception as e:
        print(f"MCP Tools error: {str(e)}")
        error_response = f"Xin lỗi, tôi gặp lỗi khi xử lý yêu cầu MCP: {str(e)}"
        return {
            "response": error_response,
            "current_agent": "mcp_tools"
        }

def general_agent(state: State):
    """General Agent node with basic response"""
    print("General Agent Node")
    
    user_input = state.get("user_input", "")
    
    try:
        # Use model for general response
        messages = [
            SystemMessage(content="Bạn là một AI assistant hữu ích. Hãy trả lời câu hỏi một cách thân thiện và hữu ích."),
            HumanMessage(content=user_input)
        ]
        
        response = model.invoke(input=messages)
        
        print(f"   General response: {response.content[:100]}...")
        
        # Log to database
        if logs_service and logs_service.session:
            asyncio.create_task(logs_service.save_message(
                thread_id="default_thread",
                message_type="agent_response",
                content=response.content,
                agent_name="general_agent"
            ))
        
        return {
            "response": response.content,
            "current_agent": "general"
        }
        
    except Exception as e:
        print(f"General Agent error: {str(e)}")
        error_response = f"Xin lỗi, tôi gặp lỗi khi xử lý yêu cầu của bạn: {str(e)}"
        return {
            "response": error_response,
            "current_agent": "general"
        }

def response_formatter(state: State):
    """Format the final response with logging"""
    print("Response Formatter Node")
    
    response = state.get("response", "Không có phản hồi.")
    current_agent = state.get("current_agent", "unknown")
    
    formatted_response = f"[{current_agent.upper()}] {response}"
    print(f"   Formatted response: {formatted_response[:100]}...")
                
    # Log final response to database
    if logs_service and logs_service.session:
        asyncio.create_task(logs_service.save_message(
            thread_id="default_thread",
            message_type="final_response",
            content=formatted_response,
            agent_name="response_formatter"
        ))
    
        return {
        "response": formatted_response
    }

def router_condition(state: State):
    """Router condition based on current agent"""
    current_agent = state.get("current_agent", "general")
    
    if current_agent == "calendar_agent":
        return "calendar_agent"
    elif current_agent == "mcp_tools":
        return "mcp_tools"
    else:
        return "general_agent"

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

intent_model = ChatOpenAI(model="gpt-4o-mini")

def calendar_router_condition(state: State):
    """Router condition using LLM-based intent classification for calendar operations"""
    user_input = state.get("user_input", "")

    # Enhanced intent detection for calendar operations
    calendar_operation_keywords = [
        'tạo', 'create', 'schedule', 'đặt lịch', 'lịch hẹn', 'cuộc họp', 'meeting',
        'cập nhật', 'update', 'sửa', 'edit', 'thay đổi', 'change',
        'xóa', 'delete', 'hủy', 'cancel', 'remove',
        'di chuyển', 'move', 'dời', 'reschedule', 'postpone',
        'kiểm tra', 'check', 'xem lịch', 'view calendar', 'availability',
        'tìm kiếm', 'search', 'find', 'look for'
    ]
    
    # Check if user input contains calendar operation keywords
    user_input_lower = user_input.lower()
    has_calendar_operation = any(keyword in user_input_lower for keyword in calendar_operation_keywords)
    
    if has_calendar_operation:
        print("   → Routing to MCP Tools for calendar operation")
        return "mcp_tools"
    else:
        print("   → Routing to Response Formatter for general response")
        return "response_formatter"

        
# 2️⃣ Create builder with state manager
builder = StateGraph(State)

# 3️⃣ Add nodes
builder.add_node("input_processor", input_processor)
builder.add_node("supervisor", supervisor)
builder.add_node("calendar_agent", calendar_agent)
builder.add_node("mcp_tools", mcp_tools)
builder.add_node("general_agent", general_agent)
builder.add_node("response_formatter", response_formatter)

builder.add_edge(START, "input_processor")
builder.add_edge("input_processor", "supervisor")
builder.add_conditional_edges(
            "supervisor",
            router_condition,
            {
                "calendar_agent": "calendar_agent", 
                "general_agent": "general_agent"
            }
        )
builder.add_conditional_edges(
    "calendar_agent",
    calendar_router_condition,
    {
        "mcp_tools": "mcp_tools",
        "response_formatter": "response_formatter"
    }
)
builder.add_edge("mcp_tools", "response_formatter")
builder.add_edge("general_agent", "response_formatter")
builder.add_edge("response_formatter", END)

# 5️⃣ Compile with state manager and tracing
graph = builder.compile()



