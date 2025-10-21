"""
LangSmith Integration for LangGraph Visualization
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langsmith import Client
from langchain_core.tracers import LangChainTracer
from langchain_core.callbacks import CallbackManager
from langchain_openai import ChatOpenAI

from core.multi_agent_system import MultiAgentSystem
from config import Config


class LangSmithVisualizer:
    """LangSmith integration for visualizing Multi-Agent System."""
    
    def __init__(self):
        self.client = None
        self.tracer = None
        self.project_name = "multi-agent-system"
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def initialize(self):
        """Initialize LangSmith client and tracer."""
        try:
            # Check for LangSmith API key
            if not os.getenv("LANGCHAIN_API_KEY"):
            
                print("⚠ LANGCHAIN_API_KEY not set - LangSmith features disabled")
                return False
            self.client = Client()
            self.tracer = LangChainTracer(project_name=self.project_name)
            
            print(f" LangSmith initialized")
            print(f"   Project: {self.project_name}")
            print(f"   Session: {self.session_id}")
            print(f"   Dashboard: https://smith.langchain.com/")
            
            return True
            
        except Exception as e:
            print(f" LangSmith initialization failed: {str(e)}")
            return False
    
    async def run_visualized_demo(self):
        """Chạy demo với LangSmith tracing."""
        print(" LangSmith Visualization Demo")
        print("=" * 60)
        
        if not self.initialize():
            print("Skipping LangSmith features...")
            return
        
        # Initialize Multi-Agent System
        system = MultiAgentSystem()
        
        try:
            await system.initialize()
            
            # Demo queries with different complexity levels
            demo_scenarios = [
                {
                    "name": "Health Consultation",
                    "query": "Tôi bị đau đầu và sốt 38.5 độ, phải làm sao?",
                    "expected_agent": "Health Agent"
                },
                {
                    "name": "Calendar Management", 
                    "query": "Show me my calendar for today and create a meeting at 2 PM",
                    "expected_agent": "Calendar Agent"
                },
                {
                    "name": "General Query",
                    "query": "What's the weather like today?",
                    "expected_agent": "Supervisor Agent"
                },
                {
                    "name": "Complex Health Query",
                    "query": "Tôi bị đau bụng dữ dội kèm sốt cao, có nguy hiểm không? Có thể tạo lịch hẹn bác sĩ không?",
                    "expected_agent": "Multi-Agent"
                }
            ]
            
            print(f"\n Running {len(demo_scenarios)} demo scenarios...")
            print("Each scenario will be traced in LangSmith")
            print("-" * 60)
            
            for i, scenario in enumerate(demo_scenarios, 1):
                print(f"\n[Scenario {i}] {scenario['name']}")
                print(f"Query: {scenario['query']}")
                print(f"Expected Agent: {scenario['expected_agent']}")
                print("-" * 40)
                
                # Process with tracing
                response = await self.process_with_tracing(
                    system, 
                    scenario['query'],
                    scenario_name=scenario['name']
                )
                
                print(f"Response: {response[:150]}...")
                print(f" Scenario {i} completed - check LangSmith dashboard")
            
            # Show session summary
            await self.show_session_summary()
            
        except Exception as e:
            print(f" Demo failed: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            await system.close()
    
    async def process_with_tracing(self, system, query: str, scenario_name: str = None):
        """Process query with LangSmith tracing."""
        try:
            # Create callback manager with tracer
            callback_manager = CallbackManager([self.tracer])
            
            # Process message with tracing
            response = await system.process_message(
                query,
                thread_id=f"langsmith_demo_{scenario_name or 'general'}",
                user_id="langsmith_user"
            )
            
            return response
            
        except Exception as e:
            print(f"Error processing with tracing: {str(e)}")
            return f"Error: {str(e)}"
    
    async def show_session_summary(self):
        """Hiển thị tóm tắt session trong LangSmith."""
        if not self.client:
            return
        
        try:
            print(f"\n LangSmith Session Summary")
            print("=" * 40)
            
            # Get recent runs for this project
            runs = list(self.client.list_runs(project_name=self.project_name, limit=10))
            
            print(f"Total runs in session: {len(runs)}")
            
            # Group by scenario
            scenarios = {}
            for run in runs:
                if hasattr(run, 'extra') and run.extra:
                    scenario = run.extra.get('scenario', 'Unknown')
                    if scenario not in scenarios:
                        scenarios[scenario] = []
                    scenarios[scenario].append(run)
            
            for scenario, runs_list in scenarios.items():
                print(f"\n {scenario}: {len(runs_list)} runs")
                for run in runs_list[:3]:  # Show first 3 runs
                    status = "" if run.status == "success" else ""
                    duration = f"{run.total_time:.2f}s" if run.total_time else "N/A"
                    print(f"   {status} {run.name} ({duration})")
            
            print(f"\n View in LangSmith Dashboard:")
            print(f"   https://smith.langchain.com/projects")
            print(f"   Project: {self.project_name}")
            
        except Exception as e:
            print(f"Error getting session summary: {str(e)}")
    
    def create_graph_visualization_guide(self):
        """Tạo hướng dẫn visualization."""
        guide = """
# LangGraph Visualization Guide

##  LangSmith Dashboard Features

### 1. Trace View
- Xem chi tiết từng bước xử lý
- Timeline của các agent calls
- Input/Output của mỗi node
- Error tracking và debugging

### 2. Graph Visualization
- Sơ đồ luồng hoạt động
- Dependencies giữa các components
- Performance metrics
- Agent routing decisions

### 3. Analytics
- Response time analysis
- Agent usage statistics
- Error rate monitoring
- Cost tracking

##  Setup Instructions

### 1. Environment Setup
```bash
export LANGCHAIN_API_KEY="your_langsmith_api_key"
export LANGCHAIN_PROJECT="multi-agent-system"
export LANGCHAIN_TRACING_V2=true
```

### 2. Run Visualization
```bash
python visualization/langsmith_integration.py
```

### 3. View in Dashboard
1. Go to https://smith.langchain.com/
2. Navigate to your project
3. View traces and analytics

##  Graph Components

### Nodes
- **Input Processor**: Handles user input
- **Supervisor**: Routes to appropriate agent
- **Health Agent**: Medical consultations
- **Calendar Agent**: Calendar operations
- **Tools**: MCP function execution
- **Response Formatter**: Final output formatting

### Edges
- **Conditional Routing**: Based on content analysis
- **Sequential Processing**: Linear flow
- **Feedback Loops**: Tool results back to supervisor

##  Visualization Types

1. **Flow Diagram**: Basic agent flow
2. **Sequence Diagram**: Time-based interactions
3. **Data Flow**: Information movement
4. **Architecture Diagram**: System components

##  Debugging Tips

1. **Check Trace Details**: Look for errors in specific nodes
2. **Analyze Routing**: See why certain agents were chosen
3. **Monitor Performance**: Track response times
4. **Review Logs**: Check database operations
        """
        
        with open("visualization/README_LANGSMITH.md", "w", encoding="utf-8") as f:
            f.write(guide)
        
        print(" Created LangSmith visualization guide")
        return guide


async def main():
    """Main function to run LangSmith visualization."""
    print(" LangSmith LangGraph Visualization")
    print("=" * 60)
    
    visualizer = LangSmithVisualizer()
    
    # Create visualization guide
    visualizer.create_graph_visualization_guide()
    
    # Run demo
    await visualizer.run_visualized_demo()
    
    print("\n🎉 Visualization complete!")
    print("Check the LangSmith dashboard for detailed traces and graphs.")


if __name__ == "__main__":
    asyncio.run(main())
