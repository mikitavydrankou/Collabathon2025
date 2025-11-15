"""
LLM utility module using LangChain and OpenAI.
"""

import os
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


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


def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
    """
    Call LLM with system and user prompts.

    Args:
        system_prompt: System instructions for the LLM
        user_prompt: User message/query
        temperature: Temperature for generation

    Returns:
        LLM response as string
    """
    llm = get_llm(temperature=temperature)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    response = llm.invoke(messages)
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
