"""
Multi-Agent System orchestrator
"""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from agents import HealthAgent, CalendarAgent, SupervisorAgent
from services import MCPService
from .state_manager import StateManager


class MultiAgentSystem:
    """Main orchestrator for the multi-agent system."""
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model = ChatOpenAI(model=model_name)
        self.mcp_service = MCPService()
        self.state_manager = StateManager()
        
        # Initialize agents
        self.health_agent = HealthAgent(self.model)
        self.calendar_agent = CalendarAgent(self.model, self.mcp_service)
        self.supervisor_agent = SupervisorAgent(self.model, self.health_agent, self.calendar_agent)
        
        self.graph = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the multi-agent system."""
        if self._initialized:
            return
        
        print(" Initializing Multi-Agent System...")
        
        # Initialize MCP service
        await self.mcp_service.initialize()
        
        # Initialize supervisor agent (which initializes calendar agent)
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
    
    async def process_message(self, message: str, thread_id: Optional[str] = None) -> str:
        """Process a message through the multi-agent system."""
        if not self._initialized:
            await self.initialize()
        
        # Use provided thread_id or current one
        config = self.state_manager.get_config()
        if thread_id:
            config["configurable"]["thread_id"] = thread_id
        
        # Process the message
        result = await self.graph.ainvoke(
            {"messages": [HumanMessage(content=message)]},
            config=config
        )
        
        # Get the last message (agent's response)
        response = result["messages"][-1].content
        return response
    
    async def chat_interactive(self):
        """Start interactive chat session."""
        if not self._initialized:
            await self.initialize()
        
        print("=" * 60)
        print(" Multi-Agent System (Health + Calendar)")
        print("=" * 60)
        print("Special commands:")
        print("  - 'exit' or 'quit': Exit")
        print("  - 'clear': Clear chat history")
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
                
                # Process the message
                print("\ Processing...\n")
                response = await self.process_message(user_input)
                print(f"Assistant: {response}\n")
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
                "name": "Health Consultation",
                "query": "I have a headache and mild fever, what should I do?"
            },
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
        print(" Multi-Agent System closed.")
