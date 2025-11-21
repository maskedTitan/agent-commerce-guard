from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

app = FastAPI(title="AgentGuard Risk Engine")

# --- SIMULATED DATABASE (In-Memory) ---
# In a real app, this would be PostgreSQL
transactions_db = []

# User Configuration (The "Rules")
USER_CONFIG = {
    "daily_budget": 10000.00,  # $10,000 daily budget
    "spent_today": 1000.00,    # Already spent $1,000
    "require_approval_over": 5000.00,  # Anything > $5,000 needs human approval
    "blocked_merchants": ["sketchy-crypto.com", "unknown-seller.net"]
}

# --- DATA MODELS ---
class PaymentRequest(BaseModel):
    agent_id: str
    merchant_name: str
    amount: float
    item_description: str

class TransactionResponse(BaseModel):
    transaction_id: str
    status: str  # APPROVED, DENIED, PENDING_APPROVAL
    message: str

class ApprovalRequest(BaseModel):
    transaction_id: str
    decision: str # APPROVE or DENY

# --- ENDPOINTS ---

@app.get("/")
def read_root():
    return {"status": "Agent Gateway is Active"}

@app.get("/config")
def get_config():
    """Return current budget status for the Dashboard"""
    return USER_CONFIG

@app.post("/v1/agent/pay", response_model=TransactionResponse)
def process_payment(req: PaymentRequest):
    """
    The Core Logic: Decides if the Agent can pay.
    """
    tx_id = str(uuid.uuid4())[:8]
    
    # 1. Check Blocked Merchants (Compliance Rule)
    if req.merchant_name in USER_CONFIG["blocked_merchants"]:
        return {
            "transaction_id": tx_id, 
            "status": "DENIED", 
            "message": "Merchant is on the Blocklist"
        }

    # 2. Check Budget (Financial Health Rule)
    remaining_budget = USER_CONFIG["daily_budget"] - USER_CONFIG["spent_today"]
    if req.amount > remaining_budget:
        return {
            "transaction_id": tx_id, 
            "status": "DENIED", 
            "message": f"Exceeds daily budget. Remaining: ${remaining_budget}"
        }

    # 3. Risk Analysis (The 'Brain')
    # Logic: Check amount, item, AND merchant for suspicious patterns
    requires_approval = False
    risk_reason = ""

    if req.amount > USER_CONFIG["require_approval_over"]:
        requires_approval = True
        risk_reason = "Amount exceeds auto-approval limit"

    # Check for suspicious ITEM keywords
    suspicious_item_keywords = ["crypto", "gift card", "casino", "mystery", "hacked", "stolen"]
    if any(word in req.item_description.lower() for word in suspicious_item_keywords):
        requires_approval = True
        risk_reason = "High-risk item category detected"

    # Check for suspicious MERCHANT keywords (SECURITY FIX)
    suspicious_merchant_keywords = [
        "scam", "scammy", "sketchy", "dark", "darkweb", "hack", "illegal",
        "fraud", "suspicious", "unknown", "untrusted", "shady", "fake"
    ]
    if any(word in req.merchant_name.lower() for word in suspicious_merchant_keywords):
        requires_approval = True
        risk_reason = "Suspicious merchant detected"

    # 4. Final Decision
    if requires_approval:
        status = "PENDING_APPROVAL"
        message = f"Risk Triggered: {risk_reason}. Waiting for user."
    else:
        status = "APPROVED"
        message = "Transaction successful."
        USER_CONFIG["spent_today"] += req.amount # Update spent amount

    # Save to DB
    tx_record = {
        "id": tx_id,
        "timestamp": datetime.now().isoformat(),
        "merchant": req.merchant_name,
        "amount": req.amount,
        "item": req.item_description,
        "status": status,
        "risk_reason": risk_reason
    }
    transactions_db.append(tx_record)

    return {
        "transaction_id": tx_id,
        "status": status,
        "message": message
    }

@app.get("/v1/admin/transactions")
def get_transactions():
    """Used by the Dashboard to show history"""
    return transactions_db

@app.post("/v1/admin/approve")
def approve_transaction(req: ApprovalRequest):
    """
    Human-in-the-Loop Endpoint.
    The Dashboard calls this when the user clicks 'Approve'.
    """
    for tx in transactions_db:
        if tx["id"] == req.transaction_id:
            if req.decision == "APPROVE":
                tx["status"] = "APPROVED"
                # Deduct money now that it's approved
                USER_CONFIG["spent_today"] += tx["amount"]
                return {"status": "updated", "new_status": "APPROVED"}
            else:
                tx["status"] = "DENIED"
                return {"status": "updated", "new_status": "DENIED"}
    
    raise HTTPException(status_code=404, detail="Transaction not found")