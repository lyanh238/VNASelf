"""
Script to create logs table in Neon Database
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.chat_history_service import LogsService
from config import Config


async def create_logs_table():
    """Create logs table in Neon Database."""
    
    print("🗄️ Creating logs table in Neon Database")
    print("=" * 60)
    
    # Check configuration
    if not Config.NEON_DATABASE_URL:
        print("❌ NEON_DATABASE_URL not set!")
        print("Please set the environment variable:")
        print("export NEON_DATABASE_URL='postgresql://username:password@host:port/database'")
        return
    
    # Initialize service
    service = LogsService()
    
    try:
        await service.initialize()
        print(" Logs service initialized successfully!")
        
        # Check if table exists
        session = service.get_session()
        if session:
            try:
                # Try to query the table to see if it exists
                result = session.execute("SELECT COUNT(*) FROM logs LIMIT 1")
                print(" Logs table already exists and is accessible")
                
                # Show table structure
                print("\n Current logs table structure:")
                result = session.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'logs' 
                    ORDER BY ordinal_position
                """)
                
                for row in result:
                    print(f"  - {row[0]}: {row[1]} {'(nullable)' if row[2] == 'YES' else '(not null)'}")
                
            except Exception as e:
                if "does not exist" in str(e).lower():
                    print("⚠ Logs table does not exist, creating it...")
                    
                    # Create table manually
                    create_table_sql = """
                    CREATE TABLE IF NOT EXISTS logs (
                        id SERIAL PRIMARY KEY,
                        thread_id VARCHAR(255) NOT NULL,
                        user_id VARCHAR(255),
                        message_type VARCHAR(50) NOT NULL,
                        content TEXT NOT NULL,
                        agent_name VARCHAR(100),
                        metadata TEXT,
                        timestamp BIGINT NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        is_deleted BOOLEAN DEFAULT FALSE
                    );
                    """
                    
                    session.execute(create_table_sql)
                    session.commit()
                    print(" Logs table created successfully!")
                    
                    # Create indexes
                    print(" Creating indexes...")
                    indexes = [
                        "CREATE INDEX IF NOT EXISTS idx_logs_thread_id ON logs(thread_id);",
                        "CREATE INDEX IF NOT EXISTS idx_logs_user_id ON logs(user_id);",
                        "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);",
                        "CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at);"
                    ]
                    
                    for index_sql in indexes:
                        session.execute(index_sql)
                    
                    session.commit()
                    print(" Indexes created successfully!")
                    
                else:
                    print(f" Error checking table: {str(e)}")
                    return
        else:
            print(" Could not establish database connection")
            return
        
        # Test table with sample data
        print("\n Testing table with sample data...")
        
        # Save test message
        test_message = await service.save_message(
            thread_id="test_table_creation",
            message_type="user",
            content="Test message for table creation",
            user_id="test_user",
            agent_name="Test Agent",
            metadata={"test": True}
        )
        
        if test_message:
            print(f" Test message saved successfully! ID: {test_message.id}")
            print(f"   Timestamp: {test_message.timestamp}")
            print(f"   Thread ID: {test_message.thread_id}")
            
            # Retrieve test message
            messages = await service.get_chat_history("test_table_creation", limit=1)
            if messages:
                print(f" Test message retrieved successfully!")
                print(f"   Content: {messages[0].content}")
                print(f"   Agent: {messages[0].agent_name}")
            else:
                print(" Could not retrieve test message")
        else:
            print(" Failed to save test message")
        
        print("\n Logs table setup completed successfully!")
        print("\nTable structure:")
        print("- id: Primary key")
        print("- thread_id: Conversation thread identifier")
        print("- user_id: User identifier")
        print("- message_type: 'user' or 'assistant'")
        print("- content: Message content")
        print("- agent_name: Agent that handled the message")
        print("- metadata: JSON metadata")
        print("- timestamp: Unix timestamp in milliseconds")
        print("- created_at: Database creation timestamp")
        print("- updated_at: Last update timestamp")
        print("- is_deleted: Soft delete flag")
        
    except Exception as e:
        print(f" Error creating logs table: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        await service.close()


if __name__ == "__main__":
    print(" Starting logs table creation")
    print("Make sure you have set NEON_DATABASE_URL environment variable")
    print()
    
    asyncio.run(create_logs_table())
