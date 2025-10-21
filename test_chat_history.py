"""
Test script for chat history functionality
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.multi_agent_system import MultiAgentSystem
from config import Config


async def test_chat_history():
    """Test the chat history functionality."""
    
    print("🧪 Testing Chat History Functionality")
    print("=" * 60)
    
    # Check configuration
    if not Config.validate():
        print("❌ Please set up environment variables first!")
        print("Required: OPENAI_API_KEY, NEON_DATABASE_URL")
        return
    
    # Initialize system
    print("🚀 Initializing system...")
    system = MultiAgentSystem()
    
    try:
        await system.initialize()
        print("✅ System ready!")
        
        # Test user ID
        test_user_id = "test_user_123"
        test_thread_id = "test_thread_456"
        
        print(f"\n👤 Testing with user_id: {test_user_id}")
        print(f"🧵 Testing with thread_id: {test_thread_id}")
        
        # Test 1: Basic conversation
        print("\n📝 Test 1: Basic conversation")
        print("-" * 40)
        
        messages = [
            "Hello, I have a headache",
            "Can you help me with my calendar?",
            "What's the weather like today?"
        ]
        
        for i, message in enumerate(messages, 1):
            print(f"\nMessage {i}: {message}")
            response = await system.process_message(
                message, 
                thread_id=test_thread_id, 
                user_id=test_user_id
            )
            print(f"Response: {response[:100]}...")
        
        # Test 2: Retrieve chat history
        print("\n📚 Test 2: Retrieve chat history")
        print("-" * 40)
        
        history = await system.get_chat_history(test_thread_id, limit=10)
        print(f"Retrieved {len(history)} messages:")
        
        for msg in history:
            role = "👤 User" if msg["message_type"] == "user" else f"🤖 {msg['agent_name'] or 'Assistant'}"
            print(f"  {role}: {msg['content'][:50]}...")
            print(f"    Thread: {msg['thread_id']}, User: {msg['user_id']}")
            print(f"    Time: {msg['created_at']}")
            print()
        
        # Test 3: User's chat history
        print("\n👤 Test 3: User's chat history")
        print("-" * 40)
        
        user_history = await system.get_user_chat_history(test_user_id, limit=5)
        print(f"User {test_user_id} has {len(user_history)} messages:")
        
        for msg in user_history:
            role = "👤 User" if msg["message_type"] == "user" else f"🤖 {msg['agent_name'] or 'Assistant'}"
            print(f"  {role}: {msg['content'][:50]}...")
        
        # Test 4: User's threads
        print("\n📁 Test 4: User's threads")
        print("-" * 40)
        
        threads = await system.get_user_threads(test_user_id)
        print(f"User {test_user_id} has {len(threads)} threads:")
        for thread in threads:
            print(f"  - {thread}")
        
        # Test 5: Multiple threads
        print("\n🧵 Test 5: Multiple threads")
        print("-" * 40)
        
        thread2_id = "test_thread_789"
        await system.process_message(
            "This is a different conversation", 
            thread_id=thread2_id, 
            user_id=test_user_id
        )
        
        threads = await system.get_user_threads(test_user_id)
        print(f"Now user has {len(threads)} threads:")
        for thread in threads:
            print(f"  - {thread}")
        
        # Test 6: Agent detection
        print("\n🤖 Test 6: Agent detection")
        print("-" * 40)
        
        health_message = "I have a fever and cough"
        calendar_message = "Show me my calendar for today"
        
        print(f"Health query: {health_message}")
        response1 = await system.process_message(
            health_message, 
            thread_id=test_thread_id, 
            user_id=test_user_id
        )
        print(f"Response: {response1[:100]}...")
        
        print(f"\nCalendar query: {calendar_message}")
        response2 = await system.process_message(
            calendar_message, 
            thread_id=test_thread_id, 
            user_id=test_user_id
        )
        print(f"Response: {response2[:100]}...")
        
        # Check which agents were detected
        recent_history = await system.get_chat_history(test_thread_id, limit=4)
        print(f"\nRecent messages with agent detection:")
        for msg in recent_history[-4:]:
            role = "👤 User" if msg["message_type"] == "user" else f"🤖 {msg['agent_name'] or 'Assistant'}"
            print(f"  {role}: {msg['content'][:50]}...")
        
        print("\n✅ Chat History Test Completed Successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        await system.close()


async def test_database_operations():
    """Test database operations separately."""
    
    print("\n🗄️ Testing Database Operations")
    print("=" * 60)
    
    from services.chat_history_service import LogsService
    
    service = LogsService()
    
    try:
        await service.initialize()
        print("✓ Logs service initialized")
        
        # Test saving messages
        print("\nTesting message saving...")
        
        # Save user message
        user_msg = await service.save_message(
            thread_id="db_test_thread",
            message_type="user",
            content="Test user message",
            user_id="db_test_user"
        )
        
        if user_msg:
            print(f"✓ User message saved: ID {user_msg.id}")
        else:
            print("⚠ User message not saved (database not available)")
        
        # Save assistant message
        assistant_msg = await service.save_message(
            thread_id="db_test_thread",
            message_type="assistant",
            content="Test assistant response",
            agent_name="Test Agent",
            user_id="db_test_user"
        )
        
        if assistant_msg:
            print(f"✓ Assistant message saved: ID {assistant_msg.id}")
        else:
            print("⚠ Assistant message not saved (database not available)")
        
        # Test retrieving messages
        print("\nTesting message retrieval...")
        messages = await service.get_chat_history("db_test_thread", limit=5)
        print(f"✓ Retrieved {len(messages)} messages")
        
        for msg in messages:
            print(f"  - {msg.message_type}: {msg.content[:30]}...")
        
        # Test user threads
        print("\nTesting user threads...")
        threads = await service.get_threads_for_user("db_test_user")
        print(f"✓ User has {len(threads)} threads: {threads}")
        
        print("✓ Database operations test completed")
        
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        raise
    
    finally:
        await service.close()


if __name__ == "__main__":
    print("🚀 Starting Chat History Tests")
    print("Make sure you have set the following environment variables:")
    print("- OPENAI_API_KEY")
    print("- NEON_DATABASE_URL")
    print()
    
    # Run tests
    asyncio.run(test_database_operations())
    asyncio.run(test_chat_history())
