"""
Demo script để chạy LangGraph visualization
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.multi_agent_system import MultiAgentSystem
from config import Config


async def demo_basic_visualization():
    """Demo cơ bản với console visualization."""
    
    print("LangGraph Visualization Demo")
    print("=" * 60)
    
    # Check configuration
    if not Config.validate():
        print("Please set up environment variables first!")
        print("Required: OPENAI_API_KEY, NEON_DATABASE_URL")
        return
    
    # Initialize system
    print("Initializing Multi-Agent System...")
    system = MultiAgentSystem()
    
    try:
        await system.initialize()
        print("System ready!")
        
        # Demo queries
        demo_queries = [
            "Tôi bị đau đầu và sốt, phải làm sao?",
            "Show me my calendar for today",
            "What's the weather like?",
            "Tạo cuộc họp lúc 2 giờ chiều mai"
        ]
        
        print(f"\nRunning {len(demo_queries)} demo queries...")
        print("-" * 60)
        
        for i, query in enumerate(demo_queries, 1):
            print(f"\n[Query {i}] {query}")
            print("Processing...")
            
            try:
                response = await system.process_message(
                    query, 
                    thread_id=f"demo_thread_{i}",
                    user_id="demo_user"
                )
                
                print(f"Response: {response[:150]}...")
                
                # Show conversation history
                history = await system.get_chat_history(f"demo_thread_{i}", limit=2)
                print(f"Logged {len(history)} messages to database")
                
            except Exception as e:
                print(f"Error: {str(e)}")
            
            print("-" * 40)
        
        print("\nDemo completed successfully!")
        print("\nKey Features Demonstrated:")
        print("- Multi-Agent routing")
        print("- Database logging")
        print("- Thread management")
        print("- User tracking")
        
    except Exception as e:
        print(f"Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await system.close()


def show_mermaid_diagrams():
    """Hiển thị thông tin về Mermaid diagrams."""
    
    print("\nMermaid Diagrams Available:")
    print("=" * 40)
    
    diagrams = [
        ("langgraph_flow.mmd", "Basic LangGraph flow"),
        ("detailed_flow.mmd", "Detailed flow with database"),
        ("agent_interaction.mmd", "Sequence diagram"),
        ("data_flow.mmd", "Data flow architecture")
    ]
    
    for filename, description in diagrams:
        filepath = f"visualization/{filename}"
        if os.path.exists(filepath):
            print(f"✓ {filename}: {description}")
        else:
            print(f"✗ {filename}: Not found")
    
    print("\nTo view diagrams:")
    print("1. Copy content from .mmd files")
    print("2. Paste into https://mermaid.live/")
    print("3. Or use Mermaid extension in VS Code")


def show_langsmith_setup():
    """Hiển thị hướng dẫn setup LangSmith."""
    
    print("\nLangSmith Setup:")
    print("=" * 30)
    
    if os.getenv("LANGCHAIN_API_KEY"):
        print("✓ LANGCHAIN_API_KEY is set")
        print("✓ LangSmith tracing enabled")
        print("\nTo view traces:")
        print("1. Run: python visualization/langsmith_integration.py")
        print("2. Visit: https://smith.langchain.com/")
    else:
        print("✗ LANGCHAIN_API_KEY not set")
        print("\nTo enable LangSmith:")
        print("1. Get API key from https://smith.langchain.com/")
        print("2. Set: export LANGCHAIN_API_KEY='your_key'")
        print("3. Set: export LANGCHAIN_TRACING_V2=true")


async def main():
    """Main function."""
    
    print("LangGraph Visualization Suite")
    print("=" * 60)
    
    # Show available diagrams
    show_mermaid_diagrams()
    
    # Show LangSmith setup
    show_langsmith_setup()
    
    # Run basic demo
    print("\n" + "=" * 60)
    await demo_basic_visualization()
    
    print("\n" + "=" * 60)
    print("Visualization Demo Complete!")
    print("\nNext Steps:")
    print("1. View Mermaid diagrams at https://mermaid.live/")
    print("2. Set up LangSmith for advanced tracing")
    print("3. Run: python visualization/run_visualizations.py")


if __name__ == "__main__":
    asyncio.run(main())
