"""
LangGraph Visualization for LangSmith
Tạo sơ đồ hoạt động của Multi-Agent System
"""

import asyncio
import sys
import os
from typing import Dict, Any, List
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import Client
from langchain_core.tracers.langchain import LangChainTracer
from agents import HealthAgent, CalendarAgent, SupervisorAgent
from services import MCPService
from services.chat_history_service import LogsService
from core.state_manager import StateManager
from config import Config


class VisualizedMultiAgentSystem:
    """Multi-Agent System với visualization cho LangSmith."""
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model = ChatOpenAI(model=model_name)
        self.mcp_service = MCPService()
        self.logs_service = LogsService()
        self.state_manager = StateManager()
        
        # Initialize agents
        self.health_agent = HealthAgent(self.model)
        self.calendar_agent = CalendarAgent(self.model, self.mcp_service)
        self.supervisor_agent = SupervisorAgent(self.model, self.health_agent, self.calendar_agent)
        
        self.graph = None
        self._initialized = False
        
        # LangSmith client for visualization
        self.langsmith_client = None
        self.tracer = None
    
    async def initialize(self):
        """Initialize the visualized multi-agent system."""
        if self._initialized:
            return
        
        print(" Initializing Visualized Multi-Agent System...")
        
        # Initialize LangSmith
        try:
            self.langsmith_client = Client()
            self.tracer = LangChainTracer()
            print("✓ LangSmith client initialized")
        except Exception as e:
            print(f"⚠ LangSmith not available: {str(e)}")
        
        # Initialize services
        await self.logs_service.initialize()
        await self.mcp_service.initialize()
        await self.supervisor_agent.initialize()
        
        # Build the graph with detailed nodes
        await self._build_visualized_graph()
        
        self._initialized = True
        print("✓ Visualized Multi-Agent System initialized!")
    
    async def _build_visualized_graph(self):
        """Build a detailed LangGraph for visualization."""
        builder = StateGraph(MessagesState)
        
        # Get supervisor model with tools
        supervisor_model = self.supervisor_agent.get_supervisor_model()
        
        def input_processor_node(state: MessagesState):
            """Node xử lý input và log vào database."""
            print(" Input Processor Node")
            
            # Log user input
            if state["messages"]:
                last_message = state["messages"][-1]
                if isinstance(last_message, HumanMessage):
                    print(f"   User input: {last_message.content[:50]}...")
            
            return state
        
        def supervisor_node(state: MessagesState):
            """Supervisor node quyết định agent nào xử lý."""
            print(" Supervisor Node")
            
            system_prompt = self.supervisor_agent.get_system_prompt()
            current_time = self.supervisor_agent.get_current_time_iso()
            
            full_prompt = f"{system_prompt}\n\nCurrent time (Asia/Ho_Chi_Minh): {current_time}"
            
            # Add system message for context
            messages = [
                SystemMessage(content=full_prompt)
            ] + state["messages"]
            
            response = supervisor_model.invoke(messages)
            
            print(f"   Supervisor decision: {response.content[:100]}...")
            
            return {
                "messages": state["messages"] + [response]
            }
        
        def health_agent_node(state: MessagesState):
            """Health Agent node xử lý câu hỏi sức khỏe."""
            print(" Health Agent Node")
            
            # Get last user message
            user_message = None
            for msg in reversed(state["messages"]):
                if isinstance(msg, HumanMessage):
                    user_message = msg.content
                    break
            
            if user_message:
                # Use health consultation tool
                response = self.health_agent.health_consultation_tool(user_message)
                print(f"   Health response: {response[:100]}...")
                
                from langchain_core.messages import AIMessage
                return {
                    "messages": state["messages"] + [
                        AIMessage(content=response, additional_kwargs={"agent": "health_agent"})
                    ]
                }
            
            return state
        
        def calendar_agent_node(state: MessagesState):
            """Calendar Agent node xử lý câu hỏi lịch."""
            print(" Calendar Agent Node")
            
            # Get last user message
            user_message = None
            for msg in reversed(state["messages"]):
                if isinstance(msg, HumanMessage):
                    user_message = msg.content
                    break
            
            if user_message:
                # Use calendar tools
                try:
                    # This would normally use MCP tools
                    response = f"Calendar response for: {user_message[:50]}..."
                    print(f"   Calendar response: {response[:100]}...")
                    
                    from langchain_core.messages import AIMessage
                    return {
                        "messages": state["messages"] + [
                            AIMessage(content=response, additional_kwargs={"agent": "calendar_agent"})
                        ]
                    }
                except Exception as e:
                    print(f"   Calendar error: {str(e)}")
                    return state
            
            return state
        
        def response_formatter_node(state: MessagesState):
            """Node format response cuối cùng."""
            print(" Response Formatter Node")
            
            # Get the last AI message
            last_message = state["messages"][-1]
            if hasattr(last_message, 'content'):
                formatted_response = f" Assistant: {last_message.content}"
                print(f"   Formatted response: {formatted_response[:100]}...")
                
                from langchain_core.messages import AIMessage
                return {
                    "messages": state["messages"] + [
                        AIMessage(content=formatted_response, additional_kwargs={"formatted": True})
                    ]
                }
            
            return state
        
        def router_condition(state: MessagesState):
            """Router quyết định node tiếp theo dựa trên nội dung."""
            last_message = state["messages"][-1]
            
            if hasattr(last_message, 'content'):
                content = last_message.content.lower()
                
                # Health-related keywords
                health_keywords = ['đau', 'sốt', 'bệnh', 'sức khỏe', 'triệu chứng', 'thuốc', 'bác sĩ']
                if any(keyword in content for keyword in health_keywords):
                    print("   → Routing to Health Agent")
                    return "health_agent"
                
                # Calendar-related keywords
                calendar_keywords = ['lịch', 'calendar', 'sự kiện', 'họp', 'meeting', 'appointment']
                if any(keyword in content for keyword in calendar_keywords):
                    print("   → Routing to Calendar Agent")
                    return "calendar_agent"
            
            print("   → Routing to Response Formatter")
            return "response_formatter"
        
        # Add nodes with detailed descriptions
        builder.add_node("input_processor", input_processor_node)
        builder.add_node("supervisor", supervisor_node)
        builder.add_node("health_agent", health_agent_node)
        builder.add_node("calendar_agent", calendar_agent_node)
        builder.add_node("response_formatter", response_formatter_node)
        builder.add_node("tools", ToolNode(self.supervisor_agent.get_tools()))
        
        # Add edges
        builder.add_edge(START, "input_processor")
        builder.add_edge("input_processor", "supervisor")
        builder.add_conditional_edges(
            "supervisor",
            router_condition,
            {
                "health_agent": "health_agent",
                "calendar_agent": "calendar_agent", 
                "response_formatter": "response_formatter",
                "tools": "tools"
            }
        )
        builder.add_edge("health_agent", "response_formatter")
        builder.add_edge("calendar_agent", "response_formatter")
        builder.add_edge("tools", "supervisor")
        builder.add_edge("response_formatter", END)
        
        # Compile graph
        self.graph = builder.compile(checkpointer=self.state_manager.get_memory())
        print("✓ Visualized graph built successfully!")
        from IPython.display import display, Image
        from PIL import Image as PILImage
        import io

        display(Image(self.graph.get_graph().draw_mermaid_png()))
        img_data = self.graph.get_graph().draw_mermaid_png()
        image = PILImage.open(io.BytesIO(img_data))
        image.show()
    
    async def process_message_with_visualization(
        self, 
        message: str, 
        thread_id: str = None, 
        user_id: str = None
    ) -> str:
        """Process message với LangSmith tracing."""
        if not self._initialized:
            await self.initialize()
        
        # Use provided thread_id or current one
        config = self.state_manager.get_config()
        if thread_id:
            config["configurable"]["thread_id"] = thread_id
        
        # Add LangSmith tracing
        if self.tracer:
            config["callbacks"] = [self.tracer]
        
        print(f"\n Processing message: {message[:50]}...")
        print(f"   Thread ID: {thread_id or config['configurable']['thread_id']}")
        print(f"   User ID: {user_id or 'anonymous'}")
        
        # Process the message
        result = await self.graph.ainvoke(
            {"messages": [HumanMessage(content=message)]},
            config=config
        )
        
        # Get the last message (agent's response)
        response = result["messages"][-1].content
        
        # Log to database
        current_timestamp = int(datetime.now().timestamp() * 1000)
        await self.logs_service.save_message(
            thread_id=thread_id or config["configurable"]["thread_id"],
            message_type="user",
            content=message,
            user_id=user_id,
            timestamp=current_timestamp
        )
        
        await self.logs_service.save_message(
            thread_id=thread_id or config["configurable"]["thread_id"],
            message_type="assistant",
            content=response,
            agent_name="Multi-Agent System",
            user_id=user_id,
            timestamp=current_timestamp + 1
        )
        
        print(f" Response generated: {response[:100]}...")
        return response
    
    def get_graph_representation(self) -> Dict[str, Any]:
        """Get graph representation for visualization."""
        if not self.graph:
            return {}
        
        return {
            "nodes": [
                {
                    "id": "input_processor",
                    "label": "Input Processor",
                    "type": "input",
                    "description": "Processes user input and logs to database"
                },
                {
                    "id": "supervisor",
                    "label": "Supervisor Agent",
                    "type": "decision",
                    "description": "Decides which agent should handle the request"
                },
                {
                    "id": "health_agent",
                    "label": "Health Agent",
                    "type": "agent",
                    "description": "Handles health-related questions and consultations"
                },
                {
                    "id": "calendar_agent",
                    "label": "Calendar Agent",
                    "type": "agent",
                    "description": "Manages calendar operations and events"
                },
                {
                    "id": "tools",
                    "label": "Tools",
                    "type": "tools",
                    "description": "Executes specific tools and functions"
                },
                {
                    "id": "response_formatter",
                    "label": "Response Formatter",
                    "type": "output",
                    "description": "Formats the final response"
                }
            ],
            "edges": [
                {"from": "input_processor", "to": "supervisor"},
                {"from": "supervisor", "to": "health_agent", "condition": "health_related"},
                {"from": "supervisor", "to": "calendar_agent", "condition": "calendar_related"},
                {"from": "supervisor", "to": "tools", "condition": "tool_required"},
                {"from": "supervisor", "to": "response_formatter", "condition": "direct_response"},
                {"from": "health_agent", "to": "response_formatter"},
                {"from": "calendar_agent", "to": "response_formatter"},
                {"from": "tools", "to": "supervisor"}
            ],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "version": "1.0.0",
                "description": "Multi-Agent System with Health and Calendar capabilities"
            }
        }
    
    async def close(self):
        """Close the system."""
        await self.mcp_service.close()
        await self.logs_service.close()
        print("✓ Visualized Multi-Agent System closed.")


async def demo_visualization():
    """Demo the visualization system."""
    print(" LangGraph Visualization Demo")
    print("=" * 60)
    
    # Initialize system
    system = VisualizedMultiAgentSystem()
    
    try:
        await system.initialize()
        
        # Demo queries
        demo_queries = [
            "Tôi bị đau đầu và sốt, phải làm sao?",
            "Show me my calendar for today",
            "What's the weather like?",
            "Tạo cuộc họp lúc 2 giờ chiều mai"
        ]
        
        for i, query in enumerate(demo_queries, 1):
            print(f"\n{'='*20} Query {i} {'='*20}")
            response = await system.process_message_with_visualization(
                query, 
                thread_id=f"demo_thread_{i}",
                user_id="demo_user"
            )
            print(f"Final Response: {response}")
        
        # Show graph representation
        print(f"\n Graph Representation:")
        graph_repr = system.get_graph_representation()
        print(f"Nodes: {len(graph_repr.get('nodes', []))}")
        print(f"Edges: {len(graph_repr.get('edges', []))}")
        
        for node in graph_repr.get('nodes', []):
            print(f"  - {node['id']}: {node['description']}")
        
    except Exception as e:
        print(f" Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await system.close()


if __name__ == "__main__":
    print(" Starting LangGraph Visualization Demo")
    print("Make sure you have set LANGCHAIN_API_KEY for LangSmith")
    print()
    
    asyncio.run(demo_visualization())
