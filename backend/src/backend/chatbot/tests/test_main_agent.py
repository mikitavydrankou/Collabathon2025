# tests/manual_main_agent_live.py

import os
import sys
from zipfile import Path

from langchain_openai import ChatOpenAI

from backend.chatbot.agents.main_agent import run_main_agent
from backend.chatbot.agents import MainAgentAction
from backend.chatbot.graph import ConversationState, Intent

from dotenv import load_dotenv

load_dotenv()


def run_manual_main_agent_test():
    """
    Bardzo prosty "ręczny" test integracyjny:
    - woła prawdziwe OpenAI (gpt-4o-mini),
    - odpala run_main_agent,
    - sprawdza, że intencja to MONEY_TRANSFER
      i wypisuje wynik na ekran.
    """

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Brak zmiennej środowiskowej OPENAI_API_KEY")

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=api_key,
    )

    state = ConversationState(
        user_id="test-user",
        session_id="test-session",
    )

    user_message = "I want to send 200 EUR to my landlord Anna Kowalska."

    output = run_main_agent(
        llm=llm,
        state=state,
        latest_user_message=user_message,
    )

    # Debug / podgląd:
    print("assistant_text:", output.assistant_text)
    print("action:", output.action)
    print("intent:", output.intent)
    print("field_to_edit:", output.field_to_edit)

    # Minimalne asercje (wbudowane assert, bez pytest):
    assert isinstance(output.assistant_text, str), "assistant_text nie jest stringiem"
    assert len(output.assistant_text) > 0, "assistant_text jest pusty"

    assert output.intent == Intent.MONEY_TRANSFER, (
        f"Oczekiwano Intent.MONEY_TRANSFER, a jest {output.intent}"
    )

    assert isinstance(output.action, MainAgentAction), "action nie jest MainAgentAction"

    print("\n✅ Test main agenta zakończony powodzeniem.")


if __name__ == "__main__":
    run_manual_main_agent_test()
