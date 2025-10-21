# LangGraph Visualization Suite

Bộ công cụ visualization cho Multi-Agent System sử dụng LangGraph, LangChain và LangSmith.

## 🎯 Tổng quan

Hệ thống này cung cấp nhiều cách để visualize hoạt động của Multi-Agent System:

1. **LangSmith Dashboard** - Real-time tracing và monitoring
2. **Mermaid Diagrams** - Sơ đồ luồng hoạt động
3. **Console Visualization** - Step-by-step processing
4. **Graph Representation** - Cấu trúc graph chi tiết

##  Cài đặt

### 1. Dependencies

```bash
pip install langsmith langchain langgraph mermaid
```

### 2. Environment Variables

```bash
# Required
export OPENAI_API_KEY="your_openai_api_key"
export NEON_DATABASE_URL="your_neon_database_url"

# Optional (for LangSmith)
export LANGCHAIN_API_KEY="your_langsmith_api_key"
export LANGCHAIN_PROJECT="multi-agent-system"
export LANGCHAIN_TRACING_V2=true
```

##  Các loại Visualization

### 1. LangSmith Dashboard

**File**: `langsmith_integration.py`

Real-time tracing và monitoring trong LangSmith dashboard.

```bash
python visualization/langsmith_integration.py
```

**Features**:
- Trace từng bước xử lý
- Performance analytics
- Error monitoring
- Cost tracking
- Agent routing decisions

### 2. Mermaid Diagrams

**File**: `create_mermaid_diagram.py`

Tạo sơ đồ Mermaid cho documentation và presentation.

```bash
python visualization/create_mermaid_diagram.py
```

**Generated Files**:
- `langgraph_flow.mmd` - Basic LangGraph flow
- `detailed_flow.mmd` - Detailed flow with database
- `agent_interaction.mmd` - Sequence diagram
- `data_flow.mmd` - Data flow architecture

**View**: Copy content to https://mermaid.live/

### 3. Console Visualization

**File**: `graph_visualization.py`

Step-by-step visualization trong console.

```bash
python visualization/graph_visualization.py
```

**Features**:
- Detailed node processing
- Agent routing decisions
- Database operations
- Response formatting

### 4. All-in-One Runner

**File**: `run_visualizations.py`

Chạy tất cả visualizations cùng lúc.

```bash
python visualization/run_visualizations.py
```

##  Graph Architecture

### Nodes

1. **Input Processor**
   - Xử lý input từ user
   - Log vào database
   - Forward đến supervisor

2. **Supervisor Agent** 
   - Phân tích nội dung
   - Quyết định routing
   - Quản lý workflow

3. **Health Agent** 
   - Xử lý câu hỏi sức khỏe
   - Tư vấn y tế
   - Sử dụng medical knowledge

4. **Calendar Agent** 
   - Quản lý lịch
   - Tạo/sửa/xóa events
   - Tích hợp Google Calendar

5. **Tools** 
   - Thực thi MCP functions
   - External API calls
   - Utility functions

6. **Response Formatter** 
   - Format response cuối cùng
   - Log vào database
   - Return to user

### Routing Logic

```python
def router_condition(state):
    content = state["messages"][-1].content.lower()
    
    # Health keywords
    if any(keyword in content for keyword in ['đau', 'sốt', 'bệnh']):
        return "health_agent"
    
    # Calendar keywords  
    if any(keyword in content for keyword in ['lịch', 'meeting', 'event']):
        return "calendar_agent"
    
    # Tool required
    if "tool" in content:
        return "tools"
    
    # Default
    return "response_formatter"
```

##  LangSmith Features

### Trace View

- **Timeline**: Thứ tự thực hiện các operations
- **Input/Output**: Dữ liệu vào/ra của mỗi node
- **Duration**: Thời gian xử lý từng bước
- **Errors**: Lỗi và stack trace

### Graph Visualization

- **Node Dependencies**: Mối quan hệ giữa các nodes
- **Data Flow**: Luồng dữ liệu qua hệ thống
- **Performance Metrics**: Response time, throughput
- **Agent Usage**: Thống kê sử dụng agents

### Analytics

- **Response Time Analysis**: Phân tích thời gian phản hồi
- **Agent Usage Statistics**: Thống kê sử dụng agents
- **Error Rate Monitoring**: Theo dõi tỷ lệ lỗi
- **Cost Tracking**: Theo dõi chi phí API calls

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

##  Troubleshooting

### Common Issues

1. **LangSmith Not Working**
   - Check LANGCHAIN_API_KEY
   - Verify project permissions
   - Check network connectivity

2. **Mermaid Diagrams Not Rendering**
   - Validate Mermaid syntax
   - Check for special characters
   - Use online Mermaid editor

3. **Console Visualization Issues**
   - Check agent initialization
   - Verify database connection
   - Review error logs

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
from visualization.graph_visualization import VisualizedMultiAgentSystem

# Initialize system
system = VisualizedMultiAgentSystem()
await system.initialize()

# Process with visualization
response = await system.process_message_with_visualization(
    "Tôi bị đau đầu, phải làm sao?",
    thread_id="demo_thread",
    user_id="demo_user"
)
```

### LangSmith Integration

```python
from visualization.langsmith_integration import LangSmithVisualizer

visualizer = LangSmithVisualizer()
await visualizer.run_visualized_demo()
```

##  Best Practices

1. **Always Enable Tracing**: Sử dụng LangSmith cho production
2. **Monitor Performance**: Theo dõi metrics thường xuyên
3. **Document Changes**: Update diagrams khi thay đổi system
4. **Test Visualizations**: Verify diagrams hoạt động đúng
5. **Optimize Based on Data**: Sử dụng analytics để cải thiện

##  Changelog

### v1.0.0
- ✅ LangSmith integration
- ✅ Mermaid diagram generation
- ✅ Console visualization
- ✅ Graph representation
- ✅ Performance monitoring
- ✅ Documentation và examples
