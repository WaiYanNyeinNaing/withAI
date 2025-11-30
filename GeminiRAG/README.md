# GeminiRAG: Hybrid Search RAG System

A clean, powerful Retrieval-Augmented Generation (RAG) system powered by Google Gemini, Qdrant vector database, and BM25 keyword search.

## 🚀 Features

- **Hybrid Search**: Combines **Semantic Search** (Vector embeddings) and **Keyword Search** (BM25) for superior retrieval accuracy
- **Smart Chunking**: Hybrid semantic chunking strategy that respects sentence boundaries and merges small chunks
- **Detailed Answers**: Generates comprehensive, well-cited answers using Gemini 2.0 Flash
- **Persistent Storage**: Qdrant for vectors with automatic BM25 index rebuilding on startup
- **Clean UI**: User-friendly interface for uploading documents (PDF/TXT/MD) and testing RAG

## 🛠️ Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set API Key**:
   Create a `.env` file:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

## ▶️ Running

Start the server:
```bash
cd web
python server.py
```

Access the UI at: **http://localhost:6001**

## 📖 Usage

1. **Upload Documents**: Click "📁 Upload Files" to add PDFs, TXT, or MD files
2. **Ask Questions**: Use the RAG section to get AI-powered answers with source citations
3. **View Sources**: See which chunks were used (labeled as SEMANTIC, BM25, or HYBRID match)
4. **Manage Data**: Clear all documents to start fresh

## 🏗️ Architecture

See [system_design.md](system_design.md) for detailed architecture.

**Key Components**:
- `backend/vector_store.py` - Manages Qdrant + BM25 hybrid search
- `backend/chunking.py` - Smart semantic chunking
- `web/server.py` - FastAPI server
- `web/index.html` - Web UI

## 📦 What's in Archive

The `archive/` folder contains the old chat UI implementation and legacy code. The current clean implementation focuses solely on the hybrid search RAG system.
