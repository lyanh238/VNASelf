"""
Demo script showcasing chat history functionality
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.multi_agent_system import MultiAgentSystem
from config import Config


async def demo_chat_history():
    """Demo the chat history functionality."""
    
    print(" Chat History Demo")
    print("=" * 60)
    
    # Check configuration
    if not Config.validate():
        print(" Please set up environment variables first!")
        print("Required: OPENAI_API_KEY, NEON_DATABASE_URL")
        return
    
    # Initialize system
    print(" Initializing system...")
    system = MultiAgentSystem()
    
    try:
        await system.initialize()
        print(" System ready!")
        
        # Demo user
        demo_user_id = "demo_user"
        demo_thread_id = "demo_conversation"
        
        print(f"\n Demo User: {demo_user_id}")
        print(f" Demo Thread: {demo_thread_id}")
        
        # Demo conversation
        print("\n Starting demo conversation...")
        print("=" * 60)
        
        demo_messages = [
            "Hello! I'm feeling unwell today",
            "I have a headache and feel tired",
            "Can you help me schedule a doctor appointment?",
            "What should I do to feel better?",
            "Show me my calendar for this week"
        ]
        
        for i, message in enumerate(demo_messages, 1):
            print(f"\n[Message {i}] 👤 User: {message}")
            
            response = await system.process_message(
                message, 
                thread_id=demo_thread_id, 
                user_id=demo_user_id
            )
            
            print(f"[Response {i}]  Assistant: {response}")
            print("-" * 40)
        
        # Show conversation history
        print("\n Conversation History")
        print("=" * 60)
        
        history = await system.get_chat_history(demo_thread_id, limit=10)
        print(f"Total messages in conversation: {len(history)}")
        
        for i, msg in enumerate(history, 1):
            role = " User" if msg["message_type"] == "user" else f" {msg['agent_name'] or 'Assistant'}"
            timestamp = msg["created_at"][:19] if msg["created_at"] else "Unknown time"
            print(f"\n{i}. [{timestamp}] {role}")
            print(f"   {msg['content']}")
        
        # Show user's threads
        print(f"\n User's Conversation Threads")
        print("=" * 60)
        
        threads = await system.get_user_threads(demo_user_id)
        print(f"User {demo_user_id} has {len(threads)} conversation threads:")
        
        for i, thread in enumerate(threads, 1):
            print(f"  {i}. {thread}")
        
        # Demo multiple users
        print(f"\n👥 Multi-User Demo")
        print("=" * 60)
        
        user2_id = "demo_user_2"
        thread2_id = "demo_conversation_2"
        
        print(f"Adding conversation for user: {user2_id}")
        
        await system.process_message(
            "Hi, I need help with my health", 
            thread_id=thread2_id, 
            user_id=user2_id
        )
        
        await system.process_message(
            "I have a fever", 
            thread_id=thread2_id, 
            user_id=user2_id
        )
        
        # Show both users' threads
        print(f"\nUser {demo_user_id} threads:")
        threads1 = await system.get_user_threads(demo_user_id)
        for thread in threads1:
            print(f"  - {thread}")
        
        print(f"\nUser {user2_id} threads:")
        threads2 = await system.get_user_threads(user2_id)
        for thread in threads2:
            print(f"  - {thread}")
        
        # Show agent detection
        print(f"\n Agent Detection Demo")
        print("=" * 60)
        
        print("Analyzing which agents handled each message:")
        for msg in history:
            if msg["message_type"] == "assistant":
                agent = msg["agent_name"] or "Unknown"
                content_preview = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
                print(f"   {agent}: {content_preview}")
        
        print("\n Chat History Demo Completed!")
        print("\nKey Features Demonstrated:")
        print(" Automatic message logging")
        print(" Thread-based conversation tracking")
        print(" User-based conversation management")
        print(" Agent detection and logging")
        print(" Multi-user support")
        print(" Conversation history retrieval")
        
    except Exception as e:
        print(f" Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        await system.close()


async def interactive_demo():
    """Interactive demo with chat history features."""
    
    print(" Interactive Chat History Demo")
    print("=" * 60)
    print("Chat with the system and explore history features!")
    print("Commands:")
    print("  - 'history': Show recent conversation")
    print("  - 'threads': Show your conversation threads")
    print("  - 'clear': Start new conversation")
    print("  - 'exit': Quit")
    print("=" * 60)
    
    # Initialize system
    system = MultiAgentSystem()
    await system.initialize()
    
    # Get user ID
    user_id = input("Enter your user ID (or press Enter for 'demo_user'): ").strip()
    if not user_id:
        user_id = "demo_user"
    
    print(f" Logged in as: {user_id}")
    
    try:
        while True:
            message = input(f"\n {user_id}: ").strip()
            
            if not message:
                continue
            
            if message.lower() in ['exit', 'quit', 'thoát']:
                print("\n Goodbye!")
                break
            
            if message.lower() == 'history':
                # Show recent conversation
                config = system.state_manager.get_config()
                thread_id = config["configurable"]["thread_id"]
                history = await system.get_chat_history(thread_id, limit=10)
                
                print(f"\n Recent conversation ({len(history)} messages):")
                for msg in history:
                    role = " You" if msg["message_type"] == "user" else f" {msg['agent_name'] or 'Assistant'}"
                    timestamp = msg["created_at"][:19] if msg["created_at"] else "Unknown"
                    print(f"[{timestamp}] {role}: {msg['content']}")
                continue
            
            if message.lower() == 'threads':
                # Show user's threads
                threads = await system.get_user_threads(user_id)
                print(f"\n Your conversation threads ({len(threads)} threads):")
                for i, thread in enumerate(threads, 1):
                    print(f"  {i}. {thread}")
                continue
            
            if message.lower() == 'clear':
                # Start new conversation
                system.state_manager.create_new_thread()
                print("\n New conversation started!")
                continue
            
            # Process message
            print("\n Processing...")
            response = await system.process_message(message, user_id=user_id)
            print(f" Assistant: {response}")
    
    except KeyboardInterrupt:
        print("\n\n Goodbye!")
    
    finally:
        await system.close()


if __name__ == "__main__":
    print("Choose demo mode:")
    print("1. Automated demo")
    print("2. Interactive chat")
    
    choice = input("Enter choice (1/2): ").strip()
    
    if choice == "2":
        asyncio.run(interactive_demo())
    else:
        asyncio.run(demo_chat_history())
