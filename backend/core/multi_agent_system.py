"""
Multi-Agent System orchestrator
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable
import json
import re

from config import Config
from agents import CalendarAgent, SupervisorAgent, FinanceAgent, SearchAgent, NoteAgent, OCRAgent
from services import MCPService
from services.document_service import DocumentService
from services.chat_history_service import LogsService
from services.conversation_service import ConversationService
from services.conversation_title_service import ConversationTitleService
from services.per_conversation_storage_service import PerConversationStorageService
from services.payment_history_service import PaymentHistoryService
from services.note_service import NoteService
from .state_manager import StateManager


class MultiAgentSystem:
    """Main orchestrator for the multi-agent system."""

    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        # Use API key from Config (loaded from .env file)
        api_key = Config.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file. Please set it in your .env file.")
        self.model = ChatOpenAI(model=model_name, api_key=api_key)
        self.mcp_service = MCPService()
        self.logs_service = LogsService()
        self.conversation_service = ConversationService()
        self.conversation_title_service = ConversationTitleService()
        self.per_conversation_storage = PerConversationStorageService()
        self.payment_service = PaymentHistoryService()
        self.note_db_service = NoteService()
        self.document_service = DocumentService()
        self.state_manager = StateManager()
        
        # Initialize agents
        self.calendar_agent = CalendarAgent(self.model, self.mcp_service)
        self.finance_agent = FinanceAgent(self.model, self.payment_service)
        self.search_agent = SearchAgent(self.model)
        self.note_agent = NoteAgent(self.model, self.note_db_service)
        self.ocr_agent = OCRAgent(self.model, document_service=self.document_service)
        self.supervisor_agent = SupervisorAgent(self.model, self.calendar_agent, self.finance_agent, self.search_agent, self.note_agent, self.ocr_agent)
        
        # Note: Cross-agent context is automatically handled by LangGraph MessagesState
        # which stores all conversation history and makes it available to all agents
        
        self.graph = None
        self._initialized = False
    
    @traceable(name="multi_agent.initialize")
    async def initialize(self):
        """Initialize the multi-agent system with parallel initialization."""
        if self._initialized:
            return
        
        print(" Initializing Multi-Agent System...")
        
        # Initialize services in parallel for better performance
        import asyncio
        await asyncio.gather(
            self.logs_service.initialize(),
            self.conversation_service.initialize(),
            self.conversation_title_service.initialize(),
            self.per_conversation_storage.initialize(),
            self.payment_service.initialize(),
            self.note_db_service.initialize(),
            self.document_service.initialize(),
            self.mcp_service.initialize(),
            return_exceptions=True  # Don't fail if one service fails
        )
        
        # Initialize supervisor agent (which initializes all agents)
        await self.supervisor_agent.initialize()
        
        # Build the graph
        await self._build_graph()
        
        self._initialized = True
        print(" Multi-Agent System initialized successfully!")
    
    @traceable(name="multi_agent.build_graph")
    async def _build_graph(self):
        """Build the LangGraph for the multi-agent system."""
        builder = StateGraph(MessagesState)
        
        # Get supervisor model with tools
        supervisor_model = self.supervisor_agent.get_supervisor_model()
        
        def _supervisor_node_impl(state: MessagesState):
            """Supervisor node that decides which tool to use."""
            system_prompt = self.supervisor_agent.get_system_prompt()
            current_time = self.supervisor_agent.get_current_time_iso()
            
            # Try to detect language from the last user message
            detected_lang = None
            for msg in reversed(state["messages"]):
                if hasattr(msg, 'content') and isinstance(msg.content, str):
                    # Check if this is a user message
                    if hasattr(msg, 'type') and msg.type == 'human':
                        detected_lang = self._detect_language(msg.content, None)
                        break
                    # Also check HumanMessage
                    if isinstance(msg, HumanMessage):
                        detected_lang = self._detect_language(msg.content, None)
                        break
            
            # Add language instruction to system prompt if detected
            language_info = self._get_language_info(detected_lang)
            language_section = ""
            if language_info["system_prompt_addition"]:
                language_section = f"\n\n{language_info['system_prompt_addition']}"
            
            full_prompt = f"{system_prompt}{language_section}\n\nCurrent time (Asia/Ho_Chi_Minh): {current_time}"
            
            # Create system message and combine with existing messages
            messages = [SystemMessage(content=full_prompt)] + state["messages"]
            
            return {
                "messages": [supervisor_model.invoke(messages)]
            }

        # Wrap the supervisor node with a LangSmith span for visibility in traces
        supervisor_node = traceable(name="graph.supervisor_node")(_supervisor_node_impl)
        
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
    
    @traceable(name="multi_agent.process_message")
    async def process_message(self, message: str, thread_id: Optional[str] = None, user_id: Optional[str] = None, model_name: Optional[str] = None, locale: Optional[str] = None) -> str:
        """Process a message through the multi-agent system."""
        if not self._initialized:
            await self.initialize()
        
        # Update model if model_name is provided
        if model_name and model_name != self.model.model_name:
            # Use API key from Config (loaded from .env file)
            api_key = Config.OPENAI_API_KEY
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in .env file. Please set it in your .env file.")
            self.model = ChatOpenAI(model=model_name, api_key=api_key)
            # Re-initialize agents with new model
            await self.initialize()
        
        # Use provided thread_id or current one
        config = self.state_manager.get_config()
        if thread_id:
            config["configurable"]["thread_id"] = thread_id
        
        # Save user message to both logs and per-conversation storage
        current_timestamp = int(datetime.now().timestamp() * 1000)
        current_thread_id = thread_id or config["configurable"]["thread_id"]
        
        # Get user name from user_id (assuming user_id is email or contains name info)
        user_name = user_id if user_id and user_id != "default_user" else "You"
        
        # Save to logs service (for backward compatibility)
        await self.logs_service.save_message(
            thread_id=current_thread_id,
            message_type="user",
            content=message,
            user_id=user_id,
            metadata={"timestamp": datetime.now().isoformat(), "user_name": user_name},
            timestamp=current_timestamp
        )
        
        # Save to per-conversation storage
        await self.per_conversation_storage.save_message(
            thread_id=current_thread_id,
            message_type="user",
            content=message,
            user_id=user_id,
            metadata={"timestamp": datetime.now().isoformat(), "user_name": user_name},
            timestamp=current_timestamp
        )
        
        # Try to get preferred language from conversation metadata first
        preferred_language = None
        if current_thread_id:
            try:
                conversation = await self.conversation_service.get_conversation_by_thread_id(current_thread_id)
                if conversation and conversation.summary:
                    try:
                        metadata = json.loads(conversation.summary)
                        preferred_language = metadata.get("preferred_language")
                    except:
                        pass
            except Exception as e:
                print(f"Warning: Could not load language preference: {e}")
        
        # Auto-detect language from user message if no explicit locale or preferred language
        # Priority: locale > preferred_language > detected from message
        if locale:
            detected_language = self._detect_language(message, locale)
        elif preferred_language:
            detected_language = preferred_language
        else:
            detected_language = self._detect_language(message, None)
        
        # Get language instruction and system prompt addition
        language_info = self._get_language_info(detected_language)
        
        # Store detected language in conversation metadata for future reference
        if detected_language and current_thread_id and detected_language != preferred_language:
            try:
                conversation = await self.conversation_service.get_conversation_by_thread_id(current_thread_id)
                if conversation:
                    # Update conversation metadata with preferred language
                    try:
                        metadata = json.loads(conversation.summary or "{}")
                    except:
                        metadata = {}
                    metadata["preferred_language"] = detected_language
                    await self.conversation_service.update_conversation_summary(
                        current_thread_id, 
                        json.dumps(metadata)
                    )
            except Exception as e:
                print(f"Warning: Could not save language preference: {e}")
        
        # Add language instruction to user message
        user_content = message
        if language_info["instruction"]:
            user_content = f"{language_info['instruction']}\n\n{message}"

        # Process the message
        result = await self.graph.ainvoke(
            {"messages": [HumanMessage(content=user_content)]},
            config=config
        )
        
        # Get the last message (agent's response)
        response = result["messages"][-1].content
        
        # Determine which agent handled the response by analyzing the response content and tool usage
        agent_name = "Supervisor Agent"  # Default
        
        # Check if any tools were called by looking at the conversation flow
        tool_calls_found = False
        for message in result["messages"]:
            if hasattr(message, 'additional_kwargs') and 'tool_calls' in message.additional_kwargs:
                tool_calls = message.additional_kwargs.get('tool_calls', [])
                if tool_calls:
                    tool_calls_found = True
                    tool_name = tool_calls[0].get('function', {}).get('name', '')
                    
                    # Check for finance tools
                    if any(fin_tool in tool_name.lower() for fin_tool in ['add_expense', 'get_expense', 'delete_expense', 'update_expense', 'get_total_spending']):
                        agent_name = "Finance Agent"
                        break
                    # Check for calendar tools
                    elif any(cal_tool in tool_name.lower() for cal_tool in ['list_upcoming_events', 'create_event', 'get_events', 'delete_event', 'update_event', 'move_event']):
                        agent_name = "Calendar Agent"
                        break
                    # Check for search tools
                    elif any(search_tool in tool_name.lower() for search_tool in ['tavily_search', 'mock_search']):
                        agent_name = "Search Agent"
                        break
                    # Check for note tools
                    elif any(note_tool in tool_name.lower() for note_tool in ['record_note', 'list_notes']):
                        agent_name = "Note Agent"
                        break
                    # Check for OCR tools
                    elif any(ocr_tool in tool_name.lower() for ocr_tool in ['process_document', 'search_document', 'list_documents']):
                        agent_name = "OCR Agent"
                        break
        
        # If no tool calls found, try to determine from response content
        if not tool_calls_found:
            response_lower = response.lower()
            if any(keyword in response_lower for keyword in ['chi tiêu', 'expense', 'vnd', 'tổng chi tiêu', 'lịch sử chi tiêu']):
                agent_name = "Finance Agent"
            elif any(keyword in response_lower for keyword in ['lịch', 'sự kiện', 'event', 'calendar', 'thời gian']):
                agent_name = "Calendar Agent"
            elif any(keyword in response_lower for keyword in ['tìm kiếm web', 'kết quả tìm kiếm', 'nguồn tin', 'tavily']):
                agent_name = "Search Agent"
            elif any(keyword in response_lower for keyword in ['ghi chú', 'note', 'recorded note', 'đã lưu ghi chú']):
                agent_name = "Note Agent"
            elif any(keyword in response_lower for keyword in ['ocr', 'tài liệu', 'document', 'pdf', 'trích xuất', 'xử lý file', 'tìm kiếm tài liệu']):
                agent_name = "OCR Agent"
        
        # Format response with agent information
        formatted_response = f"[{agent_name}] {response}"
        
        # Save assistant response to both logs and per-conversation storage
        await self.logs_service.save_message(
            thread_id=current_thread_id,
            message_type="assistant",
            content=response,
            agent_name=agent_name,
            user_id=user_id,
            metadata={"timestamp": datetime.now().isoformat()},
            timestamp=current_timestamp + 1  # Slightly after user message
        )
        
        # Save to per-conversation storage
        await self.per_conversation_storage.save_message(
            thread_id=current_thread_id,
            message_type="assistant",
            content=response,
            agent_name=agent_name,
            user_id=user_id,
            metadata={"timestamp": datetime.now().isoformat()},
            timestamp=current_timestamp + 1
        )
        
        return formatted_response
    
    @traceable(name="multi_agent.get_chat_history")
    async def get_chat_history(self, thread_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation logs for a thread using per-conversation storage."""
        try:
            # Try to get from per-conversation storage first
            messages = await self.per_conversation_storage.get_conversation_messages(thread_id, limit)
            if messages:
                return messages
            
            # Fallback to logs service if per-conversation storage is empty
            messages = await self.logs_service.get_chat_history(thread_id, limit)
            return [msg.to_dict() for msg in messages]
            
        except Exception as e:
            print(f"Error getting chat history: {str(e)}")
            return []
    
    @traceable(name="multi_agent.get_all_conversation_messages")
    async def get_all_conversation_messages(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a conversation (no pagination)."""
        try:
            # Try to get from per-conversation storage first
            messages = await self.per_conversation_storage.get_all_conversation_messages(thread_id)
            if messages:
                return messages
            
            # Fallback to logs service if per-conversation storage is empty
            messages = await self.logs_service.get_chat_history(thread_id, limit=1000)  # Large limit
            return [msg.to_dict() for msg in messages]
            
        except Exception as e:
            print(f"Error getting all conversation messages: {str(e)}")
            return []
    
    @traceable(name="multi_agent.get_user_chat_history")
    async def get_user_chat_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get conversation logs for a specific user."""
        messages = await self.logs_service.get_user_chat_history(user_id, limit)
        return [msg.to_dict() for msg in messages]
    
    @traceable(name="multi_agent.get_user_threads")
    async def get_user_threads(self, user_id: str) -> List[str]:
        """Get all thread IDs for a user."""
        return await self.logs_service.get_threads_for_user(user_id)
    
    @traceable(name="multi_agent.delete_thread")
    async def delete_thread(self, thread_id: str) -> bool:
        """Delete a conversation thread from both storage systems."""
        try:
            # Delete from logs service
            logs_deleted = await self.logs_service.delete_thread(thread_id)
            
            # Delete from per-conversation storage
            per_conversation_deleted = await self.per_conversation_storage.delete_conversation_messages(thread_id)
            
            return logs_deleted or per_conversation_deleted
            
        except Exception as e:
            print(f"Error deleting thread: {str(e)}")
            return False
    
    async def chat_interactive(self, user_id: Optional[str] = None):
        """Start interactive chat session."""
        if not self._initialized:
            await self.initialize()
        
        print("=" * 60)
        print(" Multi-Agent System (Calendar)")
        print("=" * 60)
        print("Special commands:")
        print("  - 'exit' or 'quit': Exit")
        print("  - 'clear': Clear chat history")
        print("  - 'history': Show recent conversation")
        print("  - 'threads': Show your conversation threads")
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
                
                if user_input.lower() == 'history':
                    # Show recent conversation
                    config = self.state_manager.get_config()
                    thread_id = config["configurable"]["thread_id"]
                    history = await self.get_chat_history(thread_id, limit=5)
                    print(f"\nNekAssist Recent conversation ({len(history)} messages):")
                    for msg in history:
                        role = " You" if msg["message_type"] == "user" else f"NekAssist {msg['agent_name'] or 'Assistant'}"
                        print(f"{role}: {msg['content']}")
                    print()
                    continue
                
                if user_input.lower() == 'threads' and user_id:
                    # Show user's threads
                    threads = await self.get_user_threads(user_id)
                    print(f"\n Your conversation threads ({len(threads)} threads):")
                    for i, thread in enumerate(threads, 1):
                        print(f"  {i}. {thread}")
                    print()
                    continue
                
                # Process the message
                print("\ Processing...\n")
                response = await self.process_message(user_input, user_id=user_id)
                print(f"{response}\n")
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
    
    def _detect_language(self, message: str, locale: Optional[str] = None) -> Optional[str]:
        """Detect language from message or use provided locale."""
        if locale:
            # Extract language code from locale (e.g., "vi-VN" -> "vi", "en-US" -> "en")
            lang_code = locale.split("-")[0].lower() if "-" in locale else locale.lower()
            return lang_code
        
        if not message or not message.strip():
            return None
        
        message_lower = message.lower()
        
        # Vietnamese detection
        vietnamese_chars = set("àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ")
        vietnamese_words = ["tôi", "bạn", "của", "và", "là", "có", "không", "được", "với", "cho", "này", "đó", "trong", "một", "các"]
        
        if any(char in vietnamese_chars for char in message_lower):
            return "vi"
        if any(word in message_lower for word in vietnamese_words):
            return "vi"
        
        # Japanese detection
        japanese_chars = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
        if japanese_chars.search(message):
            return "ja"
        
        # Korean detection
        korean_chars = re.compile(r'[\uAC00-\uD7AF]')
        if korean_chars.search(message):
            return "ko"
        
        # Chinese detection
        chinese_chars = re.compile(r'[\u4E00-\u9FFF]')
        if chinese_chars.search(message):
            return "zh"
        
        # English detection (default for ASCII)
        if message.strip() and all(ord(c) < 128 for c in message):
            return "en"
        
        # Default to Vietnamese if cannot determine
        return "vi"
    
    def _get_language_info(self, language: Optional[str]) -> Dict[str, str]:
        """Get language instruction and system prompt addition based on detected language."""
        if not language:
            language = "vi"  # Default to Vietnamese
        
        lang = language.lower()
        
        language_map = {
            "vi": {
                "instruction": "Hãy trả lời bằng tiếng Việt một cách tự nhiên và rõ ràng.",
                "system_prompt_addition": "QUY TẮC NGÔN NGỮ: Trả lời bằng tiếng Việt một cách tự nhiên, rõ ràng và thân thiện."
            },
            "en": {
                "instruction": "Please answer in English naturally and clearly.",
                "system_prompt_addition": "LANGUAGE RULE: Answer in English naturally, clearly, and friendly."
            },
            "ja": {
                "instruction": "日本語で自然で明確に回答してください。",
                "system_prompt_addition": "言語ルール: 日本語で自然で明確に、親しみやすく回答してください。"
            },
            "ko": {
                "instruction": "한국어로 자연스럽고 명확하게 답변해 주세요.",
                "system_prompt_addition": "언어 규칙: 한국어로 자연스럽고 명확하며 친근하게 답변하세요."
            },
            "zh": {
                "instruction": "请用中文自然清晰地回答。",
                "system_prompt_addition": "语言规则: 用中文自然、清晰地回答，保持友好。"
            }
        }
        
        return language_map.get(lang, language_map["vi"])
    
    async def close(self):
        """Close the system and cleanup resources."""
        await self.mcp_service.close()
        await self.logs_service.close()
        await self.payment_service.close()
        await self.note_db_service.close()
        await self.document_service.close()
        print(" Multi-Agent System closed.")
