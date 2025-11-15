"""
Script to parse transaction_id and transaction_text from the transactions table.

Exports the data to JSON format for further RAG processing (embeddings, ChromaDB).
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional

project_root = Path(__file__).resolve().parents[4] 
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from shared.models import SessionLocal, Transaction

# Load environment variables
load_dotenv()


def parse_transactions(
    output_file: Optional[str] = None,
    limit: Optional[int] = None,
    filter_posted: bool = True,
) -> List[Dict[str, any]]:
    """
    Parse transaction_id and transaction_text from the transactions table.
    
    Args:
        output_file: Path to output JSON file. If None, returns data without saving.
        limit: Maximum number of transactions to fetch. None = all transactions.
        filter_posted: If True, only fetch posted transactions (transaction_posted=True).
    
    Returns:
        List of dictionaries with transaction_id and transaction_text.
    """
    db: Session = SessionLocal()
    
    try:
        # Build query
        query = db.query(
            Transaction.transaction_id,
            Transaction.transaction_text,
            Transaction.amount,
            Transaction.receiver_name,
            Transaction.receiver_surname,
            Transaction.transaction_date_and_time,
        )
        
        # Filter only posted transactions if requested
        if filter_posted:
            query = query.filter(Transaction.transaction_posted == True)
        
        # Filter out transactions with empty/null text
        query = query.filter(Transaction.transaction_text.isnot(None))
        query = query.filter(Transaction.transaction_text != "")
        
        # Apply limit if specified
        if limit:
            query = query.limit(limit)
        
        # Fetch all transactions
        transactions = query.all()
        
        # Parse into list of dicts
        parsed_data = []
        for tx in transactions:
            # Create a rich text representation for better RAG context
            recipient_full_name = f"{tx.receiver_name} {tx.receiver_surname}"
            
            # Enhanced text with context (better for embeddings)
            enhanced_text = (
                f"Transaction to {recipient_full_name} for {tx.amount} PLN. "
                f"Description: {tx.transaction_text}"
            )
            
            parsed_data.append({
                "transaction_id": tx.transaction_id,
                "transaction_text": tx.transaction_text,
                "enhanced_text": enhanced_text,
                "amount": float(tx.amount),
                "recipient_name": recipient_full_name,
                "date": tx.transaction_date_and_time.isoformat() if tx.transaction_date_and_time else None,
            })
        
        print(f"✓ Parsed {len(parsed_data)} transactions from database")
        
        # Save to file if output_file is specified
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(parsed_data, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Saved to {output_file}")
        
        return parsed_data
    
    finally:
        db.close()


def main():
    """
    Main entry point for the script.
    
    Parses transactions and saves to data/transactions.json by default.
    """
    # Default output location
    script_dir = Path(__file__).parent
    output_file = script_dir / "transactions.json"
    
    print("=" * 60)
    print("Transaction Parser for RAG")
    print("=" * 60)
    print(f"Output file: {output_file}")
    print()
    
    # Parse and save
    data = parse_transactions(
        output_file=str(output_file),
        filter_posted=True,  # Only posted transactions
        limit=None,  # Fetch all
    )
    
    print()
    print("=" * 60)
    print("Summary:")
    print(f"  Total transactions: {len(data)}")
    if data:
        print(f"  Sample transaction_id: {data[0]['transaction_id']}")
        print(f"  Sample text: {data[0]['transaction_text'][:50]}...")
    print("=" * 60)


if __name__ == "__main__":
    main()
