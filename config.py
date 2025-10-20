"""
Configuration settings for the Multi-Agent System
"""

import os
from typing import Dict, Any


class Config:
    """Configuration class for the multi-agent system."""
    
    # Model settings
    MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Timezone settings
    TIMEZONE = "Asia/Ho_Chi_Minh"
    
    # MCP settings
    MCP_SERVER_CONFIG = {
        "google_calendar": {
            "command": "python",
            "args": ["calendar_server.py"],
            "transport": "stdio",
        }
    }
    
    # System settings
    MAX_TOOLS_PER_AGENT = 10
    DEFAULT_THREAD_ID = "01"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration."""
        if not cls.OPENAI_API_KEY:
            print(" Error: OPENAI_API_KEY environment variable not set")
            return False
        return True
    
    @classmethod
    def get_model_config(cls) -> Dict[str, Any]:
        """Get model configuration."""
        return {
            "model": cls.MODEL_NAME,
            "api_key": cls.OPENAI_API_KEY
        }
