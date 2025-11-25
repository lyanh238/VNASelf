"""
Configuration settings for the Multi-Agent System
"""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load .env file from project root (parent directory of backend)
# override=True ensures .env file values take precedence over system environment variables
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path, override=True)

def _clean_env_value(value: str) -> str:
    """Clean environment variable value by removing quotes and whitespace."""
    if not value:
        return value
    # Remove surrounding quotes (single or double)
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    return value.strip()

class Config:
    """Configuration class for the multi-agent system."""
    
    # Model settings
    MODEL_NAME = _clean_env_value(os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    OPENAI_API_KEY = _clean_env_value(os.getenv("OPENAI_API_KEY") or "")
    
    # Timezone settings
    TIMEZONE = "Asia/Ho_Chi_Minh"
    
    # Database settings
    NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")
    
    # Search API settings
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    
    # Google Calendar settings
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # LangSmith settings (optional)
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "x23d8")
    
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
