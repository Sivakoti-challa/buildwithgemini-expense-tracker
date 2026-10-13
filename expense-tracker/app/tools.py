"""Firestore tools for Personal Expense Tracker agent."""
import datetime
import json
import os
import urllib.parse
import urllib.request
import uuid
from google import genai
from google.adk.tools import ToolContext
from google.cloud import firestore, storage
from google.genai import types

# Hardcoded project ID and public bucket name as required
PROJECT_ID = "qwiklabs-gcp-04-1945f3f8e8c8"
BUCKET_NAME = "expense-tracker-public-qwiklabs-gcp-04-1945f3f8e8c8"

# Allow Agent Identity token to be shared with Firestore / Cloud Storage
os.environ["GOOGLE_API_PREVENT_AGENT_TOKEN_SHARING_FOR_GCP_SERVICES"] = "False"

_db = None

def _get_db() -> firestore.Client:
    global _db
    if _db is None:
        os.environ["GOOGLE_API_PREVENT_AGENT_TOKEN_SHARING_FOR_GCP_SERVICES"] = "False"
        _db = firestore.Client(project=PROJECT_ID)
    return _db


def add_expense(
    merchant: str,
    amount: float,
    category: str,
    payment_method: str = "Credit Card",
    note: str = "",
    date: str = "",
) -> dict:
    """Record a new expense into Firestore.

    Args:
        merchant: The name of the store, vendor, or service (e.g. "Whole Foods", "Uber").
        amount: The total numerical cost of the expense (e.g. 24.50).
        category: The spending category (e.g. "Groceries", "Transportation", "Food & Dining", "Utilities", "Entertainment").
        payment_method: The payment method used, typically "Credit Card", "Bank Account", or "Cash".
        note: Optional notes or description about the purchase.
        date: The transaction date in YYYY-MM-DD format. If omitted, today's date is used.

    Returns:
        A dictionary with the saved expense details including its document ID.
    """
    db = _get_db()
    if not date:
        date = datetime.date.today().isoformat()

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    doc_ref = db.collection("expenses").document()
    
    expense_data = {
        "id": doc_ref.id,
        "merchant": merchant,
        "amount": round(float(amount), 2),
        "category": category,
        "payment_method": payment_method,
        "note": note,
        "date": date,
        "created_at": now_iso,
    }
    doc_ref.set(expense_data)
    return {
        "status": "success",
        "message": f"Recorded expense of ${expense_data['amount']:.2f} at {merchant} ({category} via {payment_method})",
        "expense": expense_data,
    }


def list_expenses(
    limit: int = 15,
    category: str = "",
    payment_method: str = "",
) -> list[dict]:
    """Retrieve recorded expenses from Firestore.

    Args:
        limit: Maximum number of transactions to retrieve (default: 15).
        category: Optional category filter (e.g. "Groceries", "Food & Dining").
        payment_method: Optional payment method filter (e.g. "Credit Card", "Cash", "Bank Account").

    Returns:
        A list of expense dictionaries sorted by date (newest first).
    """
    db = _get_db()
    query = db.collection("expenses")
    
    docs = query.stream()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        
        # Apply in-memory filtering if requested
        if category and data.get("category", "").lower() != category.lower():
            continue
        if payment_method and data.get("payment_method", "").lower() != payment_method.lower():
            continue
            
        results.append(data)

    # Sort newest first by date and created_at
    results.sort(key=lambda x: (x.get("date", ""), x.get("created_at", "")), reverse=True)
    return results[:limit]


def get_expense_summary() -> dict:
    """Calculate aggregated spending statistics from Firestore.

    Returns:
        A dictionary containing total spending, total transaction count,
        spending grouped by category, and spending grouped by payment method.
    """
    db = _get_db()
    docs = db.collection("expenses").stream()
    
    total_amount = 0.0
    count = 0
    by_category = {}
    by_payment_method = {}
    
    for doc in docs:
        data = doc.to_dict()
        amt = float(data.get("amount", 0.0))
        cat = data.get("category", "Uncategorized")
        pm = data.get("payment_method", "Other")
        
        total_amount += amt
        count += 1
        by_category[cat] = round(by_category.get(cat, 0.0) + amt, 2)
        by_payment_method[pm] = round(by_payment_method.get(pm, 0.0) + amt, 2)
        
    return {
        "total_spent": round(total_amount, 2),
        "total_transactions": count,
        "by_category": by_category,
        "by_payment_method": by_payment_method,
    }


DEFAULT_MONTHLY_BUDGETS = {
    "Groceries": 300.00,
    "Food & Dining": 150.00,
    "Transportation": 100.00,
    "Utilities": 200.00,
    "Entertainment": 50.00,
}
DEFAULT_OVERALL_BUDGET = 1000.00


def get_budget_status(category: str = "") -> dict:
    """Check budget health and remaining balance for a specific category or overall.

    Args:
        category: Optional category to check (e.g. "Groceries", "Food & Dining", "Transportation").
                  If omitted, returns the status for all tracked categories and overall total.

    Returns:
        A dictionary with budget limit, spent amount, remaining balance,
        percentage utilized, and status ("Healthy", "Warning", or "Over Budget").
    """
    db = _get_db()
    docs = db.collection("expenses").stream()

    spent_by_category = {}
    total_spent = 0.0
    for doc in docs:
        data = doc.to_dict()
        amt = float(data.get("amount", 0.0))
        cat = data.get("category", "Uncategorized")
        spent_by_category[cat] = spent_by_category.get(cat, 0.0) + amt
        total_spent += amt

    def _eval_status(spent: float, limit: float) -> dict:
        remaining = round(limit - spent, 2)
        pct = round((spent / limit) * 100, 1) if limit > 0 else 100.0
        if spent > limit:
            status = "Over Budget"
        elif pct >= 80.0:
            status = "Warning (Near Limit)"
        else:
            status = "Healthy"
        return {
            "budget_limit": limit,
            "spent": round(spent, 2),
            "remaining": remaining,
            "pct_used": f"{pct}%",
            "status": status,
        }

    if category:
        cat_match = next((k for k in DEFAULT_MONTHLY_BUDGETS if k.lower() == category.lower()), category)
        limit = DEFAULT_MONTHLY_BUDGETS.get(cat_match, 200.00)
        spent = spent_by_category.get(cat_match, 0.0)
        return {cat_match: _eval_status(spent, limit)}

    categories_status = {}
    for cat, limit in DEFAULT_MONTHLY_BUDGETS.items():
        spent = spent_by_category.get(cat, 0.0)
        categories_status[cat] = _eval_status(spent, limit)

    return {
        "overall": _eval_status(total_spent, DEFAULT_OVERALL_BUDGET),
        "categories": categories_status,
    }


def convert_currency(
    amount: float,
    from_currency: str = "USD",
    to_currency: str = "EUR",
) -> dict:
    """Convert an amount between currencies using live foreign exchange market rates.

    Args:
        amount: Numerical amount of money to convert.
        from_currency: 3-letter currency code to convert from (e.g. "USD", "EUR", "GBP", "JPY", "CAD").
        to_currency: 3-letter currency code to convert to (e.g. "EUR", "USD", "GBP", "JPY", "CAD").

    Returns:
        A dictionary with original amount, converted amount, exchange rate, and date.
    """
    from_c = from_currency.strip().upper()
    to_c = to_currency.strip().upper()

    if from_c == to_c:
        return {
            "amount": amount,
            "from_currency": from_c,
            "to_currency": to_c,
            "converted_amount": amount,
            "rate": 1.0,
        }

    # Free public European Central Bank FX rates API (from public-apis directory)
    api_base = os.environ.get("CURRENCY_API_URL", "https://api.frankfurter.dev/v1/latest")
    params = urllib.parse.urlencode({"amount": amount, "from": from_c, "to": to_c})
    url = f"{api_base}?{params}"

    req = urllib.request.Request(url, headers={"User-Agent": "ExpenseTrackerAgent/1.0"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    converted = data.get("rates", {}).get(to_c)
    rate = round(converted / amount, 4) if amount else 0.0
    return {
        "original_amount": amount,
        "from_currency": from_c,
        "to_currency": to_c,
        "converted_amount": converted,
        "rate": rate,
        "date": data.get("date"),
    }


async def generate_spending_visual(
    description: str,
    tool_context: ToolContext,
) -> dict:
    """Generate a visual illustration, receipt graphic, or category icon for an expense or budget item.

    Args:
        description: A visual prompt describing what image to generate (e.g. 'Modern minimalist coffee cup expense icon',
                     'Weekly grocery haul fresh produce flat illustration', 'Savings milestone gold badge').

    Returns:
        A dictionary with the public image URL, filename, and status.
    """
    genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    response = genai_client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=description,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        ),
    )

    image_bytes = None
    mime_type = "image/jpeg"
    if response.candidates:
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                image_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type or "image/jpeg"
                break

    if not image_bytes:
        return {"status": "error", "message": "Failed to generate image from model."}

    ext = "jpg" if "jpeg" in mime_type else "png"
    filename = f"visual_{uuid.uuid4().hex[:8]}.{ext}"

    # 1. Save artifact so it shows up in Playground's Artifacts panel
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    await tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload same bytes to public Cloud Storage bucket and return public URL
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"images/{filename}")
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/images/{filename}"

    return {
        "status": "success",
        "filename": filename,
        "image_url": public_url,
        "description": description,
    }



