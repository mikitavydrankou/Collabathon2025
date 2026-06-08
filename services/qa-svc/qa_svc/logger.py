"""
Logging utility for agent system with prompt tracking.
"""
import logging
import sys
from datetime import datetime
from typing import Optional

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # Simplified format for cleaner output
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True  # Force reconfiguration
)

# Set log level for QA modules
logging.getLogger('qa_svc').setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module."""
    return logging.getLogger(name)


def log_prompt(logger: logging.Logger, agent_name: str, system_prompt: str, user_prompt: str, temperature: float = 0.7):
    """Log LLM prompt details."""
    logger.info(f"\n{'='*80}")
    logger.info(f"🤖 {agent_name} - LLM Call")
    logger.info(f"{'='*80}")
    logger.info(f"Temperature: {temperature}")
    logger.info(f"\n📝 System Prompt:\n{system_prompt[:500]}{'...' if len(system_prompt) > 500 else ''}")
    logger.info(f"\n💬 User Prompt:\n{user_prompt[:500]}{'...' if len(user_prompt) > 500 else ''}")
    logger.info(f"{'='*80}\n")


def log_llm_response(logger: logging.Logger, agent_name: str, response: str, success: bool = True):
    """Log LLM response."""
    status = "✅" if success else "❌"
    logger.info(f"\n{status} {agent_name} - LLM Response")
    logger.info(f"{'='*80}")
    logger.info(f"Response:\n{response[:500]}{'...' if len(response) > 500 else ''}")
    logger.info(f"{'='*80}\n")


def log_agent_action(logger: logging.Logger, agent_name: str, action: str, details: Optional[dict] = None):
    """Log agent action with details."""
    logger.info(f"🔧 {agent_name} - {action}")
    if details:
        for key, value in details.items():
            logger.info(f"  {key}: {value}")


def log_tool_call(logger: logging.Logger, tool_name: str, function: str, params: dict):
    """Log tool call details."""
    logger.info(f"\n🔨 Tool Call: {tool_name}")
    logger.info(f"  Function: {function}")
    logger.info(f"  Parameters: {params}")


def log_tool_result(logger: logging.Logger, tool_name: str, success: bool, data: any, error: Optional[str] = None):
    """Log tool execution result."""
    status = "✅" if success else "❌"
    logger.info(f"{status} Tool Result: {tool_name}")
    if success:
        if isinstance(data, list):
            logger.info(f"  Data count: {len(data)}")
            logger.info(f"  Sample: {data[0] if data else 'empty'}")
        else:
            logger.info(f"  Data: {data}")
    else:
        logger.error(f"  Error: {error}")


def log_classification(logger: logging.Logger, query: str, needs_sql: bool, needs_rag: bool, reasoning: str = ""):
    """Log query classification."""
    logger.info(f"\n🎯 Query Classification")
    logger.info(f"  Query: {query}")
    logger.info(f"  Needs SQL: {needs_sql}")
    logger.info(f"  Needs RAG: {needs_rag}")
    if reasoning:
        logger.info(f"  Reasoning: {reasoning}")

