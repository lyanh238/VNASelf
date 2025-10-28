"""
Script to create conversations table in Neon Database
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.conversation_service import ConversationService
from config import Config


async def create_conversations_table():
    """Create conversations table in Neon Database."""
    
    print("Creating conversations table in Neon Database")
    print("=" * 60)
    
    # Check configuration
    if not Config.NEON_DATABASE_URL:
        print("ERROR: NEON_DATABASE_URL not set!")
        print("Please set the environment variable:")
        print("export NEON_DATABASE_URL='postgresql://username:password@host:port/database'")
        return
    
    # Initialize service
    service = ConversationService()
    
    try:
        await service.initialize()
        print("✅ Conversations table created successfully!")
        print("✅ Conversation Service initialized")
        
    except Exception as e:
        print(f"❌ Error creating conversations table: {str(e)}")
        return
    
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(create_conversations_table())
