# X23D8 Multi-Agent System

A comprehensive multi-agent system with React frontend and FastAPI backend.

## Project Structure

```
├── backend/                 # FastAPI backend
│   ├── agents/             # Agent implementations
│   ├── core/               # Core system components
│   ├── models/             # Data models
│   ├── services/           # Business logic services
│   ├── server/             # Additional server components
│   ├── scripts/            # Utility scripts
│   ├── visualization/      # Visualization components
│   ├── backend_api.py      # Main FastAPI application
│   ├── main.py             # Entry point
│   └── requirements.txt   # Python dependencies
├── frontend/               # React frontend
│   ├── src/                # React source code
│   ├── public/             # Static assets
│   ├── package.json        # Node.js dependencies
│   └── vite.config.js      # Vite configuration
└── docs/                   # Documentation
```

## Quick Start

### Prerequisites
- Node.js (v16 or higher)
- Python 3.8+
- pip

### Installation

1. **Install frontend dependencies:**
```bash
   cd frontend
   npm install
```

2. **Install backend dependencies:**
```bash
   cd backend
pip install -r requirements.txt
```

### Development

**Option 1: Run both frontend and backend together:**
```bash
npm install concurrently --save-dev
```

```bash
npm run dev
```

**Option 2: Run separately:**
```bash
# Terminal 1 - Frontend
npm run frontend

# Terminal 2 - Backend  
npm run backend
```

### Available Scripts

- `npm run dev` - Runs both frontend and backend concurrently
- `npm run frontend` - Runs only the React frontend (port 5173)
- `npm run backend` - Runs only the FastAPI backend (port 8000)
- `npm run build` - Builds the frontend for production

## API Endpoints

The backend runs on `http://localhost:8000` with the following main endpoints:

- `POST /api/chat` - Send messages to the multi-agent system
- `GET /api/chat/history/{thread_id}` - Get chat history
- `GET /docs` - API documentation (Swagger UI)

## Frontend

The React frontend runs on `http://localhost:5173` and provides:

- Interactive chat interface
- Multi-agent system integration
- Real-time communication with backend
- Responsive design with dark/light theme

## Backend

The FastAPI backend provides:

- Multi-agent system orchestration
- Chat history management
- WebSocket support for real-time communication
- CORS configuration for frontend integration
