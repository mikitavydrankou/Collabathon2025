"""
Example usage of transaction operations.

This file demonstrates how to use the transaction API endpoints
and services in various scenarios.
"""

from decimal import Decimal

import requests

# Base API URL
BASE_URL = "http://localhost:8000"


# ============================================================================
# Example 1: Create a Simple Transaction
# ============================================================================


def example_create_transaction():
    """Create a basic money transfer"""
    print("\n=== Example 1: Create Transaction ===")

    response = requests.post(
        f"{BASE_URL}/transactions/create",
        json={
            "user_id": 1,
            "receiver_bank_number": "4276987654321098",
            "receiver_name": "Kate",
            "receiver_surname": "Davis",
            "amount": 1500.00,
            "transaction_text": "Rent payment - January 2025",
        },
    )

    result = response.json()

    if result["success"]:
        print(f"✓ Transaction created successfully!")
        print(f"  Transaction ID: {result['transaction_id']}")
        print(f"  Amount: {result['transaction']['amount']} PLN")
        print(f"  New balance: {result['transaction']['amount_after']} PLN")
    else:
        print(f"✗ Transaction failed: {result['message']}")

    return result


# ============================================================================
# Example 2: Get User Transaction History
# ============================================================================


def example_get_transactions(user_id: int = 1):
    """Retrieve transaction history for a user"""
    print(f"\n=== Example 2: Get Transactions for User {user_id} ===")

    response = requests.get(
        f"{BASE_URL}/transactions/{user_id}",
        params={"limit": 10, "offset": 0, "posted_only": True},
    )

    data = response.json()

    print(f"Total transactions: {data['total']}")
    print(f"Showing {data['page_size']} transactions (page {data['page']})")
    print("\nRecent transactions:")

    for t in data["transactions"][:5]:  # Show first 5
        direction = "Sent to" if t["is_sent"] else "Received from"
        print(
            f"  {t['transaction_date'][:10]}: {direction} "
            f"{t['receiver_name']} {t['receiver_surname']} - "
            f"{t['amount']} PLN"
        )

    return data


# ============================================================================
# Example 3: Get Transaction Statistics
# ============================================================================


def example_get_stats(user_id: int = 1):
    """Get aggregated transaction statistics"""
    print(f"\n=== Example 3: Transaction Statistics for User {user_id} ===")

    response = requests.get(f"{BASE_URL}/transactions/{user_id}/stats")
    stats = response.json()

    print(f"Total sent: {stats['total_sent']} PLN")
    print(f"Total received: {stats['total_received']} PLN")
    print(f"Net balance change: {stats['total_received'] - stats['total_sent']} PLN")
    print(f"Total transactions: {stats['total_transactions']}")
    print(f"  - Sent: {stats['sent_count']}")
    print(f"  - Received: {stats['received_count']}")
    print(f"  - Pending: {stats['pending_count']}")

    return stats


# ============================================================================
# Example 4: Verify Receiver Before Sending
# ============================================================================


def example_verify_receiver(bank_number: str, name: str, surname: str):
    """Verify receiver details before creating transaction"""
    print(f"\n=== Example 4: Verify Receiver ===")
    print(f"Checking: {name} {surname} - {bank_number}")

    response = requests.post(
        f"{BASE_URL}/transactions/verify-receiver",
        params={"bank_number": bank_number, "name": name, "surname": surname},
    )

    result = response.json()

    if result["valid"]:
        print("✓ Receiver verified successfully!")
    else:
        print(f"✗ Verification failed: {result['message']}")

    return result


# ============================================================================
# Example 5: Get Recent Receivers for Quick Transfer
# ============================================================================


def example_get_recent_receivers(user_id: int = 1):
    """Get list of recent transaction receivers"""
    print(f"\n=== Example 5: Recent Receivers for User {user_id} ===")

    response = requests.get(
        f"{BASE_URL}/transactions/{user_id}/recent-receivers", params={"limit": 5}
    )

    data = response.json()

    print(f"Found {data['count']} recent receivers:")
    for receiver in data["recent_receivers"]:
        print(f"  {receiver['receiver_name']} {receiver['receiver_surname']}")
        print(f"    Account: {receiver['receiver_bank_account']}")
        print(
            f"    Last transfer: {receiver['last_amount']} PLN on "
            f"{receiver['last_transaction_date'][:10]}"
        )

    return data


# ============================================================================
# Example 6: Get Transaction Details
# ============================================================================


def example_get_transaction_detail(user_id: int, transaction_id: int):
    """Get detailed information about a specific transaction"""
    print(f"\n=== Example 6: Transaction Detail ===")

    response = requests.get(f"{BASE_URL}/transactions/{user_id}/{transaction_id}")

    if response.status_code == 200:
        transaction = response.json()
        print(f"Transaction ID: {transaction['transaction_id']}")
        print(f"Date: {transaction['transaction_date']}")
        print(f"From: {transaction['sender_name']} {transaction['sender_surname']}")
        print(f"  Account: {transaction['sender_bank_account']}")
        print(f"To: {transaction['receiver_name']} {transaction['receiver_surname']}")
        print(f"  Account: {transaction['receiver_bank_account']}")
        print(f"Amount: {transaction['amount']} PLN")
        print(f"Description: {transaction['transaction_text']}")
        print(f"Balance before: {transaction['amount_before']} PLN")
        print(f"Balance after: {transaction['amount_after']} PLN")
        return transaction
    else:
        print(f"✗ Transaction not found or access denied")
        return None


# ============================================================================
# Example 7: Filter Transactions by Date and Amount
# ============================================================================


def example_filter_transactions(user_id: int = 1):
    """Filter transactions by various criteria"""
    print(f"\n=== Example 7: Filter Transactions ===")

    response = requests.get(
        f"{BASE_URL}/transactions/{user_id}",
        params={
            "min_amount": 1000.00,
            "max_amount": 10000.00,
            "posted_only": True,
            "limit": 10,
        },
    )

    data = response.json()

    print(f"Transactions between 1,000 and 10,000 PLN:")
    print(f"Found {data['page_size']} transactions")

    for t in data["transactions"]:
        print(
            f"  {t['transaction_date'][:10]}: {t['amount']} PLN - "
            f"{t['transaction_text']}"
        )

    return data


# ============================================================================
# Example 8: Complete Transaction Flow with Validation
# ============================================================================


def example_complete_transaction_flow():
    """Demonstrate complete transaction flow with all validations"""
    print("\n=== Example 8: Complete Transaction Flow ===")

    # Step 1: Define transaction details
    user_id = 1
    receiver_bank = "4276987654321098"
    receiver_name = "Kate"
    receiver_surname = "Davis"
    amount = 2500.00

    print(f"\nStep 1: Preparing to send {amount} PLN")

    # Step 2: Verify receiver
    print("\nStep 2: Verifying receiver...")
    verify_result = requests.post(
        f"{BASE_URL}/transactions/verify-receiver",
        params={
            "bank_number": receiver_bank,
            "name": receiver_name,
            "surname": receiver_surname,
        },
    ).json()

    if not verify_result["valid"]:
        print(f"✗ Receiver verification failed: {verify_result['message']}")
        return None

    print("✓ Receiver verified")

    # Step 3: Check user's balance (get recent transaction to see current balance)
    print("\nStep 3: Checking balance...")
    stats = requests.get(f"{BASE_URL}/transactions/{user_id}/stats").json()
    print(f"✓ Account statistics retrieved")

    # Step 4: Create transaction
    print("\nStep 4: Creating transaction...")
    transaction_result = requests.post(
        f"{BASE_URL}/transactions/create",
        json={
            "user_id": user_id,
            "receiver_bank_number": receiver_bank,
            "receiver_name": receiver_name,
            "receiver_surname": receiver_surname,
            "amount": amount,
            "transaction_text": "Monthly allowance",
        },
    ).json()

    if transaction_result["success"]:
        print(f"✓ Transaction completed!")
        print(f"  Transaction ID: {transaction_result['transaction_id']}")
        print(f"  New balance: {transaction_result['transaction']['amount_after']} PLN")
        return transaction_result
    else:
        print(f"✗ Transaction failed: {transaction_result['message']}")
        return None


# ============================================================================
# Example 9: Handle Transaction Errors
# ============================================================================


def example_handle_errors():
    """Demonstrate error handling for various scenarios"""
    print("\n=== Example 9: Error Handling ===")

    # Test 1: Insufficient funds
    print("\nTest 1: Insufficient funds")
    response = requests.post(
        f"{BASE_URL}/transactions/create",
        json={
            "user_id": 4,  # Sarah Taylor has 30,000 PLN
            "receiver_bank_number": "4276987654321098",
            "receiver_name": "Kate",
            "receiver_surname": "Davis",
            "amount": 50000.00,  # More than available
            "transaction_text": "Test insufficient funds",
        },
    )
    result = response.json()
    print(f"Response: {result['message']}")

    # Test 2: Invalid receiver
    print("\nTest 2: Invalid receiver (non-existent bank account)")
    response = requests.post(
        f"{BASE_URL}/transactions/create",
        json={
            "user_id": 1,
            "receiver_bank_number": "9999999999999999",
            "receiver_name": "John",
            "receiver_surname": "Doe",
            "amount": 100.00,
            "transaction_text": "Test invalid receiver",
        },
    )
    result = response.json()
    print(f"Response: {result['message']}")

    # Test 3: Name mismatch
    print("\nTest 3: Name mismatch")
    response = requests.post(
        f"{BASE_URL}/transactions/create",
        json={
            "user_id": 1,
            "receiver_bank_number": "4276987654321098",
            "receiver_name": "Wrong",
            "receiver_surname": "Name",
            "amount": 100.00,
            "transaction_text": "Test name mismatch",
        },
    )
    result = response.json()
    print(f"Response: {result['message']}")


# ============================================================================
# Example 10: Pagination for Large Result Sets
# ============================================================================


def example_pagination(user_id: int = 1):
    """Demonstrate pagination for large transaction lists"""
    print(f"\n=== Example 10: Pagination ===")

    page_size = 5
    all_transactions = []
    page = 0

    while True:
        response = requests.get(
            f"{BASE_URL}/transactions/{user_id}",
            params={"limit": page_size, "offset": page * page_size},
        )

        data = response.json()
        transactions = data["transactions"]

        if not transactions:
            break

        all_transactions.extend(transactions)
        print(f"Page {page + 1}: Retrieved {len(transactions)} transactions")

        if not data["has_more"]:
            break

        page += 1

    print(f"\nTotal transactions retrieved: {len(all_transactions)}")
    return all_transactions


# ============================================================================
# Main execution
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("TRANSACTION API EXAMPLES")
    print("=" * 70)

    try:
        # Run examples
        example_get_transactions(user_id=1)
        example_get_stats(user_id=1)
        example_verify_receiver("4276987654321098", "Kate", "Davis")
        example_get_recent_receivers(user_id=1)
        example_filter_transactions(user_id=1)

        # Uncomment to run transaction creation examples
        # example_create_transaction()
        # example_complete_transaction_flow()

        # Uncomment to see error handling
        # example_handle_errors()

        print("\n" + "=" * 70)
        print("Examples completed successfully!")
        print("=" * 70)

    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Cannot connect to API server")
        print("Make sure the backend is running at http://localhost:8000")
    except Exception as e:
        print(f"\n✗ Error: {e}")
