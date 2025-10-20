"""
Base Agent class for the multi-agent system
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
import pytz
from datetime import datetime


class BaseAgent(ABC):
    """Base class for all agents in the multi-agent system."""
    
    def __init__(self, model: ChatOpenAI, timezone: str = "Asia/Ho_Chi_Minh"):
        self.model = model
        self.timezone = pytz.timezone(timezone)
        self.name = self.__class__.__name__
    
    def get_current_time_iso(self) -> str:
        """Get current time in ISO format for Vietnam timezone."""
        return datetime.now(self.timezone).isoformat()
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass
    
    @abstractmethod
    def get_tools(self) -> List[Any]:
        """Get the tools available to this agent."""
        pass
    
    def process_message(self, message: str) -> str:
        """Process a message and return a response."""
        system_prompt = self.get_system_prompt()
        current_time = self.get_current_time_iso()
        
        full_prompt = f"{system_prompt}\n\nCurrent time (Asia/Ho_Chi_Minh): {current_time}"
        
        response = self.model.invoke([
            {"role": "system", "content": full_prompt},
            {"role": "user", "content": message}
        ])
        
        return response.content
