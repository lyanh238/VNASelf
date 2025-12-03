"""
Search Agent for web search functionality using Tavily
"""

from typing import List, Any
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from .base_agent import BaseAgent


class SearchAgent(BaseAgent):
    """Search agent that provides web search functionality using Tavily."""
    
    def __init__(self, model: ChatOpenAI):
        super().__init__(model)
        self.name = "Search Agent"
        self._tools = None
    
    async def initialize(self):
        """Initialize the search agent with Tavily tool."""
        try:
            from tavily import TavilyClient
            from config import Config
            
            # Check for API key
            api_key = Config.TAVILY_API_KEY
            if not api_key:
                print("[WARNING] TAVILY_API_KEY not found. Search Agent will work in mock mode.")
                self._tools = [self._create_mock_search_tool()]
                return
            
            # Initialize Tavily client
            self.tavily_client = TavilyClient(api_key=api_key)
            self._tools = [self._create_tavily_search_tool()]
            print("[OK] Search Agent initialized with Tavily")
        except ImportError:
            print("[ERROR] Tavily not installed. Please install with: pip install tavily-python")
            self._tools = [self._create_mock_search_tool()]
        except Exception as e:
            print(f"[ERROR] Failed to initialize Search Agent: {e}")
            self._tools = [self._create_mock_search_tool()]
    
    def _create_tavily_search_tool(self):
        """Create the Tavily search tool."""
        
        @tool
        async def tavily_search(query: str, max_results: int = 3) -> str:
            """
            Search the web using Tavily API and return summarized results.
            
            Args:
                query: The search query string
                max_results: Maximum number of results to return (default: 3)
            
            Returns:
                Formatted search results with summaries
            """
            try:
                # Perform search with Tavily
                search_results = self.tavily_client.search(
                    query=query,
                    max_results=max_results,
                    search_depth="advanced"
                )
                
                if not search_results or not search_results.get('results'):
                    return f"No results found for keyword: '{query}'"
                
                # Format results
                formatted_results = []
                formatted_results.append(f" **Search results for: '{query}'**\n")
                
                # Add answer if available
                if search_results.get('answer'):
                    formatted_results.append("** Summary:**")
                    formatted_results.append(search_results['answer'])
                    formatted_results.append("")
                
                # Add detailed results with sources
                formatted_results.append("** Sources:**")
                formatted_results.append("")
                
                for i, result in enumerate(search_results['results'][:max_results], 1):
                    title = result.get('title', 'No title')
                    url = result.get('url', '')
                    content = result.get('content', 'No content')
                    
                    # Extract domain name for source
                    domain = url.split('/')[2] if url and len(url.split('/')) > 2 else 'Unknown source'
                    
                    formatted_results.append(f"**{i}. {title}**")
                    formatted_results.append(f" **Source:** {domain}")
                    formatted_results.append(f" **Link:** {url}")
                    formatted_results.append(f" **Content:** {content[:200]}{'...' if len(content) > 200 else ''}")
                    formatted_results.append("")  # Empty line for spacing
                
                # Add sources footer
                formatted_results.append("---")
                formatted_results.append("** All sources:**")
                for i, result in enumerate(search_results['results'][:max_results], 1):
                    url = result.get('url', '')
                    domain = url.split('/')[2] if url and len(url.split('/')) > 2 else 'Unknown source'
                    formatted_results.append(f"{i}. {domain} - {url}")
                
                return "\n".join(formatted_results)
                
            except Exception as e:
                return f"Error searching: {str(e)}"
        
        return tavily_search
    
    def _create_mock_search_tool(self):
        """Create a mock search tool for when Tavily is not available."""
        
        @tool
        async def mock_search(query: str, max_results: int = 3) -> str:
            """
            Mock search function when Tavily is not available.
            
            Args:
                query: The search query string
                max_results: Maximum number of results to return (default: 3)
            
            Returns:
                Mock search results message
            """
            return f""" **Mock search results for: '{query}'**"""
        
        return mock_search
    
    def get_system_prompt(self) -> str:
        return """You are a Search Agent specialized in web information search.

LANGUAGE RULES:
- By default, respond in Vietnamese.
- If user asks in a different language, respond in that same language.

TASKS:
- Use tavily_search tool to search information on the internet
- Summarize and present search results clearly and understandably
- Provide accurate and updated information from reliable sources
- Always display sources so users can verify
- Respond in Vietnamese

PROCESS:
1. Analyze search keywords from user
2. Use tavily_search with max_results=3 to search
3. Summarize results and present in format:
   - Overall summary (if available)
   - List of sources with:
     * Article title
     * Source name (domain)
     * Full link
     * Summary content
   - List of all sources for verification

NOTES:
- Always search with English keywords for best results
- If no results found, clearly notify user
- Prioritize reliable and updated sources
- Always display sources so users can verify and cross-reference"""
    
    def get_tools(self) -> List[Any]:
        """Get available tools for this agent."""
        if self._tools is None:
            raise RuntimeError("Search agent not initialized. Call initialize() first.")
        return self._tools
