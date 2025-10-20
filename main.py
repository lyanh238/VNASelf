"""
Main entry point for the Multi-Agent System
"""

import asyncio
import sys
from core import MultiAgentSystem


async def main():
    """Main function to run the multi-agent system."""
    print("\n Starting Multi-Agent System...\n")
    
    # Create the system
    system = MultiAgentSystem()
    
    try:
        # Initialize the system
        await system.initialize()
        
        # Choose mode
        print("\nChoose mode:")
        print("1. Run example demonstrations")
        print("2. Interactive chat")
        
        try:
            choice = input("\nEnter choice (1/2): ").strip()
            
            if choice == "1":
                await system.run_examples()
            else:
                await system.chat_interactive()
                
        except KeyboardInterrupt:
            print("\n\n Goodbye!")
        except Exception as e:
            print(f"\n Error: {str(e)}")
    
    finally:
        # Cleanup
        await system.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n Goodbye!")
        sys.exit(0)
