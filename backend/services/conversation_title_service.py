"""
LLM-based conversation title generation service
"""

import asyncio
from typing import List, Optional, Dict, Any
import openai
from config import Config

class ConversationTitleService:
    """Service for generating conversation titles using LLM."""
    
    def __init__(self):
        self.client = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize OpenAI client."""
        if self._initialized:
            return
        
        try:
            if Config.OPENAI_API_KEY:
                self.client = openai.AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
                print("[OK] Conversation Title Service initialized")
            else:
                print("WARNING: OPENAI_API_KEY not set - title generation disabled")
            
            self._initialized = True
            
        except Exception as e:
            print(f"[ERROR] Error initializing conversation title service: {str(e)}")
            self._initialized = True
    
    async def generate_title_from_messages(self, messages: List[Dict[str, Any]]) -> str:
        """Generate a conversation title from the first few messages."""
        if not self.client or not messages:
            return "New conversation"
        
        try:
            # Get the first user message and first assistant response
            user_messages = [msg for msg in messages if msg.get("message_type") == "user"]
            assistant_messages = [msg for msg in messages if msg.get("message_type") == "assistant"]
            
            if not user_messages:
                return "New conversation"
            
            # Use first user message and optionally first assistant response
            context_messages = [user_messages[0]["content"]]
            if assistant_messages:
                context_messages.append(assistant_messages[0]["content"])
            
            # Limit context to avoid token limits
            context = " ".join(context_messages)[:1000]
            
            prompt = f"""Based on this conversation, generate a concise, descriptive title (maximum 5 words) that captures the main topic or purpose:

User: {context}

Title:"""

            response = await self.client.chat.completions.create(
                model=Config.MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates concise, descriptive titles for conversations. Keep titles under 5 words and make them clear and informative."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=20,
                temperature=0.7
            )
            
            title = response.choices[0].message.content.strip()
            # Clean up the title
            title = title.replace('"', '').replace("'", "").strip()
            
            # Ensure title is not too long
            if len(title) > 50:
                title = title[:47] + "..."
            
            return title if title else "New conversation"
            
        except Exception as e:
            print(f"Error generating title: {str(e)}")
            return "New conversation"
    
    async def generate_title_from_content(self, content: str) -> str:
        """Generate a conversation title from content."""
        if not self.client or not content:
            return "New conversation"
        
        try:
            # Limit content to avoid token limits
            content = content[:1000]
            
            prompt = f"""Based on this message content, generate a concise, descriptive title (maximum 5 words) that captures the main topic or purpose:

Content: {content}

Title:"""

            response = await self.client.chat.completions.create(
                model=Config.MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates concise, descriptive titles for conversations. Keep titles under 5 words and make them clear and informative."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=20,
                temperature=0.7
            )
            
            title = response.choices[0].message.content.strip()
            # Clean up the title
            title = title.replace('"', '').replace("'", "").strip()
            
            # Ensure title is not too long
            if len(title) > 50:
                title = title[:47] + "..."
            
            return title if title else "New conversation"
            
        except Exception as e:
            print(f"Error generating title from content: {str(e)}")
            return "New conversation"
    
    async def generate_summary(self, messages: List[Dict[str, Any]]) -> str:
        """Generate a summary of the conversation."""
        if not self.client or not messages:
            return ""
        
        try:
            # Combine all messages into a single context
            conversation_text = []
            for msg in messages:
                role = "User" if msg.get("message_type") == "user" else "Assistant"
                content = msg.get("content", "")
                conversation_text.append(f"{role}: {content}")
            
            context = "\n".join(conversation_text)[:2000]  # Limit context
            
            prompt = f"""Summarize this conversation in 2-3 sentences, focusing on the main topics discussed and any key outcomes or decisions:

{context}

Summary:"""

            response = await self.client.chat.completions.create(
                model=Config.MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise summaries of conversations. Focus on main topics and key outcomes."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.5
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
            
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return ""
