"""Seed script to populate Firestore with sample expenses."""
import datetime
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-1945f3f8e8c8"

SAMPLE_EXPENSES = [
    {
        "merchant": "Whole Foods Market",
        "amount": 78.45,
        "category": "Groceries",
        "payment_method": "Credit Card",
        "note": "Weekly organic groceries & produce",
        "date": "2026-10-10",
        "created_at": "2026-10-10T14:32:00Z",
    },
    {
        "merchant": "Uber",
        "amount": 24.50,
        "category": "Transportation",
        "payment_method": "Credit Card",
        "note": "Ride home from downtown conference",
        "date": "2026-10-11",
        "created_at": "2026-10-11T21:15:00Z",
    },
    {
        "merchant": "Blue Bottle Coffee",
        "amount": 6.75,
        "category": "Food & Dining",
        "payment_method": "Cash",
        "note": "Morning latte and pastry",
        "date": "2026-10-12",
        "created_at": "2026-10-12T08:45:00Z",
    },
    {
        "merchant": "Pacific Gas & Electric",
        "amount": 115.20,
        "category": "Utilities",
        "payment_method": "Bank Account",
        "note": "Monthly electricity and gas bill",
        "date": "2026-10-08",
        "created_at": "2026-10-08T10:00:00Z",
    },
    {
        "merchant": "Netflix",
        "amount": 15.99,
        "category": "Entertainment",
        "payment_method": "Credit Card",
        "note": "Monthly streaming subscription",
        "date": "2026-10-05",
        "created_at": "2026-10-05T03:00:00Z",
    },
    {
        "merchant": "Trader Joe's",
        "amount": 42.80,
        "category": "Groceries",
        "payment_method": "Credit Card",
        "note": "Snacks and pantry supplies",
        "date": "2026-10-12",
        "created_at": "2026-10-12T17:20:00Z",
    },
    {
        "merchant": "Corner Bakery",
        "amount": 14.50,
        "category": "Food & Dining",
        "payment_method": "Cash",
        "note": "Lunch sandwich with colleague",
        "date": "2026-10-11",
        "created_at": "2026-10-11T12:30:00Z",
    },
]

def seed_database():
    print(f"Connecting to Firestore for project: {PROJECT_ID}...")
    db = firestore.Client(project=PROJECT_ID)
    collection = db.collection("expenses")
    
    count = 0
    for item in SAMPLE_EXPENSES:
        doc_ref = collection.document()
        item_data = dict(item)
        item_data["id"] = doc_ref.id
        doc_ref.set(item_data)
        print(f"Added expense: {item['merchant']} - ${item['amount']} ({item['category']} via {item['payment_method']}) [id: {doc_ref.id}]")
        count += 1
        
    print(f"\nSuccessfully seeded {count} expense items to collection 'expenses'.")

if __name__ == "__main__":
    seed_database()
