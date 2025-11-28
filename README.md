# GeminiRAG - Document Q&A with Multi-Agent RAG

A professional document question-answering system powered by Google's Gemini AI with a multi-agent architecture (Planner → Judge → Synthesizer).

## Features

- 🎨 **Modern UI** - Professional dark theme with glassmorphism design
- 🤖 **Multi-Agent RAG** - Planner-Judge-Synthesizer orchestration for accurate answers
- 📚 **Document Management** - Upload and index TXT/MD/PDF files
- 🔍 **Smart Search** - Vector-based semantic search across documents
- 💬 **Streaming Responses** - Real-time answer generation
- 🔧 **Tool Visibility** - See which documents are being searched (optional)
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (HTML/CSS/JS)                  │
│               GeminiRAG/react_frontend/index.html           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Server (Port 5001)                    │
│               GeminiRAG/backend/api_server.py               │
│  • /api/ask - Streaming Q&A                                │
│  • /api/upload-file - File upload                          │
│  • /api/list-files - List documents                        │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
┌─────────────────────┐      ┌─────────────────────┐
│   Orchestrator      │      │  Document Service   │
│  (Planner+Judge)    │      │    (Port 8000)      │
│                     │      │ GeminiRAG/services/ │
│ • Planner Agent     │      │                     │
│ • Judge Agent       │      │ • Vector search     │
│ • Tool Executor     │◄─────┤ • Chunking          │
│ • Synthesizer       │      │ • Persistence       │
└─────────────────────┘      └─────────────────────┘
```

## Quick Start

### 1. Prerequisites

- Python 3.9+
- Google API Key ([Get one here](https://aistudio.google.com/app/apikey))

### 2. Installation

```bash
cd GeminiRAG

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and add your Google API key
nano .env  # or use your preferred editor
```

### 3. Run the Application

**Option A: Using the startup script (recommended)**

```bash
cd GeminiRAG
./start.sh
```

**Option B: Manual startup**

```bash
cd GeminiRAG

# Terminal 1: Start document service
uvicorn services.api:app --port 8000 --reload

# Terminal 2: Start API server
python backend/api_server.py

# Terminal 3: Start Frontend Server
cd react_frontend
python -m http.server 8080

# Open frontend
open http://localhost:8080
```

### 4. Use the Application

1. **Upload Documents**: Drag and drop `.txt`, `.md`, or `.pdf` files
2. **Ask Questions**: Type your question in the chat input
3. **View Answers**: Watch as the AI streams the answer in real-time
4. **Check Sources**: See which documents were used (citations)

## Project Structure

```
GeminiRAG/
├── backend/                 # Backend Logic & API Server
│   ├── agents/              # Agent implementations (Planner, Judge, Synthesizer)
│   ├── api_server.py        # Main API server
│   ├── orchestrator.py      # Planner-Judge orchestration
│   ├── http_tools.py        # Document retrieval tools
│   ├── config.py            # Configuration
│   ├── models.py            # Data models
│   └── logger.py            # Logging utilities
├── services/                # Document Service
│   ├── api.py               # Document service API
│   ├── doc_store.py         # In-memory document store
│   └── persistence.py       # Document persistence
├── react_frontend/          # Professional Web UI (HTML/CSS/JS)
│   ├── index.html           # Main HTML
│   ├── style.css            # Styling
│   └── script.js            # Frontend logic
├── streamlit_frontend/      # Streamlit UI (Alternative)
│   └── streamlit_app.py     # Streamlit application
├── knowledge/               # Auto-loaded documents
├── documents/               # Persisted documents
├── archive/                 # Unused/Old files
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
├── start.sh                 # Startup script
└── README.md                # Inner README
```

## Documentation

- [**Getting Started**](GeminiRAG/GETTING_STARTED.md): Setup and run in 5 minutes.
- [**Codebase Overview**](GeminiRAG/docs/CODEBASE_OVERVIEW.md): High-level tour of folders and code.
- [**System Design**](GeminiRAG/docs/SYSTEM_DESIGN.md): Architecture diagram and detailed explanation.
- [**Search & Indexing System**](GeminiRAG/docs/SEARCH_AND_INDEXING.md): Deep dive into Hybrid Search.
- [**Google File Search Reference**](GeminiRAG/docs/google_file_search_reference.md): Original API docs.

## License

MIT License - See LICENSE file for details
