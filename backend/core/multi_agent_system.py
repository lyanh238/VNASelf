"""
Multi-Agent System orchestrator
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from agents import CalendarAgent, SupervisorAgent, FinanceAgent, SearchAgent, NoteAgent
from services import MCPService
from services.chat_history_service import LogsService
from services.conversation_service import ConversationService
from services.conversation_title_service import ConversationTitleService
from services.per_conversation_storage_service import PerConversationStorageService
from services.payment_history_service import PaymentHistoryService
from services.note_service import NoteService
from services.note_storage_service import NoteStorageService
from .state_manager import StateManager


class MultiAgentSystem:
    """Main orchestrator for the multi-agent system."""

    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model = ChatOpenAI(model=model_name)
        self.mcp_service = MCPService()
        self.logs_service = LogsService()
        self.conversation_service = ConversationService()
        self.conversation_title_service = ConversationTitleService()
        self.per_conversation_storage = PerConversationStorageService()
        self.payment_service = PaymentHistoryService()
        self.note_db_service = NoteService()
        self.note_storage_service = NoteStorageService()
        self.state_manager = StateManager()
        
        # Initialize agents
        self.calendar_agent = CalendarAgent(self.model, self.mcp_service)
        self.finance_agent = FinanceAgent(self.model, self.payment_service)
        self.search_agent = SearchAgent(self.model)
        self.note_agent = NoteAgent(self.model, self.note_db_service)
        self.supervisor_agent = SupervisorAgent(self.model, self.calendar_agent, self.finance_agent, self.search_agent, self.note_agent)
        
        self.graph = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the multi-agent system with parallel initialization."""
        if self._initialized:
            return
        
        print(" Initializing Multi-Agent System...")
        
        # Initialize services in parallel for better performance
        import asyncio
        await asyncio.gather(
            self.logs_service.initialize(),
            self.conversation_service.initialize(),
            self.conversation_title_service.initialize(),
            self.per_conversation_storage.initialize(),
            self.payment_service.initialize(),
            self.note_db_service.initialize(),
            self.note_storage_service.initialize(),
            self.mcp_service.initialize(),
            return_exceptions=True  # Don't fail if one service fails
        )
        
        # Initialize supervisor agent (which initializes calendar and finance agents)
        await self.supervisor_agent.initialize()
        
        # Build the graph
        await self._build_graph()
        
        self._initialized = True
        print(" Multi-Agent System initialized successfully!")
    
    async def _build_graph(self):
        """Build the LangGraph for the multi-agent system."""
        builder = StateGraph(MessagesState)
        
        # Get supervisor model with tools
        supervisor_model = self.supervisor_agent.get_supervisor_model()
        
        def supervisor_node(state: MessagesState):
            """Supervisor node that decides which tool to use."""
            system_prompt = self.supervisor_agent.get_system_prompt()
            current_time = self.supervisor_agent.get_current_time_iso()
            
            full_prompt = f"{system_prompt}\n\nCurrent time (Asia/Ho_Chi_Minh): {current_time}"
            
            return {
                "messages": [supervisor_model.invoke([
                    {"role": "system", "content": full_prompt}
                ] + state["messages"])]
            }
        
        # Add nodes
        builder.add_node("supervisor", supervisor_node)
        builder.add_node("tools", ToolNode(self.supervisor_agent.get_tools()))
        
        # Add edges
        builder.add_edge(START, "supervisor")
        builder.add_conditional_edges("supervisor", tools_condition)
        builder.add_edge("tools", "supervisor")
        builder.add_edge("supervisor", END)
        
        # Compile graph
        self.graph = builder.compile(checkpointer=self.state_manager.get_memory())
        print(" Agent graph built successfully!")
    
    async def process_message(self, message: str, thread_id: Optional[str] = None, user_id: Optional[str] = None, model_name: Optional[str] = None) -> str:
        """Process a message through the multi-agent system."""
        if not self._initialized:
            await self.initialize()
        
        # Update model if model_name is provided
        if model_name and model_name != self.model.model_name:
            self.model = ChatOpenAI(model=model_name)
            # Re-initialize agents with new model
            await self.initialize()
        
        # Use provided thread_id or current one
        config = self.state_manager.get_config()
        if thread_id:
            config["configurable"]["thread_id"] = thread_id
        
        # Save user message to both logs and per-conversation storage
        current_timestamp = int(datetime.now().timestamp() * 1000)
        current_thread_id = thread_id or config["configurable"]["thread_id"]
        
        # Get user name from user_id (assuming user_id is email or contains name info)
        user_name = user_id if user_id and user_id != "default_user" else "You"
        
        # Save to logs service (for backward compatibility)
        await self.logs_service.save_message(
            thread_id=current_thread_id,
            message_type="user",
            content=message,
            user_id=user_id,
            metadata={"timestamp": datetime.now().isoformat(), "user_name": user_name},
            timestamp=current_timestamp
        )
        
        # Save to per-conversation storage
        await self.per_conversation_storage.save_message(
            thread_id=current_thread_id,
            message_type="user",
            content=message,
            user_id=user_id,
            metadata={"timestamp": datetime.now().isoformat(), "user_name": user_name},
            timestamp=current_timestamp
        )
        
        # Process the message
        result = await self.graph.ainvoke(
            {"messages": [HumanMessage(content=message)]},
            config=config
        )
        
        # Get the last message (agent's response)
        response = result["messages"][-1].content
        
        # Determine which agent handled the response by analyzing the response content and tool usage
        agent_name = "Supervisor Agent"  # Default
        
        # Check if any tools were called by looking at the conversation flow
        tool_calls_found = False
        for message in result["messages"]:
            if hasattr(message, 'additional_kwargs') and 'tool_calls' in message.additional_kwargs:
                tool_calls = message.additional_kwargs.get('tool_calls', [])
                if tool_calls:
                    tool_calls_found = True
                    tool_name = tool_calls[0].get('function', {}).get('name', '')
                    
                    # Check for finance tools
                    if any(fin_tool in tool_name.lower() for fin_tool in ['add_expense', 'get_expense', 'delete_expense', 'update_expense', 'get_total_spending']):
                        agent_name = "Finance Agent"
                        break
                    # Check for calendar tools
                    elif any(cal_tool in tool_name.lower() for cal_tool in ['list_upcoming_events', 'create_event', 'get_events', 'delete_event', 'update_event', 'move_event']):
                        agent_name = "Calendar Agent"
                        break
                    # Check for search tools
                    elif any(search_tool in tool_name.lower() for search_tool in ['tavily_search', 'mock_search']):
                        agent_name = "Search Agent"
                        break
                    # Check for note tools
                    elif any(note_tool in tool_name.lower() for note_tool in ['record_note', 'list_notes']):
                        agent_name = "Note Agent"
                        break
        
        # If no tool calls found, try to determine from response content
        if not tool_calls_found:
            response_lower = response.lower()
            if any(keyword in response_lower for keyword in ['chi tiêu', 'expense', 'vnd', 'tổng chi tiêu', 'lịch sử chi tiêu']):
                agent_name = "Finance Agent"
            elif any(keyword in response_lower for keyword in ['lịch', 'sự kiện', 'event', 'calendar', 'thời gian']):
                agent_name = "Calendar Agent"
            elif any(keyword in response_lower for keyword in ['tìm kiếm web', 'kết quả tìm kiếm', 'nguồn tin', 'tavily']):
                agent_name = "Search Agent"
            elif any(keyword in response_lower for keyword in ['ghi chú', 'note', 'recorded note', 'đã lưu ghi chú']):
                agent_name = "Note Agent"
        
        # Format response with agent information
        formatted_response = f"[{agent_name}] {response}"
        
        # Save assistant response to both logs and per-conversation storage
        await self.logs_service.save_message(
            thread_id=current_thread_id,
            message_type="assistant",
            content=response,
            agent_name=agent_name,
            user_id=user_id,
            metadata={"timestamp": datetime.now().isoformat()},
            timestamp=current_timestamp + 1  # Slightly after user message
        )
        
        # Save to per-conversation storage
        await self.per_conversation_storage.save_message(
            thread_id=current_thread_id,
            message_type="assistant",
            content=response,
            agent_name=agent_name,
            user_id=user_id,
            metadata={"timestamp": datetime.now().isoformat()},
            timestamp=current_timestamp + 1
        )
        
        return formatted_response
    
    async def get_chat_history(self, thread_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation logs for a thread using per-conversation storage."""
        try:
            # Try to get from per-conversation storage first
            messages = await self.per_conversation_storage.get_conversation_messages(thread_id, limit)
            if messages:
                return messages
            
            # Fallback to logs service if per-conversation storage is empty
            messages = await self.logs_service.get_chat_history(thread_id, limit)
            return [msg.to_dict() for msg in messages]
            
        except Exception as e:
            print(f"Error getting chat history: {str(e)}")
            return []
    
    async def get_all_conversation_messages(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a conversation (no pagination)."""
        try:
            # Try to get from per-conversation storage first
            messages = await self.per_conversation_storage.get_all_conversation_messages(thread_id)
            if messages:
                return messages
            
            # Fallback to logs service if per-conversation storage is empty
            messages = await self.logs_service.get_chat_history(thread_id, limit=1000)  # Large limit
            return [msg.to_dict() for msg in messages]
            
        except Exception as e:
            print(f"Error getting all conversation messages: {str(e)}")
            return []
    
    async def get_user_chat_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get conversation logs for a specific user."""
        messages = await self.logs_service.get_user_chat_history(user_id, limit)
        return [msg.to_dict() for msg in messages]
    
    async def get_user_threads(self, user_id: str) -> List[str]:
        """Get all thread IDs for a user."""
        return await self.logs_service.get_threads_for_user(user_id)
    
    async def delete_thread(self, thread_id: str) -> bool:
        """Delete a conversation thread from both storage systems."""
        try:
            # Delete from logs service
            logs_deleted = await self.logs_service.delete_thread(thread_id)
            
            # Delete from per-conversation storage
            per_conversation_deleted = await self.per_conversation_storage.delete_conversation_messages(thread_id)
            
            return logs_deleted or per_conversation_deleted
            
        except Exception as e:
            print(f"Error deleting thread: {str(e)}")
            return False
    
    async def chat_interactive(self, user_id: Optional[str] = None):
        """Start interactive chat session."""
        if not self._initialized:
            await self.initialize()
        
        print("=" * 60)
        print(" Multi-Agent System (Calendar)")
        print("=" * 60)
        print("Special commands:")
        print("  - 'exit' or 'quit': Exit")
        print("  - 'clear': Clear chat history")
        print("  - 'history': Show recent conversation")
        print("  - 'threads': Show your conversation threads")
        print("=" * 60)
        print()
        
        while True:
            try:
                # Get user input
                user_input = input(" You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'thoát']:
                    print("\n Goodbye! See you next time!")
                    break
                
                if user_input.lower() == 'clear':
                    self.state_manager.create_new_thread()
                    print("\n Chat history cleared. Starting new conversation!\n")
                    continue
                
                if user_input.lower() == 'history':
                    # Show recent conversation
                    config = self.state_manager.get_config()
                    thread_id = config["configurable"]["thread_id"]
                    history = await self.get_chat_history(thread_id, limit=5)
                    print(f"\nNekAssist Recent conversation ({len(history)} messages):")
                    for msg in history:
                        role = " You" if msg["message_type"] == "user" else f"NekAssist {msg['agent_name'] or 'Assistant'}"
                        print(f"{role}: {msg['content']}")
                    print()
                    continue
                
                if user_input.lower() == 'threads' and user_id:
                    # Show user's threads
                    threads = await self.get_user_threads(user_id)
                    print(f"\n Your conversation threads ({len(threads)} threads):")
                    for i, thread in enumerate(threads, 1):
                        print(f"  {i}. {thread}")
                    print()
                    continue
                
                # Process the message
                print("\ Processing...\n")
                response = await self.process_message(user_input, user_id=user_id)
                print(f"{response}\n")
                print("-" * 60)
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\n Error: {str(e)}\n")
    
    async def run_examples(self):
        """Run example queries to demonstrate functionality."""
        if not self._initialized:
            await self.initialize()
        
        print("\n" + "=" * 60)
        print(" RUNNING EXAMPLES")
        print("=" * 60 + "\n")
        
        examples = [
            {
                "name": "View Upcoming Events",
                "query": "Show me the next 5 events in my calendar"
            },
            {
                "name": "Create New Event",
                "query": "Create a meeting 'Team Meeting' on 2025-10-25 from 14:00 to 15:00"
            },
            {
                "name": "Search Events",
                "query": "Find events with 'meeting' in the title"
            }
        ]
        
        for i, example in enumerate(examples, 1):
            print(f"\n[{i}/{len(examples)}] {example['name']}")
            print(f"Query: {example['query']}")
            print()
            
            try:
                response = await self.process_message(example["query"])
                print(f"Response: {response}")
            except Exception as e:
                print(f"Error: {str(e)}")
            
            print("-" * 60)
            
            # Reset thread for next example
            self.state_manager.create_new_thread()
    
    async def close(self):
        """Close the system and cleanup resources."""
        await self.mcp_service.close()
        await self.logs_service.close()
        await self.payment_service.close()
        await self.note_db_service.close()
        print(" Multi-Agent System closed.")
