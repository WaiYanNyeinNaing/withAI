# Meta Agent Framework

> Build end-to-end AI applications with a single instruction

## Overview
This is an enhanced meta-agent framework that can autonomously build complete AI applications with React frontends and Python backends from simple instructions.

## Features
- 🤖 **Autonomous Development:** Give a one-line instruction, get a full application
- ⚛️ **Modern Stack:** React + Vite frontend, FastAPI backend
- 🔧 **Tool Creation:** Automatically creates new tools when needed
- 🌐 **Web Search:** Searches the web for implementation guides
- 📚 **Comprehensive Handbook:** Detailed guides for all common patterns
- 🎨 **Multiple UI Options:** React (modern) or Streamlit (simple demos)
- 🔌 **Easy Integration:** Pre-built templates for frontend-backend connection

## Quick Start

### 1. Setup
```bash
# Clone or navigate to the project
cd Z21

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.sample .env
# Edit .env with your API keys
```

### 2. Create Your First App
Simply update `inputs/project_goal.md` with your instruction:
```
Create a weather app that shows current weather for any city
```

Then let the meta-agent build it for you!

## Project Structure
```
Z21/
├── inputs/
│   ├── project_goal.md          # Your one-line instruction
│   ├── tooling_handbook.txt     # Comprehensive tool guides
│   ├── templates/               # React & FastAPI templates
│   │   ├── react_frontend_template.md
│   │   ├── fastapi_backend_template.md
│   │   └── integration_guide.md
│   └── examples/                # Example projects
│       └── web_search_agent.md
├── output/                      # Generated applications
├── system_architecture.md       # Meta-agent protocol
├── env.sample                   # Environment variables template
└── requirements.txt
```

## How It Works

### 1. Analysis Phase
The meta-agent reads your `project_goal.md` and decides:
- Does it need web search? → Use Serper API
- Does it need file processing? → Use Gemini RAG
- Does it need a database? → Choose SQLite or PostgreSQL
- Frontend type? → React (default) or Streamlit
- Backend type? → FastAPI (default)

### 2. Planning Phase
- Selects tools from the comprehensive handbook
- If a tool is missing, searches the web for implementation guides
- Creates a detailed implementation plan

### 3. Build Phase
**Backend:**
- Creates `output/backend/agent.py` (core logic)
- Creates `output/backend/main.py` (FastAPI server)
- Generates `requirements.txt`
- Creates `.env.sample` with all needed keys

**Frontend (if React):**
- Initializes Vite + React app
- Creates components with Tailwind CSS
- Configures API integration
- Sets up proper CORS

### 4. Integration Phase
- Ensures frontend and backend work together
- Creates comprehensive README
- Provides setup instructions

## Available Tools

### Web Search
- **Serper API:** Real-time Google search
- **SerpAPI:** Alternative search provider

### AI/ML
- **Google Gemini:** Core AI capabilities
- **Function Calling:** Tool integration
- **File Upload & RAG:** Document processing

### Backend
- **FastAPI:** Modern Python API framework
- **Streamlit:** Quick UI prototyping

### Frontend
- **React + Vite:** Modern frontend framework
- **Tailwind CSS:** Utility-first styling
- **Axios:** HTTP client

### Database
- **SQLite:** Simple file-based database
- **PostgreSQL:** Production-ready database

## Templates

### React Frontend
See `inputs/templates/react_frontend_template.md` for:
- Basic form interface
- Chat interface
- API integration patterns
- Tailwind CSS setup

### FastAPI Backend
See `inputs/templates/fastapi_backend_template.md` for:
- API structure
- CORS configuration
- Error handling
- Environment variables

### Integration
See `inputs/templates/integration_guide.md` for:
- Connecting React to FastAPI
- CORS setup
- Error handling
- Production deployment

## Examples

### Web Search Agent
A complete example in `inputs/examples/web_search_agent.md`:
- Uses Serper API for web search
- Gemini for intelligent responses
- Streamlit UI
- CLI testing support

## Environment Variables

Required:
```bash
GOOGLE_API_KEY=your_key          # From aistudio.google.com
GEMINI_MODEL=gemini-2.0-flash-exp
```

Optional:
```bash
SERPER_API_KEY=your_key          # For web search
DEBUG=True
PORT=8000
```

See `env.sample` for complete list with documentation.

## Autonomous Tool Creation

When the meta-agent needs a tool not in the handbook:
1. Searches the web: "[tool name] Python implementation guide"
2. Finds official documentation
3. Implements and tests the tool
4. Adds it to the generated code
5. Documents it in the project README

## Best Practices

### For Users
1. Be specific in `project_goal.md`
2. Mention if you need specific features (auth, database, etc.)
3. Specify React if you want a modern UI
4. Review generated code before deploying

### For Generated Code
1. Always use environment variables
2. Implement proper error handling
3. Add loading states in UI
4. Configure CORS correctly
5. Include comprehensive README

## Common Use Cases

### Simple Chatbot
```
Create a chatbot that can answer questions about my company
```

### Data Dashboard
```
Create a React dashboard that displays sales data from a CSV file
```

### API Service
```
Create an API that translates text between languages using Gemini
```

### Full-Stack App
```
Create a todo app with React frontend and FastAPI backend with SQLite database
```

## Troubleshooting

### CORS Errors
Ensure backend has CORS middleware configured for your frontend URL.

### API Key Errors
Check `.env` file has all required keys and they're valid.

### Build Errors
Check Node.js and Python versions are compatible.

### Connection Refused
Ensure backend is running before starting frontend.

## Contributing

To add new tools to the handbook:
1. Add implementation to `inputs/tooling_handbook.txt`
2. Follow the existing format
3. Include usage examples
4. Document environment variables

## License
MIT

## Support
For issues or questions, check the examples and templates first.

---

**Built with ❤️ by the Meta Agent Framework**
