# Neurobank Chat - Money Transfer Assistant

FastAPI chatbot backend using LangGraph for conversational money transfers.

## ✅ Setup Complete!

All dependencies are installed and the app is ready to run.

## Quick Start

### Option 1: Using Conda Environment (Recommended)

```bash
# Navigate to backend directory
cd /Users/petromelnyk/Desktop/projects/Collabathon2025/backend

# Set your OpenAI API key (choose one method):

# Method A: Export in shell (temporary for current session)
export OPENAI_API_KEY='your-api-key-here'

# Method B: Create a .env file (persistent)
echo "OPENAI_API_KEY=your-api-key-here" > .env

# Method C: Set inline when running
OPENAI_API_KEY='your-api-key-here' /opt/anaconda3/envs/collabathon/bin/python src/backend/chatbot/main.py

# Run the app
/opt/anaconda3/envs/collabathon/bin/python src/backend/chatbot/main.py
```

### Option 2: Using Poetry Environment

```bash
cd /Users/petromelnyk/Desktop/projects/Collabathon2025/backend

# Set API key (same methods as above)
export OPENAI_API_KEY='your-api-key-here'

# Run with Poetry
poetry run python src/backend/chatbot/main.py
```

### Option 3: Using Uvicorn with Auto-reload (Development)

```bash
cd /Users/petromelnyk/Desktop/projects/Collabathon2025/backend

export OPENAI_API_KEY='your-api-key-here'

# With conda environment
PYTHONPATH=src /opt/anaconda3/envs/collabathon/bin/uvicorn backend.chatbot.main:app --reload --host 127.0.0.1 --port 8000

# Or with Poetry
PYTHONPATH=src poetry run uvicorn backend.chatbot.main:app --reload --host 127.0.0.1 --port 8000
```

## Troubleshooting

### Port Already in Use

If you see `[Errno 48] error while attempting to bind on address ('127.0.0.1', 8000): address already in use`:

```bash
# Option 1: Kill the process using port 8000
lsof -ti:8000 | xargs kill -9

# Option 2: Use a different port
# Edit main.py line where uvicorn.run is called, change port to 8001
```

### Missing OpenAI API Key

If you see errors about missing OPENAI_API_KEY:
1. Get your API key from: https://platform.openai.com/api-keys
2. Set it using one of the methods above

### Import Errors

If you see `ModuleNotFoundError`:
- Make sure you're using the correct Python environment
- Verify packages are installed: `/opt/anaconda3/envs/collabathon/bin/pip list | grep langgraph`

## API Endpoints

Once running, the API is available at `http://127.0.0.1:8000`

- `GET /` - Health check
- `POST /chat` - Main chat endpoint

### Example Request

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-1",
    "user_id": "user-123",
    "message": "I want to send money to John"
  }'
```

## Project Structure

```
backend/
├── src/
│   └── backend/
│       └── chatbot/
│           ├── main.py          # FastAPI app entry point
│           ├── agents/          # LangChain agents
│           ├── graph/           # LangGraph workflow
│           ├── models/          # Pydantic models
│           └── services/        # Business logic
├── pyproject.toml               # Poetry dependencies
└── .env.example                 # Environment variables template
```

## Development Notes

- Python version: 3.10 (conda environment: collabathon)
- Framework: FastAPI + LangGraph
- LLM: OpenAI GPT-4o-mini
- The app uses relative imports and requires proper package context
- Hot reload is available when using uvicorn with `--reload` flag

## Next Steps

1. Set your OPENAI_API_KEY
2. Run the app using one of the methods above
3. Test the `/chat` endpoint
4. Build your frontend to integrate with the API
