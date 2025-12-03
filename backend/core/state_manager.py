"""
State Manager for the multi-agent system
"""

from typing import Dict, Any
from langgraph.checkpoint.memory import MemorySaver


class StateManager:
    """Manages state and memory for the multi-agent system."""
    
    def __init__(self):
        self.memory = MemorySaver()
        self.current_thread_id = "01"
    
    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration for the agent system."""
        return {
            "configurable": {
                "thread_id": self.current_thread_id
            }
        }
    
    def create_new_thread(self) -> str:
        """Create a new conversation thread."""
        self.current_thread_id = str(int(self.current_thread_id) + 1)
        return self.current_thread_id
    
    def get_memory(self) -> MemorySaver:
        """Get the memory saver instance."""
        return self.memory
