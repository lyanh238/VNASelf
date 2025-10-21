"""
Script chạy tất cả visualizations cho LangGraph
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_visualization_directory():
    """Tạo thư mục visualization nếu chưa có."""
    os.makedirs("visualization", exist_ok=True)
    os.makedirs("visualization/diagrams", exist_ok=True)
    os.makedirs("visualization/exports", exist_ok=True)

def run_mermaid_diagrams():
    """Tạo Mermaid diagrams."""
    print(" Creating Mermaid Diagrams...")
    
    try:
        from create_mermaid_diagram import save_diagrams
        save_diagrams()
        print(" Mermaid diagrams created successfully!")
    except Exception as e:
        print(f" Error creating Mermaid diagrams: {str(e)}")

async def run_langsmith_visualization():
    """Chạy LangSmith visualization."""
    print("\ Running LangSmith Visualization...")
    
    try:
        from langsmith_integration import LangSmithVisualizer
        
        visualizer = LangSmithVisualizer()
        await visualizer.run_visualized_demo()
        print(" LangSmith visualization completed!")
        
    except Exception as e:
        print(f" Error running LangSmith visualization: {str(e)}")

async def run_graph_visualization():
    """Chạy graph visualization demo."""
    print("\n Running Graph Visualization Demo...")
    
    try:
        from graph_visualization import demo_visualization
        await demo_visualization()
        print(" Graph visualization demo completed!")
        
    except Exception as e:
        print(f" Error running graph visualization: {str(e)}")

def create_visualization_summary():
    """Tạo tóm tắt visualization."""
    summary = f"""
# LangGraph Visualization Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

##  Generated Files

### Mermaid Diagrams
- `langgraph_flow.mmd` - Basic LangGraph flow
- `detailed_flow.mmd` - Detailed flow with database
- `agent_interaction.mmd` - Sequence diagram
- `data_flow.mmd` - Data flow architecture

### Python Scripts
- `graph_visualization.py` - LangGraph with detailed nodes
- `langsmith_integration.py` - LangSmith tracing integration
- `create_mermaid_diagram.py` - Mermaid diagram generator

### Documentation
- `README_LANGSMITH.md` - LangSmith setup guide

##  Visualization Types

### 1. LangSmith Dashboard
- Real-time tracing
- Performance analytics
- Error monitoring
- Cost tracking

### 2. Mermaid Diagrams
- Flow charts
- Sequence diagrams
- Architecture diagrams
- Data flow diagrams

### 3. Console Visualization
- Step-by-step processing
- Agent routing decisions
- Database operations
- Response formatting

##  How to Use

### View Mermaid Diagrams
1. Copy content from .mmd files
2. Paste into https://mermaid.live/
3. Or use Mermaid extension in VS Code

### View LangSmith Traces
1. Set LANGCHAIN_API_KEY environment variable
2. Run: `python visualization/langsmith_integration.py`
3. Visit: https://smith.langchain.com/

### Run Graph Demo
1. Run: `python visualization/graph_visualization.py`
2. Follow console output for step-by-step visualization

##  Graph Components

### Nodes
- Input Processor
- Supervisor Agent
- Health Agent
- Calendar Agent
- Tools
- Response Formatter

### Routing Logic
- Health keywords → Health Agent
- Calendar keywords → Calendar Agent
- Tool requirements → Tools
- General queries → Direct response

### Data Flow
- User Input → Processing → Agent Selection → Response → Database Logging
- LangSmith tracing throughout the entire flow

## Configuration

### Environment Variables
```bash
export LANGCHAIN_API_KEY="your_langsmith_api_key"
export LANGCHAIN_PROJECT="multi-agent-system"
export LANGCHAIN_TRACING_V2=true
export OPENAI_API_KEY="your_openai_api_key"
export NEON_DATABASE_URL="your_neon_database_url"
```

### Dependencies
```bash
pip install langsmith langchain langgraph mermaid
```

##  Benefits

1. **Debugging**: Visualize where issues occur
2. **Optimization**: Identify performance bottlenecks
3. **Understanding**: See how agents interact
4. **Monitoring**: Track system behavior over time
5. **Documentation**: Visual system architecture
    """
    
    with open("visualization/SUMMARY.md", "w", encoding="utf-8") as f:
        f.write(summary)
    
    print(" Visualization summary created!")

async def main():
    """Main function to run all visualizations."""
    print(" LangGraph Visualization Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create directories
    create_visualization_directory()
    
    # Run Mermaid diagrams
    run_mermaid_diagrams()
    
    # Run graph visualization demo
    await run_graph_visualization()
    
    # Run LangSmith visualization (if API key available)
    if os.getenv("LANGCHAIN_API_KEY"):
        await run_langsmith_visualization()
    else:
        print("\n⚠ LANGCHAIN_API_KEY not set - skipping LangSmith visualization")
        print("   Set LANGCHAIN_API_KEY to enable LangSmith features")
    
    # Create summary
    create_visualization_summary()
    
    print("\n All visualizations completed!")
    print("\n Check the 'visualization' directory for generated files")
    print(" View Mermaid diagrams at: https://mermaid.live/")
    print(" View LangSmith traces at: https://smith.langchain.com/")

if __name__ == "__main__":
    asyncio.run(main())
