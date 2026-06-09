"""
FastAPI application for MCP server.

Exposes the 3 money transfer tools as REST endpoints for backend agents to call.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from shared.models import engine
from shared.tracing import init_tracing

from . import __version__
from .schemas import (
    FilterSuggestionInput,
    FilterSuggestionOutput,
    FinalCheckInput,
    FinalCheckOutput,
    FirstSuggestionInput,
    FirstSuggestionOutput,
    RAGQueryInput,
    RAGQueryOutput,
    SQLQueryInput,
    SQLQueryOutput,
)
from .tools import (
    filter_suggestion_tool,
    final_check_tool,
    first_suggestion_tool,
    rag_query_tool,
    sql_query_tool,
)

app = FastAPI(
    title="Banking Money Transfer MCP Server",
    description="MCP tools for LLM-driven money transfer assistance",
    version=__version__,
)

# This service builds its own FastAPI (not shared.app_factory), so tracing is
# wired up here: a no-op without OTEL_EXPORTER_OTLP_ENDPOINT, otherwise mcp
# server spans continue the trace the caller (chatbot/qa) propagated over httpx.
init_tracing("mcp")
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(app)
except Exception:  # never let instrumentation break startup
    pass

# CORS middleware for backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns service health and database connectivity status.
    """
    try:
        connection = engine.connect()
        connection.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "version": __version__,
        "database": db_status,
        "service": "mcp-server",
    }


@app.post("/tools/first-suggestion", response_model=FirstSuggestionOutput)
async def first_suggestion(input_data: FirstSuggestionInput):
    """
    Get up to 5 transactions with temporal context for LLM analysis.

    Returns transactions from ~1 year/month/week ago + 2 recent.
    LLM agent decides which to suggest based on temporal patterns.
    """
    try:
        return first_suggestion_tool(input_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/filter-suggestion", response_model=FilterSuggestionOutput)
async def filter_suggestion(input_data: FilterSuggestionInput):
    """
    Filter past transactions by partial name/amount/title.

    Returns matched transactions for LLM to rank by relevance.
    """
    try:
        return filter_suggestion_tool(input_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/final-check", response_model=FinalCheckOutput)
async def final_check(input_data: FinalCheckInput):
    """
    Validate transaction and return OK or list of problems.

    Checks amount validity, balance, account length, and historical consistency.
    """
    try:
        return final_check_tool(input_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/sql-query", response_model=SQLQueryOutput)
async def sql_query(input_data: SQLQueryInput):
    """
    Execute SQL queries for transaction analysis.
    
    Supports various functions like get_recent_transactions, filter_transactions,
    get_time_based_transactions, get_recipient_patterns, and get_user_balance.
    """
    try:
        return sql_query_tool(input_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/rag-query", response_model=RAGQueryOutput)
async def rag_query(input_data: RAGQueryInput):
    """
    Search for similar transactions using semantic search (RAG).
    
    Uses ChromaDB with OpenAI embeddings to find transactions similar
    to the query text.
    """
    try:
        return rag_query_tool(input_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Banking Money Transfer MCP Server",
        "version": __version__,
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "first_suggestion": "/tools/first-suggestion",
            "filter_suggestion": "/tools/filter-suggestion",
            "final_check": "/tools/final-check",
            "sql_query": "/tools/sql-query",
            "rag_query": "/tools/rag-query",
        },
    }


def start():
    """Entry point for running the MCP server via poetry script."""
    import uvicorn
    uvicorn.run("mcp_server.app:app", host="0.0.0.0", port=8001, reload=True)
