# GeminiRAG Web Layer

This directory contains the web layer for GeminiRAG, including **two separate UI implementations** and a shared FastAPI backend.

## 🎯 Two UIs Available

### 1. Test UI (Simple HTML/JS)

**File**: `test_ui.html`  
**Access**: http://localhost:6001 (served by backend)

**Purpose**: Quick testing and debugging during development

**Features**:
- ✅ Single HTML file (no build process)
- ✅ Upload files (PDF, TXT, MD)
- ✅ Manual text input for testing
- ✅ Hybrid search testing
- ✅ RAG question answering
- ✅ Collection statistics
- ✅ Clear all documents

**When to use**:
- Testing chunking strategies
- Debugging search algorithms
- Verifying document indexing
- Quick demos without frontend setup

---

### 2. Production UI (React)

**Directory**: `ui/`  
**Access**: http://localhost:5173 (Vite dev server)

**Purpose**: Production-ready chat interface for end users

**Features**:
- ✅ **Mode Selector**: Pro Mode (3-stage reasoning) vs Flash Mode (quick answers)
- ✅ **Streaming Responses**: Real-time token-by-token display
- ✅ **Multi-Stage Reasoning**: Collapsible sections for each stage
- ✅ **Rich Markdown**: Syntax-highlighted code, tables, lists
- ✅ **Clean References**: File-based citations with page numbers
- ✅ **Upload Tab**: Dedicated document management interface
- ✅ **Modern Design**: ChatGPT-inspired layout with TailwindCSS

**When to use**:
- Production deployment
- End-user interactions
- Professional demos
- Advanced reasoning visualization

---

## 🚀 Quick Start

### Option 1: Test UI Only
```bash
# From GeminiRAG directory
python web/server.py

# Visit: http://localhost:6001
```

### Option 2: Production UI
```bash
# Terminal 1: Start backend
python web/server.py

# Terminal 2: Start React frontend
cd web/ui
npm run dev

# Visit: http://localhost:5173
```

### Option 3: Use Helper Scripts
```bash
# From GeminiRAG directory

# Start both backend + frontend
./scripts/start_dev.sh

# Or start individually
./scripts/start_backend.sh
./scripts/start_frontend.sh
```

---

## 🏗️ Architecture

```
web/
├── server.py              # FastAPI backend (port 6001)
│                          # - Serves test_ui.html at root
│                          # - Provides API endpoints for both UIs
│
├── test_ui.html           # Test UI (vanilla HTML/JS)
│
└── ui/                    # Production React app
    ├── src/
    │   ├── App.jsx
    │   ├── components/
    │   │   ├── ChatInterface.jsx
    │   │   ├── UploadInterface.jsx
    │   │   ├── MarkdownRenderer.jsx
    │   │   └── Sidebar.jsx
    │   └── lib/
    │       └── api.js
    ├── package.json
    └── vite.config.js
```

---

## 📡 API Endpoints

Both UIs connect to the same backend API:

| Endpoint | Method | Purpose | Used By |
|----------|--------|---------|---------|
| `/upload` | POST | Upload files | Both UIs |
| `/add` | POST | Add raw text | Test UI only |
| `/search` | POST | Hybrid search | Test UI only |
| `/ask` | POST | Non-streaming RAG | Test UI |
| `/ask_stream` | POST | Streaming RAG | Production UI |
| `/stats` | GET | Collection stats | Both UIs |
| `/clear` | POST | Clear all docs | Both UIs |

---

## 🔧 Development

### Backend Development
```bash
# Make changes to server.py
python web/server.py

# API docs available at:
# http://localhost:6001/docs
```

### Frontend Development
```bash
cd ui
npm run dev

# Hot reload enabled
# Changes reflect immediately
```

### Building for Production
```bash
cd ui
npm run build

# Output: ui/dist/
# Can be served by backend or separate web server
```

---

## 📚 Tech Stack

**Backend**:
- FastAPI + Uvicorn
- Qdrant (vector database)
- BM25 (keyword search)
- Google Gemini 2.5 Pro / 2.0 Flash

**Test UI**:
- Vanilla HTML/CSS/JavaScript
- marked.js (markdown rendering)

**Production UI**:
- React 19 + Vite
- TailwindCSS 4
- react-markdown
- react-syntax-highlighter
- Axios

---

## 💡 Tips

1. **Use Test UI** for quick iterations and debugging
2. **Use Production UI** for demos and end-user testing
3. Both UIs share the same Qdrant database
4. Documents uploaded in one UI are available in the other
5. Helper scripts in `../scripts/` make startup easier
