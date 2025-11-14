# Database Models

This directory contains the SQLAlchemy models for the banking application.

## Structure

- `__init__.py` - Database configuration and model exports
- `user.py` - User model
- `person_to_contact.py` - Emergency contact model
- `transaction.py` - Transaction model

## Models Overview

### PersonToContact

Emergency contact information for users.

**Table:** `person_to_contact`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| person_to_contact_id | Integer | PRIMARY KEY | Unique identifier |
| name | String(100) | NOT NULL | Contact's first name |
| surname | String(100) | NOT NULL | Contact's last name |
| phone_number | String(20) | NOT NULL | Contact phone number |
| email | String(100) | NOT NULL | Contact email address |

**Relationships:**
- One-to-many with User (one contact can be linked to multiple users)

---

### User

Main user account information.

**Table:** `users`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| user_id | Integer | PRIMARY KEY | Unique identifier |
| name | String(100) | NOT NULL | User's first name |
| surname | String(100) | NOT NULL | User's last name |
| balance | Numeric(15,2) | NOT NULL, DEFAULT 0.00 | Current account balance |
| date_of_birth | Date | NOT NULL | User's date of birth |
| bank_number | String(50) | UNIQUE, NOT NULL | Bank account number |
| person_to_contact_id | Integer | FOREIGN KEY, NULLABLE | Reference to emergency contact |
| username | String(100) | UNIQUE, NOT NULL | Login username |
| password | String(255) | NOT NULL | Hashed password |

**Relationships:**
- Many-to-one with PersonToContact (person_to_contact)
- One-to-many with Transaction as sender (sent_transactions)
- One-to-many with Transaction as receiver (received_transactions)

---

### Transaction

Transaction records between users.

**Table:** `transactions`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| transaction_id | Integer | PRIMARY KEY | Unique identifier |
| sender_id | Integer | FOREIGN KEY, NOT NULL | User ID sending money |
| receiver_id | Integer | FOREIGN KEY, NOT NULL | User ID receiving money |
| receiver_name | String(100) | NOT NULL | Receiver's first name (cached) |
| receiver_surname | String(100) | NOT NULL | Receiver's last name (cached) |
| amount | Numeric(15,2) | NOT NULL | Transaction amount |
| transaction_date_and_time | DateTime | NOT NULL | When transaction occurred |
| amount_before | Numeric(15,2) | NOT NULL | Sender's balance before transaction |
| amount_after | Numeric(15,2) | NOT NULL | Sender's balance after transaction |
| transaction_type | String(50) | NOT NULL | Type of transaction (e.g., 'transfer', 'payment') |
| transaction_posted | Boolean | NOT NULL, DEFAULT False | Whether transaction is complete |
| transaction_text | String(500) | NULLABLE | Optional transaction description/note |

**Relationships:**
- Many-to-one with User as sender (sender)
- Many-to-one with User as receiver (receiver)

---

## Usage

### Importing Models

```python
from backend.models import User, PersonToContact, Transaction, Base, engine, SessionLocal
```

### Creating Tables

```python
from backend.models import Base, engine

# Create all tables
Base.metadata.create_all(bind=engine)
```

### Using Session

```python
from backend.models import SessionLocal, User

# Create a session
session = SessionLocal()

try:
    # Query users
    users = session.query(User).all()
    
    # Add new user
    new_user = User(
        name="John",
        surname="Doe",
        username="johndoe",
        password="hashed_password",
        bank_number="1234567890",
        date_of_birth="1990-01-01",
        balance=1000.00
    )
    session.add(new_user)
    session.commit()
finally:
    session.close()
```

### Dependency Injection (FastAPI)

```python
from backend.db import get_db
from fastapi import Depends

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users
```

## Notes

- All passwords should be hashed before storing (use bcrypt or similar)
- Balance is stored with 2 decimal places precision
- Transaction records maintain immutable history (amount_before, amount_after)
- receiver_name and receiver_surname are cached to preserve transaction history even if user changes their name
- person_to_contact_id is nullable (users can exist without emergency contact)