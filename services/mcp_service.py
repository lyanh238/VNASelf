"""
MCP Service for managing Google Calendar MCP client
"""

from typing import List, Any
from langchain_mcp_adapters.client import MultiServerMCPClient


class MCPService:
    """Service for managing MCP client connections and tools."""
    
    def __init__(self):
        self.client = None
        self._calendar_tools = None
    
    async def initialize(self):
        """Initialize the MCP client."""
        if self.client is None:
            self.client = MultiServerMCPClient({
                "google_calendar": {
                    "command": "python",
                    "args": ["calendar_server.py"],
                    "transport": "stdio",
                }
            })
    
    async def get_calendar_tools(self) -> List[Any]:
        """Get Google Calendar tools from MCP server."""
        if self.client is None:
            await self.initialize()
        
        if self._calendar_tools is None:
            self._calendar_tools = await self.client.get_tools(server_name="google_calendar")
            print(f" Loaded {len(self._calendar_tools)} calendar tools from MCP server:")
            for tool in self._calendar_tools:
                print(f"  - {tool.name}: {tool.description}")
        
        return self._calendar_tools
    
    async def close(self):
        """Close the MCP client connection."""
        if self.client:
            # Add any cleanup logic here if needed
            self.client = None
            self._calendar_tools = None
