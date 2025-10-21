"""
Tạo sơ đồ Mermaid cho LangGraph visualization
"""

def create_langgraph_mermaid_diagram():
    """Tạo sơ đồ Mermaid cho Multi-Agent System."""
    
    mermaid_diagram = """
graph TD
    Start([User Input]) --> InputProcessor[ Input Processor<br/>Process & Log Input]
    
    InputProcessor --> Supervisor[ Supervisor Agent<br/>Route Decision]
    
    Supervisor --> |Health Keywords| HealthAgent[ Health Agent<br/>Medical Consultation]
    Supervisor --> |Calendar Keywords| CalendarAgent[ Calendar Agent<br/>Calendar Management]
    Supervisor --> |Tool Required| Tools[ Tools<br/>Execute Functions]
    Supervisor --> |Direct Response| ResponseFormatter[ Response Formatter<br/>Format Output]
    
    HealthAgent --> ResponseFormatter
    CalendarAgent --> ResponseFormatter
    Tools --> Supervisor
    
    ResponseFormatter --> End([Final Response])
    
    %% Styling
    classDef inputNode fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef agentNode fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef toolNode fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef outputNode fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef decisionNode fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    
    class Start,End inputNode
    class HealthAgent,CalendarAgent agentNode
    class Tools toolNode
    class ResponseFormatter outputNode
    class Supervisor decisionNode
    class InputProcessor decisionNode
    """
    
    return mermaid_diagram.strip()


def create_detailed_flow_diagram():
    """Tạo sơ đồ chi tiết hơn với database và logging."""
    
    mermaid_diagram = """
graph TD
    User[ User] --> |Message| InputProcessor[ Input Processor]
    
    InputProcessor --> |Log User Message| Database[( Neon Database<br/>logs table)]
    InputProcessor --> Supervisor[ Supervisor Agent<br/>Decision Engine]
    
    Supervisor --> |Analyze Content| Router{Router<br/>Content Analysis}
    
    Router --> |Health Keywords<br/>đau, sốt, bệnh| HealthAgent[ Health Agent<br/>Medical Consultation]
    Router --> |Calendar Keywords<br/>lịch, meeting, event| CalendarAgent[ Calendar Agent<br/>Calendar Operations]
    Router --> |Tool Required| Tools[ Tools<br/>MCP Functions]
    Router --> |General Query| ResponseFormatter[ Response Formatter]
    
    HealthAgent --> |Health Response| ResponseFormatter
    CalendarAgent --> |Calendar Response| ResponseFormatter
    Tools --> |Tool Result| Supervisor
    
    ResponseFormatter --> |Log Assistant Response| Database
    ResponseFormatter --> |Final Response| User
    
    %% Database Operations
    Database --> |Query History| HistoryRetrieval[ History Retrieval]
    HistoryRetrieval --> |Context| Supervisor
    
    %% LangSmith Tracing
    Supervisor -.-> |Trace| LangSmith[ LangSmith<br/>Tracing & Monitoring]
    HealthAgent -.-> |Trace| LangSmith
    CalendarAgent -.-> |Trace| LangSmith
    Tools -.-> |Trace| LangSmith
    
    %% Styling
    classDef userNode fill:#e3f2fd,stroke:#0277bd,stroke-width:3px
    classDef processNode fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    classDef agentNode fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef toolNode fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    classDef dbNode fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef decisionNode fill:#fff8e1,stroke:#f57c00,stroke-width:2px
    classDef traceNode fill:#f3e5f5,stroke:#7b1fa2,stroke-width:1px,stroke-dasharray: 5 5
    
    class User userNode
    class InputProcessor,ResponseFormatter processNode
    class HealthAgent,CalendarAgent agentNode
    class Tools toolNode
    class Database,HistoryRetrieval dbNode
    class Supervisor,Router decisionNode
    class LangSmith traceNode
    """
    
    return mermaid_diagram.strip()


def create_agent_interaction_diagram():
    """Tạo sơ đồ tương tác giữa các agent."""
    
    mermaid_diagram = """
sequenceDiagram
    participant U as  User
    participant IP as  Input Processor
    participant DB as  Database
    participant S as  Supervisor
    participant H as  Health Agent
    participant C as  Calendar Agent
    participant T as  Tools
    participant RF as  Response Formatter
    participant LS as  LangSmith
    
    U->>IP: Send Message
    IP->>DB: Log User Message
    IP->>S: Forward to Supervisor
    
    S->>LS: Start Trace
    S->>S: Analyze Content
    
    alt Health-related Query
        S->>H: Route to Health Agent
        H->>LS: Trace Health Processing
        H->>H: Process Medical Query
        H->>RF: Return Health Response
    else Calendar-related Query
        S->>C: Route to Calendar Agent
        C->>LS: Trace Calendar Processing
        C->>T: Use Calendar Tools
        T->>C: Return Tool Results
        C->>RF: Return Calendar Response
    else Tool Required
        S->>T: Execute Tools
        T->>LS: Trace Tool Execution
        T->>S: Return Tool Results
        S->>RF: Return Tool Response
    else General Query
        S->>RF: Direct Response
    end
    
    RF->>DB: Log Assistant Response
    RF->>U: Send Final Response
    LS->>LS: Complete Trace
    """
    
    return mermaid_diagram.strip()


def create_data_flow_diagram():
    """Tạo sơ đồ luồng dữ liệu."""
    
    mermaid_diagram = """
graph LR
    subgraph "Input Layer"
        UI[User Interface]
        API[API Endpoint]
    end
    
    subgraph "Processing Layer"
        IP[Input Processor]
        S[Supervisor Agent]
        H[Health Agent]
        C[Calendar Agent]
        T[Tools]
        RF[Response Formatter]
    end
    
    subgraph "Data Layer"
        DB[(Neon Database<br/>logs table)]
        MCP[MCP Service<br/>Google Calendar]
        LLM[OpenAI LLM]
    end
    
    subgraph "Monitoring Layer"
        LS[LangSmith<br/>Tracing]
        LOG[Application Logs]
    end
    
    UI --> IP
    API --> IP
    
    IP --> DB
    IP --> S
    
    S --> H
    S --> C
    S --> T
    S --> RF
    
    H --> LLM
    C --> MCP
    T --> MCP
    
    H --> RF
    C --> RF
    T --> S
    
    RF --> DB
    RF --> UI
    RF --> API
    
    S -.-> LS
    H -.-> LS
    C -.-> LS
    T -.-> LS
    
    IP -.-> LOG
    S -.-> LOG
    H -.-> LOG
    C -.-> LOG
    """
    
    return mermaid_diagram.strip()


def save_diagrams():
    """Lưu tất cả sơ đồ vào file."""
    
    diagrams = {
        "langgraph_flow.mmd": create_langgraph_mermaid_diagram(),
        "detailed_flow.mmd": create_detailed_flow_diagram(),
        "agent_interaction.mmd": create_agent_interaction_diagram(),
        "data_flow.mmd": create_data_flow_diagram()
    }
    
    for filename, content in diagrams.items():
        filepath = filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Saved: {filepath}")
    
    print(f"\nCreated {len(diagrams)} Mermaid diagrams!")
    print("\nTo view these diagrams:")
    print("1. Copy content to https://mermaid.live/")
    print("2. Or use Mermaid extension in VS Code")
    print("3. Or integrate with documentation tools")


if __name__ == "__main__":
    print("Creating LangGraph Mermaid Diagrams")
    print("=" * 50)
    
    save_diagrams()
    
    print("\nDiagram Types Created:")
    print("1. langgraph_flow.mmd - Basic LangGraph flow")
    print("2. detailed_flow.mmd - Detailed flow with database")
    print("3. agent_interaction.mmd - Sequence diagram")
    print("4. data_flow.mmd - Data flow architecture")
