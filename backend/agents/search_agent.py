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
                    return f"Không tìm thấy kết quả nào cho từ khóa: '{query}'"
                
                # Format results
                formatted_results = []
                formatted_results.append(f" **Kết quả tìm kiếm cho: '{query}'**\n")
                
                # Add answer if available
                if search_results.get('answer'):
                    formatted_results.append("** Tóm tắt:**")
                    formatted_results.append(search_results['answer'])
                    formatted_results.append("")
                
                # Add detailed results with sources
                formatted_results.append("** Nguồn tin:**")
                formatted_results.append("")
                
                for i, result in enumerate(search_results['results'][:max_results], 1):
                    title = result.get('title', 'Không có tiêu đề')
                    url = result.get('url', '')
                    content = result.get('content', 'Không có nội dung')
                    
                    # Extract domain name for source
                    domain = url.split('/')[2] if url and len(url.split('/')) > 2 else 'Nguồn không xác định'
                    
                    formatted_results.append(f"**{i}. {title}**")
                    formatted_results.append(f" **Nguồn:** {domain}")
                    formatted_results.append(f" **Link:** {url}")
                    formatted_results.append(f" **Nội dung:** {content[:200]}{'...' if len(content) > 200 else ''}")
                    formatted_results.append("")  # Empty line for spacing
                
                # Add sources footer
                formatted_results.append("---")
                formatted_results.append("** Tất cả nguồn:**")
                for i, result in enumerate(search_results['results'][:max_results], 1):
                    url = result.get('url', '')
                    domain = url.split('/')[2] if url and len(url.split('/')) > 2 else 'Nguồn không xác định'
                    formatted_results.append(f"{i}. {domain} - {url}")
                
                return "\n".join(formatted_results)
                
            except Exception as e:
                return f"Lỗi khi tìm kiếm: {str(e)}"
        
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
            return f""" **Kết quả tìm kiếm mô phỏng cho: '{query}'**"""
        
        return mock_search
    
    def get_system_prompt(self) -> str:
        return """Bạn là Search Agent chuyên về tìm kiếm thông tin trên web.

QUY TẮC NGÔN NGỮ:
- Mặc định trả lời bằng tiếng Việt.
- Nếu người dùng hỏi bằng ngôn ngữ khác, trả lời bằng chính ngôn ngữ đó.

NHIỆM VỤ:
- Sử dụng công cụ tavily_search để tìm kiếm thông tin trên internet
- Tổng hợp và trình bày kết quả tìm kiếm một cách rõ ràng, dễ hiểu
- Cung cấp thông tin chính xác và cập nhật từ các nguồn đáng tin cậy
- Luôn hiển thị nguồn tin để người dùng có thể đối chiếu
- Trả lời bằng tiếng Việt

QUY TRÌNH:
1. Phân tích từ khóa tìm kiếm từ người dùng
2. Sử dụng tavily_search với max_results=3 để tìm kiếm
3. Tổng hợp kết quả và trình bày theo format:
   - Tóm tắt tổng quan (nếu có)
   - Danh sách nguồn tin với:
     * Tiêu đề bài viết
     * Tên nguồn (domain)
     * Link đầy đủ
     * Nội dung tóm tắt
   - Danh sách tất cả nguồn để đối chiếu

LƯU Ý:
- Luôn tìm kiếm với từ khóa tiếng Anh để có kết quả tốt nhất
- Nếu không tìm thấy kết quả, thông báo rõ ràng cho người dùng
- Ưu tiên các nguồn tin đáng tin cậy và cập nhật
- Luôn hiển thị nguồn tin để người dùng có thể kiểm tra và đối chiếu"""
    
    def get_tools(self) -> List[Any]:
        """Get available tools for this agent."""
        if self._tools is None:
            raise RuntimeError("Search agent not initialized. Call initialize() first.")
        return self._tools
