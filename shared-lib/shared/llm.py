"""
LLM utility module using LangChain and OpenAI.
"""

import os
import logging
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Ensure handler exists
if not logger.handlers:
    import sys
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Get OpenAI API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY not found in environment. "
        "Please set it in .env file."
    )


def get_llm(model: str = "gpt-4o-mini", temperature: float = 0.7) -> ChatOpenAI:
    """
    Get configured LangChain ChatOpenAI instance.

    Args:
        model: OpenAI model name (default: gpt-4o-mini for cost efficiency)
        temperature: Temperature for generation (0.0-1.0)

    Returns:
        Configured ChatOpenAI instance
    """
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=OPENAI_API_KEY,
    )


def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.7, log_prompts: bool = True) -> str:
    """
    Call LLM with system and user prompts.

    Args:
        system_prompt: System instructions for the LLM
        user_prompt: User message/query
        temperature: Temperature for generation
        log_prompts: Whether to log prompts and responses

    Returns:
        LLM response as string
    """
    if log_prompts:
        logger.info(f"\n{'='*80}")
        logger.info(f"[LLM] LLM Call - Temperature: {temperature}")
        logger.info(f"{'='*80}")
        logger.info(f"[PROMPT] System Prompt:\n{system_prompt[:300]}{'...' if len(system_prompt) > 300 else ''}")
        logger.info(f"\n[MSG] User Prompt:\n{user_prompt[:300]}{'...' if len(user_prompt) > 300 else ''}")
        logger.info(f"{'='*80}\n")
    
    llm = get_llm(temperature=temperature)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    response = llm.invoke(messages)
    
    if log_prompts:
        logger.info(f"[OK] LLM Response:\n{response.content[:300]}{'...' if len(response.content) > 300 else ''}\n")
    
    return response.content


def call_llm_with_json(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.5
) -> str:
    """
    Call LLM expecting JSON response.

    Args:
        system_prompt: System instructions (should mention JSON format)
        user_prompt: User message/query
        temperature: Lower temperature for more deterministic JSON

    Returns:
        LLM response as string (should be valid JSON)
    """
    return call_llm(system_prompt, user_prompt, temperature=temperature)
