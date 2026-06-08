from datetime import date, datetime, timedelta
from decimal import Decimal

from shared.models import PersonToContact, SessionLocal, Transaction, User
from shared.security import get_password_hash


def seed_database():
    """Seeds the database with test data"""
    db = SessionLocal()

    try:
        # Check if data already exists
        existing_users = db.query(User).count()
        if existing_users > 0:
            print("✓ Database already seeded, skipping...")
            print(f"  - Current contacts: {db.query(PersonToContact).count()}")
            print(f"  - Current users: {db.query(User).count()}")
            print(f"  - Current transactions: {db.query(Transaction).count()}")
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
            password=get_password_hash("password123"),
            person_to_contact_id=contact1.person_to_contact_id,
        )

        user2 = User(
            name="Kate",
            surname="Davis",
            balance=Decimal("75000.00"),
            date_of_birth=date(1985, 8, 22),
            bank_number="4276987654321098",
            username="kate.davis",
            password=get_password_hash("password456"),
            person_to_contact_id=contact2.person_to_contact_id,
        )

        user3 = User(
            name="Mike",
            surname="Wilson",
            balance=Decimal("120000.00"),
            date_of_birth=date(1992, 3, 10),
            bank_number="4276555511112222",
            username="mike.wilson",
            password=get_password_hash("password789"),
            person_to_contact_id=contact3.person_to_contact_id,
        )

        user4 = User(
            name="Sarah",
            surname="Taylor",
            balance=Decimal("30000.00"),
            date_of_birth=date(1995, 11, 30),
            bank_number="4276333344445555",
            username="sarah.taylor",
            password=get_password_hash("password101"),
            person_to_contact_id=None,
        )

        db.add_all([user1, user2, user3, user4])
        db.flush()

        # Create service provider "users" (companies/utilities)
        electricity_provider = User(
            name="Energy",
            surname="Company",
            balance=Decimal("0.00"),
            date_of_birth=date(2000, 1, 1),
            bank_number="4276000000000001",
            username="energy.provider",
            password=get_password_hash("provider123"),
            person_to_contact_id=None,
        )

        service_provider = User(
            name="Service",
            surname="Provider",
            balance=Decimal("0.00"),
            date_of_birth=date(2000, 1, 1),
            bank_number="4276000000000002",
            username="service.provider",
            password=get_password_hash("provider123"),
            person_to_contact_id=None,
        )

        db.add_all([electricity_provider, service_provider])
        db.flush()

        # Create transactions
        transactions = []
        
        # Original transactions
        transactions.extend([
            Transaction(
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
            ),
            Transaction(
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
            ),
            Transaction(
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
            ),
            Transaction(
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
            ),
            Transaction(
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
            ),
            Transaction(
                sender_id=user1.user_id,
                receiver_id=user2.user_id,
                receiver_name=user2.name,
                receiver_surname=user2.surname,
                amount=Decimal("200.00"),
                transaction_date_and_time=datetime.now() - timedelta(days=365),
                amount_before=Decimal("50200.00"),
                amount_after=Decimal("50000.00"),
                transaction_type="transfer",
                transaction_posted=True,
                transaction_text="birthday gift for niece",
            ),
        ])

        # Electricity bill transactions - monthly recurring
        electricity_transactions = [
            # Alex's electricity bills
            ("alex.brown", user1.user_id, "1850.00", datetime(2024, 11, 5, 8, 15, 0), "Monthly electricity bill payment - November 2024"),
            ("alex.brown", user1.user_id, "1620.00", datetime(2024, 10, 5, 8, 20, 0), "Electricity bill for October - residential usage"),
            ("alex.brown", user1.user_id, "1940.00", datetime(2024, 9, 5, 9, 10, 0), "Electric utility payment September 2024"),
            ("alex.brown", user1.user_id, "2100.00", datetime(2024, 8, 5, 8, 30, 0), "Power bill payment - high usage month August"),
            ("alex.brown", user1.user_id, "1780.00", datetime(2024, 7, 5, 8, 45, 0), "Electricity charges July 2024"),
            
            # Kate's electricity bills
            ("kate.davis", user2.user_id, "2250.00", datetime(2024, 11, 8, 10, 0, 0), "Monthly electric bill payment November"),
            ("kate.davis", user2.user_id, "2150.00", datetime(2024, 10, 8, 10, 15, 0), "Electricity payment for October 2024"),
            ("kate.davis", user2.user_id, "2380.00", datetime(2024, 9, 8, 9, 45, 0), "Power utility bill September"),
            ("kate.davis", user2.user_id, "2560.00", datetime(2024, 8, 8, 10, 30, 0), "Electric bill August - air conditioning usage"),
            
            # Mike's electricity bills
            ("mike.wilson", user3.user_id, "1450.00", datetime(2024, 11, 10, 7, 30, 0), "November electricity bill payment"),
            ("mike.wilson", user3.user_id, "1380.00", datetime(2024, 10, 10, 7, 45, 0), "Monthly power bill October 2024"),
            ("mike.wilson", user3.user_id, "1520.00", datetime(2024, 9, 10, 8, 0, 0), "Electricity bill September - apartment"),
            
            # Sarah's electricity bills
            ("sarah.taylor", user4.user_id, "980.00", datetime(2024, 11, 12, 11, 20, 0), "Electric utility payment November"),
            ("sarah.taylor", user4.user_id, "920.00", datetime(2024, 10, 12, 11, 30, 0), "Electricity bill October 2024"),
            ("sarah.taylor", user4.user_id, "1050.00", datetime(2024, 9, 12, 11, 15, 0), "Power bill payment September"),
        ]

        # Calculate realistic balances for electricity transactions
        base_balances = {
            user1.user_id: Decimal("52000.00"),
            user2.user_id: Decimal("77000.00"),
            user3.user_id: Decimal("122000.00"),
            user4.user_id: Decimal("32000.00"),
        }
        
        for username, sender_id, amount, date_time, description in electricity_transactions:
            amount_dec = Decimal(amount)
            amount_before = base_balances[sender_id]
            amount_after = amount_before - amount_dec
            base_balances[sender_id] = amount_after  # Update for next transaction
            
            transactions.append(Transaction(
                sender_id=sender_id,
                receiver_id=electricity_provider.user_id,
                receiver_name=electricity_provider.name,
                receiver_surname=electricity_provider.surname,
                amount=amount_dec,
                transaction_date_and_time=date_time,
                amount_before=amount_before,
                amount_after=amount_after,
                transaction_type="transfer",
                transaction_posted=True,
                transaction_text=description,
            ))

        # Other varied transactions
        other_transactions = [
            # Groceries
            (user1.user_id, "450.00", datetime(2024, 11, 14, 18, 30, 0), "Weekly grocery shopping at supermarket"),
            (user2.user_id, "680.00", datetime(2024, 11, 13, 19, 15, 0), "Grocery shopping - organic products"),
            (user3.user_id, "520.00", datetime(2024, 11, 12, 17, 45, 0), "Supermarket purchase - weekly groceries"),
            (user4.user_id, "380.00", datetime(2024, 11, 11, 18, 0, 0), "Food shopping at local market"),
            
            # Internet/Phone bills
            (user1.user_id, "599.00", datetime(2024, 11, 1, 9, 0, 0), "Monthly internet subscription payment"),
            (user2.user_id, "799.00", datetime(2024, 11, 2, 9, 30, 0), "Internet and cable TV package"),
            (user3.user_id, "499.00", datetime(2024, 11, 3, 10, 0, 0), "Broadband internet monthly fee"),
            (user4.user_id, "399.00", datetime(2024, 11, 4, 10, 30, 0), "Internet service provider payment"),
            
            # Gas/Heating bills
            (user1.user_id, "1200.00", datetime(2024, 11, 6, 8, 0, 0), "Natural gas bill November 2024"),
            (user2.user_id, "1450.00", datetime(2024, 11, 7, 8, 30, 0), "Heating bill payment - gas company"),
            (user3.user_id, "980.00", datetime(2024, 11, 8, 9, 0, 0), "Gas utility payment November"),
            
            # Water bills
            (user1.user_id, "320.00", datetime(2024, 11, 9, 7, 45, 0), "Water and sewage bill payment"),
            (user2.user_id, "380.00", datetime(2024, 11, 10, 8, 15, 0), "Municipal water services November"),
            (user4.user_id, "290.00", datetime(2024, 11, 11, 8, 45, 0), "Water utility bill payment"),
            
            # Insurance
            (user1.user_id, "2500.00", datetime(2024, 11, 1, 10, 0, 0), "Monthly health insurance premium"),
            (user2.user_id, "3200.00", datetime(2024, 11, 1, 10, 30, 0), "Health and dental insurance payment"),
            (user3.user_id, "1800.00", datetime(2024, 11, 1, 11, 0, 0), "Insurance premium - health coverage"),
            
            # Gym/Fitness
            (user1.user_id, "899.00", datetime(2024, 11, 3, 6, 0, 0), "Monthly gym membership fee"),
            (user2.user_id, "1200.00", datetime(2024, 11, 4, 6, 30, 0), "Premium fitness club membership"),
            (user3.user_id, "750.00", datetime(2024, 11, 5, 7, 0, 0), "Gym subscription monthly payment"),
            
            # Streaming services
            (user1.user_id, "199.00", datetime(2024, 11, 15, 12, 0, 0), "Netflix subscription payment"),
            (user2.user_id, "159.00", datetime(2024, 11, 16, 12, 30, 0), "Spotify premium membership"),
            (user3.user_id, "249.00", datetime(2024, 11, 17, 13, 0, 0), "Streaming services bundle payment"),
            
            # Restaurants/Dining
            (user1.user_id, "850.00", datetime(2024, 11, 18, 20, 30, 0), "Dinner at Italian restaurant"),
            (user2.user_id, "1200.00", datetime(2024, 11, 19, 19, 45, 0), "Fine dining - anniversary celebration"),
            (user4.user_id, "450.00", datetime(2024, 11, 20, 21, 0, 0), "Restaurant payment - sushi bar"),
            
            # Transportation
            (user1.user_id, "250.00", datetime(2024, 11, 21, 8, 30, 0), "Monthly public transport pass"),
            (user3.user_id, "2500.00", datetime(2024, 11, 22, 9, 0, 0), "Car insurance monthly premium"),
            (user4.user_id, "180.00", datetime(2024, 11, 23, 8, 45, 0), "Metro card refill - monthly"),
            
            # Medical
            (user2.user_id, "650.00", datetime(2024, 11, 24, 14, 30, 0), "Doctor appointment - general checkup"),
            (user1.user_id, "420.00", datetime(2024, 11, 25, 15, 0, 0), "Pharmacy - prescription medication"),
            
            # Education
            (user3.user_id, "4500.00", datetime(2024, 11, 26, 10, 0, 0), "Online course enrollment fee"),
            (user4.user_id, "1200.00", datetime(2024, 11, 27, 11, 0, 0), "Professional certification exam"),
            
            # Home maintenance
            (user2.user_id, "3200.00", datetime(2024, 11, 28, 13, 30, 0), "Plumbing repair services"),
            (user3.user_id, "1500.00", datetime(2024, 11, 29, 14, 0, 0), "Home cleaning service - monthly"),
        ]

        # Reset balances for other transactions (these happen in different time periods)
        base_balances = {
            user1.user_id: Decimal("48000.00"),
            user2.user_id: Decimal("72000.00"),
            user3.user_id: Decimal("118000.00"),
            user4.user_id: Decimal("29000.00"),
        }
        
        for sender_id, amount, date_time, description in other_transactions:
            amount_dec = Decimal(amount)
            amount_before = base_balances[sender_id]
            amount_after = amount_before - amount_dec
            base_balances[sender_id] = amount_after  # Update for next transaction
            
            transactions.append(Transaction(
                sender_id=sender_id,
                receiver_id=service_provider.user_id,
                receiver_name=service_provider.name,
                receiver_surname=service_provider.surname,
                amount=amount_dec,
                transaction_date_and_time=date_time,
                amount_before=amount_before,
                amount_after=amount_after,
                transaction_type="transfer",
                transaction_posted=True,
                transaction_text=description,
            ))

        db.add_all(transactions)
        db.commit()

        print("✓ Database seeded successfully!")
        print(f"  - Created {db.query(PersonToContact).count()} contacts")
        print(f"  - Created {db.query(User).count()} users")
        print(f"  - Created {db.query(Transaction).count()} transactions")
        print("\n=== Test Users ===")
        print("Username: alex.brown    | Password: password123")
        print("Username: kate.davis    | Password: password456")
        print("Username: mike.wilson   | Password: password789")
        print("Username: sarah.taylor  | Password: password101")

    except Exception as e:
        print(f"✗ Seeding failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()