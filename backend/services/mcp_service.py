"""
MCP Service for managing Google Calendar MCP client
"""

from typing import List, Any
from langchain_mcp_adapters.client import MultiServerMCPClient
import os

class MCPService:
    """Service for managing MCP client connections and tools."""
    
    def __init__(self):
        self.client = None
        self._calendar_tools = None
    
    async def initialize(self):
        """Initialize the MCP client."""
        if self.client is None:
            # Compute absolute path to calendar_server.py
            calendar_server_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "server", "calendar_server.py")
            )
            self.client = MultiServerMCPClient({
                "google_calendar": {
                    "command": "python",
                    "args": [calendar_server_path],
                    "transport": "stdio",
                }
            })
    
    async def get_calendar_tools(self) -> List[Any]:
        """Get Google Calendar tools from MCP server with lazy loading."""
        if self.client is None:
            await self.initialize()
        
        if self._calendar_tools is None:
            try:
                self._calendar_tools = await self.client.get_tools(server_name="google_calendar")
                print(f" Loaded {len(self._calendar_tools)} calendar tools from MCP server")
                # Only print tool details in debug mode
                if os.getenv("DEBUG_MCP", "false").lower() == "true":
                    for tool in self._calendar_tools:
                        print(f"  - {tool.name}: {tool.description}")
            except Exception as e:
                print(f"WARNING: Failed to load MCP calendar tools: {e}")
                self._calendar_tools = []
        
        return self._calendar_tools
    
    async def close(self):
        """Close the MCP client connection."""
        if self.client:
            # Add any cleanup logic here if needed
            self.client = None
            self._calendar_tools = None
