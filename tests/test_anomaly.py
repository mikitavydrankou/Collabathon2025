"""Unit tests for transactions_svc.anomaly validation logic.

Runs against an in-memory SQLite DB (the `db_session` fixture). Exercises the
amount/bank-number/full-name validators that guard transaction creation.
"""

import importlib.util
import pathlib
from datetime import date, datetime

import pytest

from shared.models import Transaction, User

# Load anomaly.py by path to avoid importing transactions_svc/__init__.py, which
# pulls in Kafka/FastAPI route wiring we don't need here. anomaly.py only depends
# on numpy and shared.models.
_anomaly_path = (
    pathlib.Path(__file__).resolve().parents[1]
    / "services"
    / "transactions-svc"
    / "transactions_svc"
    / "anomaly.py"
)
_spec = importlib.util.spec_from_file_location("anomaly_under_test", _anomaly_path)
anomaly = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(anomaly)


def make_user(db, user_id, name, surname, bank_number, username):
    user = User(
        user_id=user_id,
        name=name,
        surname=surname,
        balance=1000,
        date_of_birth=date(1990, 1, 1),
        bank_number=bank_number,
        username=username,
        password="x",
    )
    db.add(user)
    db.flush()
    return user


def make_tx(db, sender_id, receiver_id, amount, receiver_name, receiver_surname):
    tx = Transaction(
        sender_id=sender_id,
        receiver_id=receiver_id,
        receiver_name=receiver_name,
        receiver_surname=receiver_surname,
        amount=amount,
        transaction_date_and_time=datetime(2024, 1, 1, 12, 0, 0),
        amount_before=1000,
        amount_after=1000 - amount,
        transaction_type="transfer",
    )
    db.add(tx)
    db.flush()
    return tx


@pytest.fixture
def two_users(db_session):
    make_user(db_session, 1, "Alice", "Sender", "1111222233334444", "alice")
    make_user(db_session, 2, "John", "Doe", "5555666677778888", "john")
    return db_session


# ---- amount validation ----------------------------------------------------


def test_amount_valid_within_normal_range(two_users):
    db = two_users
    for amt in (100, 110, 90, 105, 95, 100):
        make_tx(db, 1, 2, amt, "John", "Doe")
    assert anomaly.is_amount_valid(db, 1, 100)["valid"] is True


def test_amount_invalid_outlier(two_users):
    db = two_users
    for amt in (100, 110, 90, 105, 95, 100):
        make_tx(db, 1, 2, amt, "John", "Doe")
    assert anomaly.is_amount_valid(db, 1, 100000)["valid"] is False


def test_amount_unknown_user_raises(db_session):
    with pytest.raises(ValueError):
        anomaly.is_amount_valid(db_session, 999, 100)


# ---- bank number validation ------------------------------------------------


def test_bank_number_exact_match_valid(two_users):
    db = two_users
    make_tx(db, 1, 2, 100, "John", "Doe")
    res = anomaly.is_bankNumber_valid(db, 1, "5555666677778888")
    assert res["valid"] is True


def test_bank_number_typo_flagged_with_suggestion(two_users):
    db = two_users
    make_tx(db, 1, 2, 100, "John", "Doe")
    # one-digit typo on a previously-used receiver bank number
    res = anomaly.is_bankNumber_valid(db, 1, "5555666677778889")
    assert res["valid"] is False
    assert res["suggestion"] == "5555666677778888"
    assert res["receiver_name"] == "John Doe"
    assert res["error_position"] == 15


def test_bank_number_no_history_valid(two_users):
    db = two_users
    # sender 1 has no prior transactions → nothing to compare → valid
    res = anomaly.is_bankNumber_valid(db, 1, "9999000011112222")
    assert res["valid"] is True


# ---- full name validation --------------------------------------------------


def test_fullname_normal_order_valid(two_users):
    db = two_users
    make_tx(db, 1, 2, 100, "John", "Doe")
    res = anomaly.is_fullname_valid(db, 1, "5555666677778888", "John Doe")
    assert res["valid"] is True


def test_fullname_swapped_order_valid(two_users):
    db = two_users
    make_tx(db, 1, 2, 100, "John", "Doe")
    res = anomaly.is_fullname_valid(db, 1, "5555666677778888", "Doe John")
    assert res["valid"] is True


def test_fullname_mismatch_suggests_known_name(two_users):
    db = two_users
    make_tx(db, 1, 2, 100, "John", "Doe")
    res = anomaly.is_fullname_valid(db, 1, "5555666677778888", "Jane Smith")
    assert res["valid"] is False
    assert res["suggestion"] == "John Doe"


def test_fullname_unknown_bank_number_valid(two_users):
    db = two_users
    res = anomaly.is_fullname_valid(db, 1, "0000000000000000", "Anyone Here")
    assert res["valid"] is True
