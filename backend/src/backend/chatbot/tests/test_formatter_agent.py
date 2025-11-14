# tests/manual_formatter_agent_live.py

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from backend.chatbot.agents.formatter_agent import run_formatter_agent
from backend.chatbot.models import MoneyTransferForm, FinalRecipient

load_dotenv()


def run_manual_formatter_agent_test():
    """
    Bardzo prosty "ręczny" test integracyjny FormatterAgenta:
    - woła prawdziwe OpenAI (gpt-4o-mini),
    - buduje przykładowy MoneyTransferForm,
    - odpala run_formatter_agent,
    - wypisuje wynik na ekran i robi kilka prostych asercji.
    """

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Brak zmiennej środowiskowej OPENAI_API_KEY")

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=api_key,
    )

    # Przykładowy, "gotowy" formularz przelewu
    form = MoneyTransferForm(
        recipient=FinalRecipient(
            name="Anna Kowalska (Landlord)",
            iban="DE89 3704 0044 0532 0130 00",
        ),
        amount=850.00,
        currency="EUR",
        reference_text="Rent for November",
    )

    suggestion_source = "recent rent payment from last week"

    output = run_formatter_agent(
        llm=llm,
        form=form,
        suggestion_source=suggestion_source,
    )

    assistant_text = output.assistant_text

    # Debug / podgląd:
    print("=== FormatterAgent output ===")
    print(assistant_text)

    # Minimalne asercje (bez pytest, zwykłe assert):
    assert isinstance(assistant_text, str), "assistant_text nie jest stringiem"
    assert len(assistant_text.strip()) > 0, "assistant_text jest pusty"

    # Opcjonalnie lekka kontrola stylu (bardzo luźna, bo to LLM):
    # Sprawdzamy, czy pojawia się nazwa odbiorcy i kwota.
    assert "Anna Kowalska" in assistant_text, "Brak nazwy odbiorcy w odpowiedzi"
    assert "850" in assistant_text or "850.0" in assistant_text, \
        "Brak kwoty w odpowiedzi"

    print("\n✅ Test formatter agenta zakończony powodzeniem.")


if __name__ == "__main__":
    run_manual_formatter_agent_test()