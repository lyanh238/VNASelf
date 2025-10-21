# LangGraph Visualization System

Hệ thống visualization toàn diện cho Multi-Agent System sử dụng LangGraph, LangChain và LangSmith.

##  Tổng quan

Hệ thống này cung cấp nhiều cách để visualize và monitor hoạt động của Multi-Agent System:

1. **LangSmith Dashboard** - Real-time tracing và monitoring
2. **Mermaid Diagrams** - Sơ đồ luồng hoạt động
3. **Console Visualization** - Step-by-step processing
4. **Database Logging** - Lưu trữ logs với timestamp

##  Quick Start

### 1. Chạy Demo Cơ bản

```bash
python demo_visualization.py
```

### 2. Tạo Mermaid Diagrams

```bash
cd visualization
python create_mermaid_diagram.py
```

### 3. Chạy Tất cả Visualizations

```bash
python visualization/run_visualizations.py
```

##  Graph Architecture

### LangGraph Flow

```
User Input → Input Processor → Supervisor Agent
                                    ↓
                    ┌─────────────────┼─────────────────┐
                    ↓                 ↓                 ↓
            Health Agent      Calendar Agent      Tools
                    ↓                 ↓                 ↓
                    └─────────────────┼─────────────────┘
                                    ↓
                            Response Formatter → Final Response
```

### Nodes Chi tiết

1. **Input Processor** 
   - Xử lý input từ user
   - Log vào Neon Database
   - Forward đến supervisor

2. **Supervisor Agent** 
   - Phân tích nội dung câu hỏi
   - Quyết định routing đến agent phù hợp
   - Quản lý workflow tổng thể

3. **Health Agent** 
   - Xử lý câu hỏi sức khỏe
   - Tư vấn y tế dựa trên triệu chứng
   - Sử dụng medical knowledge base

4. **Calendar Agent** 
   - Quản lý lịch và sự kiện
   - Tích hợp Google Calendar qua MCP
   - Tạo/sửa/xóa events

5. **Tools** 
   - Thực thi MCP functions
   - External API calls
   - Utility functions

6. **Response Formatter** 
   - Format response cuối cùng
   - Log vào database
   - Return to user

##  Visualization Types

### 1. LangSmith Dashboard

**File**: `visualization/langsmith_integration.py`

Real-time tracing và monitoring trong LangSmith dashboard.

**Features**:
- Trace từng bước xử lý
- Performance analytics
- Error monitoring
- Cost tracking
- Agent routing decisions

**Setup**:
```bash
export LANGCHAIN_API_KEY="your_langsmith_api_key"
export LANGCHAIN_TRACING_V2=true
python visualization/langsmith_integration.py
```

### 2. Mermaid Diagrams

**Files**: `visualization/*.mmd`

Tạo sơ đồ Mermaid cho documentation và presentation.

**Generated Files**:
- `langgraph_flow.mmd` - Basic LangGraph flow
- `detailed_flow.mmd` - Detailed flow with database
- `agent_interaction.mmd` - Sequence diagram
- `data_flow.mmd` - Data flow architecture

**View**: Copy content to https://mermaid.live/

### 3. Console Visualization

**File**: `visualization/graph_visualization.py`

Step-by-step visualization trong console.

**Features**:
- Detailed node processing
- Agent routing decisions
- Database operations
- Response formatting

### 4. Database Logging

**Table**: `logs` trong Neon Database

Lưu trữ toàn bộ conversation với timestamp chính xác.

**Schema**:
```sql
CREATE TABLE logs (
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
```

##  Configuration

### Environment Variables

```bash
# Required
export OPENAI_API_KEY="your_openai_api_key"
export NEON_DATABASE_URL="your_neon_database_url"

# Optional (for LangSmith)
export LANGCHAIN_API_KEY="your_langsmith_api_key"
export LANGCHAIN_PROJECT="multi-agent-system"
export LANGCHAIN_TRACING_V2=true
```

### Dependencies

```bash
pip install langsmith langchain langgraph mermaid
```

##  Performance Monitoring

### Metrics Tracked

1. **Response Time**
   - Total processing time
   - Per-agent processing time
   - Database operation time

2. **Throughput**
   - Messages per minute
   - Concurrent users
   - System capacity

3. **Error Rates**
   - Agent errors
   - Database errors
   - API failures

4. **Resource Usage**
   - Memory consumption
   - CPU usage
   - Database connections

##  Routing Logic

### Content Analysis

```python
def router_condition(state):
    content = state["messages"][-1].content.lower()
    
    # Health keywords
    health_keywords = ['đau', 'sốt', 'bệnh', 'sức khỏe', 'triệu chứng', 'thuốc', 'bác sĩ']
    if any(keyword in content for keyword in health_keywords):
        return "health_agent"
    
    # Calendar keywords
    calendar_keywords = ['lịch', 'calendar', 'sự kiện', 'họp', 'meeting', 'appointment']
    if any(keyword in content for keyword in calendar_keywords):
        return "calendar_agent"
    
    # Tool required
    if "tool" in content or "function" in content:
        return "tools"
    
    # Default
    return "response_formatter"
```

### Agent Selection

- **Health Agent**: Medical consultations, symptom analysis
- **Calendar Agent**: Event management, scheduling
- **Tools**: External API calls, MCP functions
- **Direct Response**: General queries, weather, etc.

## 🔍 Debugging & Troubleshooting

### Common Issues

1. **LangSmith Not Working**
   - Check LANGCHAIN_API_KEY
   - Verify project permissions
   - Check network connectivity

2. **Mermaid Diagrams Not Rendering**
   - Validate Mermaid syntax
   - Check for special characters
   - Use online Mermaid editor

3. **Database Connection Issues**
   - Check NEON_DATABASE_URL
   - Verify database permissions
   - Check network connectivity

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with verbose output
python visualization/graph_visualization.py --verbose
```

##  Examples

### Basic Usage

```python
from core.multi_agent_system import MultiAgentSystem

# Initialize system
system = MultiAgentSystem()
await system.initialize()

# Process message
response = await system.process_message(
    "Tôi bị đau đầu, phải làm sao?",
    thread_id="demo_thread",
    user_id="demo_user"
)

# Get conversation history
history = await system.get_chat_history("demo_thread")
```

### LangSmith Integration

```python
from visualization.langsmith_integration import LangSmithVisualizer

visualizer = LangSmithVisualizer()
await visualizer.run_visualized_demo()
```

### Custom Visualization

```python
from visualization.graph_visualization import VisualizedMultiAgentSystem

system = VisualizedMultiAgentSystem()
await system.initialize()

response = await system.process_message_with_visualization(
    "Show me my calendar",
    thread_id="custom_thread",
    user_id="custom_user"
)
```

##  Customization

### Adding New Agents

1. Tạo agent class mới
2. Thêm vào routing logic
3. Update visualization nodes
4. Test với LangSmith tracing

### Custom Visualizations

1. Tạo Mermaid diagram mới
2. Update graph representation
3. Add custom metrics
4. Integrate với monitoring tools

##  Generated Files

### Mermaid Diagrams
- `visualization/langgraph_flow.mmd`
- `visualization/detailed_flow.mmd`
- `visualization/agent_interaction.mmd`
- `visualization/data_flow.mmd`

### Python Scripts
- `visualization/graph_visualization.py`
- `visualization/langsmith_integration.py`
- `visualization/create_mermaid_diagram.py`
- `visualization/run_visualizations.py`

### Documentation
- `visualization/README.md`
- `visualization/README_LANGSMITH.md`
- `visualization/SUMMARY.md`

##  Best Practices

1. **Always Enable Tracing**: Sử dụng LangSmith cho production
2. **Monitor Performance**: Theo dõi metrics thường xuyên
3. **Document Changes**: Update diagrams khi thay đổi system
4. **Test Visualizations**: Verify diagrams hoạt động đúng
5. **Optimize Based on Data**: Sử dụng analytics để cải thiện

##  Changelog

### v1.0.0
-  LangSmith integration
-  Mermaid diagram generation
-  Console visualization
-  Graph representation
-  Database logging với timestamp
-  Performance monitoring
-  Documentation và examples
-  Multi-Agent routing
-  Error handling và debugging

## 🔗 Links

- **LangSmith Dashboard**: https://smith.langchain.com/
- **Mermaid Live Editor**: https://mermaid.live/
- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **LangChain Documentation**: https://python.langchain.com/
