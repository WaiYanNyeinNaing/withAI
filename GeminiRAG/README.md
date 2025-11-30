# GeminiRAG: Advanced Hybrid Search RAG with Multi-Stage Reasoning

A sophisticated Retrieval-Augmented Generation (RAG) system powered by Google Gemini 2.5 Pro, featuring hybrid search and a 3-stage Step-Back Prompting pipeline for superior answer quality.

## ✨ Key Features

### 🔍 Hybrid Search
- **Semantic Search**: Vector embeddings via Google's `embedding-001` model
- **Keyword Search**: BM25 ranking algorithm for precise term matching
- **Intelligent Deduplication**: Combines results from both methods (typically 5-10 unique chunks)

### 🧠 3-Stage Step-Back Prompting
1. **Stage 1 - Initial Thinking** (`gemini-2.0-flash-thinking-exp-1219`): Fast initial analysis and draft answer
2. **Stage 2 - Reflection** (`gemini-2.5-pro`): Critical review to identify gaps and ensure intent alignment
3. **Stage 3 - Final Synthesis** (`gemini-2.5-pro`): Polished comprehensive answer incorporating all insights

### 📝 Smart Chunking
- **Hybrid Semantic Chunking**: Base splitting (1500 chars) + semantic refinement (90th percentile threshold)
- **Intelligent Merging**: Combines small chunks to ensure meaningful context (min 350 chars)
- **Topic-Aware**: Splits on semantic shifts while preserving context

### 🎨 Modern UI
- **Mode Selector**: Choose between Pro Mode (3-stage reasoning) or Flash Mode (quick answers)
- **Streaming Responses**: Real-time display of all reasoning stages
- **Collapsible Stages**: Color-coded sections for each reasoning phase
- **Markdown Rendering**: Syntax-highlighted code blocks, tables, and rich formatting
- **Clean References**: File-based citations with page numbers (no chunk content clutter)

## 🛠️ Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- Google API Key ([Get one here](https://aistudio.google.com/app/apikey))

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/WaiYanNyeinNaing/withAI.git
   cd withAI/GeminiRAG
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Frontend dependencies**:
   ```bash
   cd web/ui
   npm install
   cd ../..
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

## ▶️ Running the Application

GeminiRAG provides **two UI options** to suit different needs:

### 🎯 UI Options

#### 1. Test UI (Simple) - Port 6001
- **Purpose**: Quick testing and debugging
- **Tech**: Vanilla HTML/JS (no build process)
- **Features**: File upload, search testing, stats viewer
- **Best for**: Development, debugging, simple demos

#### 2. Production UI (React) - Port 5173
- **Purpose**: Production-ready chat interface
- **Tech**: React + Vite + TailwindCSS
- **Features**: Streaming, mode selector, rich markdown, collapsible reasoning stages
- **Best for**: End users, professional demos, production deployment

---

### Quick Start Options

#### Option A: Test UI Only (Fastest)
```bash
# Start backend (serves test UI at root)
python web/server.py
```
Visit: **http://localhost:6001**

#### Option B: Production UI (Recommended)
```bash
# Terminal 1: Start backend
python web/server.py

# Terminal 2: Start React frontend
cd web/ui
npm run dev
```
Visit: **http://localhost:5173**

#### Option C: Use Helper Scripts
```bash
# Start both backend + frontend together
./scripts/start_dev.sh

# Or start individually
./scripts/start_backend.sh
./scripts/start_frontend.sh
```

---

### Detailed Setup

### Start Backend Server
```bash
python web/server.py
```
Backend runs on: **http://localhost:6001**
- Test UI available at root
- API documentation at `/docs`

### Start Frontend Dev Server (Optional)
```bash
cd web/ui
npm run dev
```
Frontend runs on: **http://localhost:5173**
- Production React interface
- Hot reload enabled

## 📖 Usage

1. **Upload Documents**: 
   - Click "Upload & Index" tab
   - Upload PDF, TXT, or MD files
   - Documents are automatically chunked and indexed

2. **Ask Questions**:
   - Switch to "Chat" tab
   - **Choose your mode**:
     - 🧠 **Pro Mode** (default): 3-stage reasoning for comprehensive answers (~8-15s)
     - ⚡ **Flash Mode**: Quick single-step answers with more context (~3-5s)
   - Ask questions about your documents
   - Watch the reasoning process (Pro Mode) or get instant answers (Flash Mode)

3. **Explore Reasoning**:
   - 🧠 **Stage 1: Initial Thinking** - See the model's first thoughts
   - 📝 **Stage 1: Draft Answer** - Review the initial answer
   - 🔍 **Stage 2: Reflection** - Understand the quality check
   - 💭 **Stage 3: Final Thinking** - Follow the final reasoning
   - ✨ **Final Answer** - Get the polished response

4. **View References**: See clean file-based citations with page numbers and source types

5. **New Chat**: Click "New chat" to start a fresh conversation

## 🏗️ Architecture

### Backend (`web/server.py`)
- **FastAPI** server with streaming support
- **3-stage pipeline** for answer generation
- **Hybrid search** combining vector and keyword methods

### Vector Store (`backend/vector_store.py`)
- **Qdrant** for vector storage (local file-based)
- **BM25** index for keyword search
- **Hybrid search** with deduplication

### Chunking (`backend/chunking.py`)
- **Semantic chunking** using Google embeddings
- **Recursive base splitting** for initial chunks
- **Intelligent merging** for optimal chunk sizes

### Frontend (`web/ui/`)
- **React** with Vite
- **Streaming UI** with real-time updates
- **Markdown rendering** with syntax highlighting
- **Collapsible sections** for each reasoning stage

## 📦 Tech Stack

**Backend**:
- FastAPI, Uvicorn
- LangChain, LangChain Google GenAI
- Qdrant Client
- rank-bm25
- pypdf

**Frontend**:
- React 19
- Vite
- TailwindCSS
- react-markdown
- react-syntax-highlighter

**AI Models**:
- `gemini-2.0-flash-thinking-exp-1219` (Stage 1 - Initial thinking)
- `gemini-2.5-pro` (Stages 2 & 3 - Reflection and synthesis)
- `embedding-001` (Vector embeddings)

## 🔧 Configuration

Edit `.env` to configure:
```
GOOGLE_API_KEY=your_api_key_here
```

## 📊 Performance Notes

- **Response Time**: ~8-15 seconds (Flash for Stage 1, Pro for Stages 2 & 3)
- **Quality**: Superior reasoning with Pro model for reflection and synthesis
- **Context Size**: 5-10 unique chunks per query (hybrid search deduplication)
- **Cost**: Balanced - Flash for speed, Pro for quality

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - see LICENSE file for details
