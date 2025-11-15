from __future__ import annotations

import os
import sys
from typing import Optional

# When this module is executed directly (python src/backend/chatbot/main.py)
# Python does not set package context, so relative imports like `from .graph`
# fail with "attempted relative import with no known parent package".
# To make the file runnable as a script for local development we add the
# project's `src` directory to sys.path and set __package__ so relative
# imports resolve. This is a minimal, opt-in runtime fix that does nothing
# when the module is imported normally (e.g. by uvicorn or tests).
if __package__ is None:
    src_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    # Tell Python what package we're pretending to be part of so
    # relative imports like `from .graph import ...` work.
    __package__ = "backend.chatbot"

# Load environment variables from .env file if it exists
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_openai import ChatOpenAI

from .graph import ConversationState, Step
from .graph.builder import build_graph
from .models import ChatMessage
from .services import get_state, save_state

# =========================================================
# 1. FastAPI app setup
# =========================================================

app = FastAPI(title="Neurobank Chat – Money Transfer Assistant")

# (Optional) CORS – useful if you build a separate frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in real app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# 2. LLM + LangGraph initialization
# =========================================================

@app.on_event("startup")
def startup_event() -> None:
    """
    Initialize LLMs and LangGraph once on app startup.
    We keep them in app.state for reuse between requests.
    """
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n" + "="*60)
        print("ERROR: OPENAI_API_KEY environment variable is not set!")
        print("="*60)
        print("\nPlease set your OpenAI API key in one of these ways:\n")
        print("1. Export it in your shell:")
        print("   export OPENAI_API_KEY='your-api-key-here'\n")
        print("2. Create a .env file in the backend directory:")
        print("   echo 'OPENAI_API_KEY=your-api-key-here' > .env\n")
        print("3. Pass it when running:")
        print("   OPENAI_API_KEY='your-api-key-here' python src/backend/chatbot/main.py")
        print("="*60 + "\n")
        raise ValueError(
            "OPENAI_API_KEY environment variable is required. "
            "Set it via export, .env file, or inline when running the command."
        )

    # You can customize models / temperatures as needed.
    llm_main = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
    llm_suggestion = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
    llm_formatter = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

    graph_app = build_graph(
        llm_main=llm_main,
        llm_suggestion=llm_suggestion,
        llm_formatter=llm_formatter,
    )

    app.state.graph = graph_app


# =========================================================
# 3. Request / response schemas
# =========================================================


class ChatRequest(BaseModel):
    """
    Payload from the frontend.

    - session_id: identifies conversation (e.g. per browser tab).
    - user_id: logical user identifier (could be same as session for PoC).
    - message: user's text message.
    """

    session_id: str
    user_id: str
    message: str


class ChatResponse(BaseModel):
    """
    What the frontend receives after each turn.

    - assistant: last message that should be shown to the user.
    - step: current step of the flow (e.g. "confirming", "completed").
    - completed: True if the flow reached COMPLETED step.
    - intent: current intent string (e.g. "money_transfer", "none").
    - raw_state: optional full serialized state for debugging / dev tools.
    """

    assistant: str
    step: str
    completed: bool
    intent: str
    raw_state: Optional[dict] = None


# =========================================================
# 4. Healthcheck / basic info
# =========================================================


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Neurobank chat assistant is running.",
    }


# =========================================================
# 5. Main chat endpoint
# =========================================================


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Main endpoint used by the frontend.

    Flow:
      1. Load ConversationState for (session_id, user_id).
      2. Append the new user message to chat_history.
      3. Run the LangGraph on the state.
      4. Save updated state.
      5. Return the last assistant message + some metadata.
    """

    # 1. Get or create state
    state: ConversationState = get_state(
        session_id=request.session_id,
        user_id=request.user_id,
    )

    # 2. Append user message to history
    state.chat_history.append(
        ChatMessage(role="user", content=request.message)
    )

    # 3. Run LangGraph
    graph_app = app.state.graph
    # LangGraph returns a dict, not a ConversationState object
    result = graph_app.invoke(state.model_dump())
    
    # Convert the dict result back to ConversationState
    new_state = ConversationState(**result)

    # 4. Save updated state
    save_state(request.session_id, new_state)

    # 5. Prepare response
    assistant_text = new_state.meta.get(
        "last_assistant_text",
        "I couldn't generate a response. Please try again.",
    )
    completed = new_state.step == Step.COMPLETED
    intent_str = new_state.current_intent.value

    return ChatResponse(
        assistant=assistant_text,
        step=new_state.step.value,
        completed=completed,
        intent=intent_str,
        # For hackathon/debugging – you can set this to None in prod
        raw_state=new_state.model_dump(),
    )


if __name__ == "__main__":
    # Allow running the module directly for local development:
    # from the repo root run:
    #   PYTHONPATH=src python src/backend/chatbot/main.py
    # or (when src is already on PYTHONPATH) simply:
    #   python src/backend/chatbot/main.py
    import uvicorn

    # Use reload_dirs instead of reload=True to avoid subprocess import issues
    # Or use the app object directly without reload for simpler execution
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    import uvicorn
    # Make sure module imports resolve when running from repo root:
    # e.g. PYTHONPATH=src python src/backend/chatbot/main.py
    uvicorn.run("backend.chatbot.main:app", host="127.0.0.1", port=8000, reload=True)
