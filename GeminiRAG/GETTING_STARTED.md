# 🚀 Getting Started with GeminiRAG

This guide will get you up and running with GeminiRAG in less than 5 minutes.

## 1. Prerequisites

- **Python 3.9+** installed.
- **Google API Key** from [Google AI Studio](https://aistudio.google.com/app/apikey).

## 2. Installation

Open your terminal and run:

```bash
# 1. Clone or download this repository
cd GeminiRAG

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure Environment
cp .env.example .env
```

## 3. Configuration

Open the `.env` file and paste your API key:

```ini
GOOGLE_API_KEY=your_actual_api_key_here
```

*(Optional) Enable Hybrid Search:*
```ini
SEMANTIC_SEARCH_ENABLED=true
```

## 4. Run the App

We provide a script to start all services (Backend, Document Store, Frontend) at once:

```bash
./start.sh
```

The application will automatically open in your browser at **http://localhost:8080**.

## 5. How to Use

1.  **Upload**: Drag & drop PDF, TXT, or MD files into the UI.
2.  **Ask**: Type questions like "What does the document say about X?".
3.  **View**: Watch the AI plan, search, and answer in real-time.

---

**Troubleshooting**
- **Ports in use?** The `start.sh` script tries to free ports 5001, 8000, and 8080.
- **No answer?** Check your terminal for error logs. Ensure your API key is valid.
