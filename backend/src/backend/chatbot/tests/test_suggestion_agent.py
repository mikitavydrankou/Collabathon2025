# tests/manual_suggestion_agent_live.py

import os
from datetime import date, timedelta

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from backend.chatbot.agents.suggestion_agent import run_suggestion_agent
from backend.chatbot.graph import ConversationState
from backend.chatbot.models import TransactionRecord

load_dotenv()


def run_manual_suggestion_agent_test():
    """
    Bardzo prosty "ręczny" test integracyjny SuggestionAgenta:
    - woła prawdziwe OpenAI (gpt-4o-mini),
    - buduje przykładową historię transakcji,
    - odpala run_suggestion_agent,
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

    # Minimalny stan rozmowy (tu nie jest bardzo istotny)
    state = ConversationState(
        user_id="test-user",
        session_id="test-session",
    )

    today = date.today()

    # Przykładowa historia transakcji (podobna jak w mock_client)
    history = [
        TransactionRecord(
            date=today - timedelta(days=7),
            recipient_name="Anna Kowalska (Landlord)",
            recipient_iban="DE89 3704 0044 0532 0130 00",
            amount=850.00,
            currency="EUR",
            title="Rent for November",
        ),
        TransactionRecord(
            date=today - timedelta(days=90),
            recipient_name="Stadtwerke Berlin",
            recipient_iban="DE12 3456 7890 1234 5678 90",
            amount=120.50,
            currency="EUR",
            title="Electricity bill Q3",
        ),
        TransactionRecord(
            date=today - timedelta(days=330),
            recipient_name="Max Mustermann",
            recipient_iban="DE44 5001 0517 5407 3249 31",
            amount=50.00,
            currency="EUR",
            title="Birthday gift",
        ),
    ]

    output = run_suggestion_agent(
        llm=llm,
        state=state,
        history=history,
    )

    form = output.form

    # Debug / podgląd:
    print("=== Suggested MoneyTransferForm ===")
    print("Recipient name:", form.recipient.name)
    print("Recipient IBAN:", form.recipient.iban)
    print("Amount:", form.amount)
    print("Currency:", form.currency)
    print("Reference text:", form.reference_text)
    print("Suggestion source:", output.suggestion_source)

    # Minimalne asercje (bez pytest, zwykłe assert):
    assert form.recipient.name, "Brak nazwy odbiorcy w proponowanym formularzu"
    assert form.recipient.iban, "Brak IBAN odbiorcy w proponowanym formularzu"
    assert form.amount > 0, "Kwota powinna być dodatnia"
    assert isinstance(form.currency, str) and len(form.currency) == 3, \
        f"Nieprawidłowa waluta: {form.currency}"

    print("\n✅ Test suggestion agenta zakończony powodzeniem.")


if __name__ == "__main__":
    run_manual_suggestion_agent_test()
