from datetime import date, datetime
from decimal import Decimal

from backend.models import PersonToContact, SessionLocal, Transaction, User


def seed_database():
    """Seeds the database with test data"""
    db = SessionLocal()

    try:
        # Check if data already exists
        existing_users = db.query(User).count()
        if existing_users > 0:
            print("✓ Database already seeded, skipping...")
            return

        print("Starting database seeding...")

        # Create contacts
        contact1 = PersonToContact(
            name="Mary",
            surname="Johnson",
            phone_number="+1-555-123-4567",
            email="mary.johnson@example.com",
        )

        contact2 = PersonToContact(
            name="Peter",
            surname="Smith",
            phone_number="+1-555-765-4321",
            email="peter.smith@example.com",
        )

        contact3 = PersonToContact(
            name="Anna",
            surname="Williams",
            phone_number="+1-555-555-1234",
            email="anna.williams@example.com",
        )

        db.add_all([contact1, contact2, contact3])
        db.flush()

        # Create users
        user1 = User(
            name="Alex",
            surname="Brown",
            balance=Decimal("50000.00"),
            date_of_birth=date(1990, 5, 15),
            bank_number="4276123456789012",
            username="alex.brown",
            password="hashed_password_123",
            person_to_contact_id=contact1.person_to_contact_id,
        )

        user2 = User(
            name="Kate",
            surname="Davis",
            balance=Decimal("75000.00"),
            date_of_birth=date(1985, 8, 22),
            bank_number="4276987654321098",
            username="kate.davis",
            password="hashed_password_456",
            person_to_contact_id=contact2.person_to_contact_id,
        )

        user3 = User(
            name="Mike",
            surname="Wilson",
            balance=Decimal("120000.00"),
            date_of_birth=date(1992, 3, 10),
            bank_number="4276555511112222",
            username="mike.wilson",
            password="hashed_password_789",
            person_to_contact_id=contact3.person_to_contact_id,
        )

        user4 = User(
            name="Sarah",
            surname="Taylor",
            balance=Decimal("30000.00"),
            date_of_birth=date(1995, 11, 30),
            bank_number="4276333344445555",
            username="sarah.taylor",
            password="hashed_password_101",
            person_to_contact_id=None,
        )

        db.add_all([user1, user2, user3, user4])
        db.flush()

        # Create transactions
        transaction1 = Transaction(
            sender_id=user1.user_id,
            receiver_id=user2.user_id,
            receiver_name=user2.name,
            receiver_surname=user2.surname,
            amount=Decimal("5000.00"),
            transaction_date_and_time=datetime(2025, 1, 15, 10, 30, 0),
            amount_before=Decimal("55000.00"),
            amount_after=Decimal("50000.00"),
            transaction_type="transfer",
            transaction_posted=True,
            transaction_text="Payment for services",
        )

        transaction2 = Transaction(
            sender_id=user3.user_id,
            receiver_id=user1.user_id,
            receiver_name=user1.name,
            receiver_surname=user1.surname,
            amount=Decimal("10000.00"),
            transaction_date_and_time=datetime(2025, 1, 20, 14, 15, 0),
            amount_before=Decimal("130000.00"),
            amount_after=Decimal("120000.00"),
            transaction_type="transfer",
            transaction_posted=True,
            transaction_text="Debt repayment",
        )

        transaction3 = Transaction(
            sender_id=user2.user_id,
            receiver_id=user4.user_id,
            receiver_name=user4.name,
            receiver_surname=user4.surname,
            amount=Decimal("2500.00"),
            transaction_date_and_time=datetime(2025, 1, 22, 16, 45, 0),
            amount_before=Decimal("77500.00"),
            amount_after=Decimal("75000.00"),
            transaction_type="transfer",
            transaction_posted=True,
            transaction_text="Birthday gift",
        )

        transaction4 = Transaction(
            sender_id=user4.user_id,
            receiver_id=user3.user_id,
            receiver_name=user3.name,
            receiver_surname=user3.surname,
            amount=Decimal("1500.00"),
            transaction_date_and_time=datetime(2025, 1, 25, 9, 20, 0),
            amount_before=Decimal("31500.00"),
            amount_after=Decimal("30000.00"),
            transaction_type="transfer",
            transaction_posted=True,
            transaction_text="Rent payment",
        )

        transaction5 = Transaction(
            sender_id=user1.user_id,
            receiver_id=user3.user_id,
            receiver_name=user3.name,
            receiver_surname=user3.surname,
            amount=Decimal("7500.00"),
            transaction_date_and_time=datetime(2025, 1, 28, 11, 0, 0),
            amount_before=Decimal("57500.00"),
            amount_after=Decimal("50000.00"),
            transaction_type="transfer",
            transaction_posted=False,
            transaction_text="Project investment",
        )

        db.add_all(
            [transaction1, transaction2, transaction3, transaction4, transaction5]
        )
        db.commit()

        print("✓ Database seeded successfully!")
        print(f"  - Created {db.query(PersonToContact).count()} contacts")
        print(f"  - Created {db.query(User).count()} users")
        print(f"  - Created {db.query(Transaction).count()} transactions")

    except Exception as e:
        print(f"✗ Seeding failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()
