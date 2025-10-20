"""
Health Agent for medical consultation and health advice
"""

from typing import List, Any
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from .base_agent import BaseAgent


class HealthAgent(BaseAgent):
    """Specialized agent for health consultation and medical advice."""
    
    def __init__(self, model: ChatOpenAI):
        super().__init__(model)
        self.name = "Health Agent"
    
    def get_system_prompt(self) -> str:
        return """Bạn là bác sĩ tư vấn sức khỏe tổng quát. 
        Hãy trả lời ngắn gọn 3-5 câu về các triệu chứng và đưa ra lời khuyên an toàn.
        Lưu ý: Đây chỉ là tư vấn sơ bộ, không thay thế cho việc khám bệnh trực tiếp."""
    
    def get_tools(self) -> List[Any]:
        return [self.health_consultation_tool]
    
    @tool
    def health_consultation_tool(self, symptoms: str) -> str:
        """
        Tư vấn sức khỏe dựa trên triệu chứng người dùng.
        
        Args:
            symptoms: Mô tả triệu chứng của người dùng
        """
        prompt = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Người dùng nói rằng họ có triệu chứng: {symptoms}. Hãy mô tả nguyên nhân có thể và gợi ý hành động an toàn."}
        ]
        response = self.model.invoke(prompt)
        return response.content
