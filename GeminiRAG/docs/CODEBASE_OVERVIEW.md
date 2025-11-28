# 🏗️ Codebase Overview

This document provides a high-level tour of the GeminiRAG project structure to help you understand where everything lives.

## 📂 Directory Structure

```
GeminiRAG/
├── backend/                 # 🧠 The Brain (Agents & Logic)
├── services/                # 📚 The Library (Document Management)
├── react_frontend/          # 🎨 The Face (User Interface)
├── documents/               # 🗄️ The Storage (Uploaded Files)
├── docs/                    # 📖 Documentation
└── start.sh                 # 🚀 Startup Script
```

---

## 🧠 Backend (`backend/`)

This folder contains the core intelligence of the application. It runs on **Port 5001**.

*   **`api_server.py`**: The main entry point. It handles requests from the frontend (like "Ask a question") and coordinates the agents.
*   **`orchestrator.py`**: The conductor. It manages the multi-agent workflow (Planner → Judge → Synthesizer).
*   **`agents/`**:
    *   `planner.py`: Breaks down complex questions into steps.
    *   `judge.py`: Evaluates if the answer is good enough.
    *   `synthesizer.py`: Formats the final answer for the user.
*   **`http_tools.py`**: Tools that the agents use to "talk" to the Document Service (e.g., to search for files).

## 📚 Services (`services/`)

This is the **Document Service**. It runs on **Port 8000** and acts like a librarian.

*   **`api.py`**: The API for uploading and searching documents.
*   **`doc_store.py`**: Manages the in-memory index of documents (BM25).
*   **`semantic_search.py`**: Handles the connection to Google's Gemini File Search for "smart" semantic retrieval.
*   **`persistence.py`**: Saves the index to disk so you don't lose data when restarting.

## 🎨 Frontend (`react_frontend/`)

The user interface that runs in your browser on **Port 8080**.

*   **`index.html`**: The structure of the page.
*   **`style.css`**: The styling (Dark mode, glassmorphism).
*   **`script.js`**: The logic that sends your messages to the backend and displays the streaming response.

## 🚀 Key Workflows

### 1. File Upload
1.  User drops a file in **Frontend**.
2.  **Backend** receives it and sends it to **Services**.
3.  **Services** extracts text, creates a summary, and indexes it (both BM25 and Semantic).

### 2. Asking a Question
1.  User types a question in **Frontend**.
2.  **Backend** (`orchestrator.py`) starts the **Planner Agent**.
3.  **Planner** decides to search documents.
4.  **Backend** calls **Services** to perform Hybrid Search (BM25 + Semantic).
5.  **Services** returns relevant snippets.
6.  **Synthesizer Agent** formulates the answer.
7.  **Frontend** streams the answer to the user.
