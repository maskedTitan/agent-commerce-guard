from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime
import os
import requests
import base64

app = FastAPI(title="AgentGuard Risk Engine")

# --- CORS CONFIGURATION ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8501", "http://127.0.0.1:5173", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    amount: Optional[float] = None

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

@app.post("/reset")
def reset_state():
    """Reset the backend state (budget and transactions)"""
    global transactions_db
    USER_CONFIG["spent_today"] = 0.0
    transactions_db = []
    return {"status": "State reset successfully"}

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
        message = "Transaction approved. Please complete payment."
        # Do NOT deduct money yet. Wait for capture.

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
        "message": message,
        "amount": req.amount
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
                # Do NOT deduct money yet. Wait for capture.
                return {"status": "updated", "new_status": "APPROVED"}
            else:
                tx["status"] = "DENIED"
                return {"status": "updated", "new_status": "DENIED"}
    
    raise HTTPException(status_code=404, detail="Transaction not found")

class CompletePaymentRequest(BaseModel):
    transaction_id: str
    paypal_order_id: str

@app.post("/v1/agent/complete_payment")
def complete_payment(req: CompletePaymentRequest):
    """
    Called by the Dashboard after a successful PayPal transaction.
    """
    for tx in transactions_db:
        if tx["id"] == req.transaction_id:
            if tx["status"] != "APPROVED":
                 raise HTTPException(status_code=400, detail="Transaction must be APPROVED before payment")
            
            tx["status"] = "COMPLETED"
            tx["paypal_order_id"] = req.paypal_order_id
            return {"status": "updated", "new_status": "COMPLETED"}
    
    raise HTTPException(status_code=404, detail="Transaction not found")

# --- PAYPAL INTEGRATION ---

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "ARlx7CgH_ptjjy-eWPu6ZBBox604ONYKDERdGzmyVdW0s3nMWRnf_gjI738desC3n6rNoKyn5ugnGb7c")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET", "EIAw_w9V0JD2IHO9U30Z8Ju0tNiizMi8c-4qgjY4iWXXwXtMdk_daq4hYdTSYo41IyZHK1ELDreNFYTA")
PAYPAL_API_BASE = "https://api-m.sandbox.paypal.com"

class CreatePayPalOrderRequest(BaseModel):
    transaction_id: str
    amount: float
    return_url: str

class CapturePayPalOrderRequest(BaseModel):
    order_id: str
    transaction_id: str

def get_paypal_access_token():
    """Get PayPal OAuth access token"""
    auth = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    response = requests.post(f"{PAYPAL_API_BASE}/v1/oauth2/token", headers=headers, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    raise HTTPException(status_code=500, detail="Failed to get PayPal access token")

@app.post("/v1/paypal/create-order")
def create_paypal_order(req: CreatePayPalOrderRequest):
    """
    Create a PayPal order and return the approval URL for redirect
    """
    # Verify transaction exists and is approved
    tx = next((t for t in transactions_db if t["id"] == req.transaction_id), None)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if tx["status"] != "APPROVED":
        raise HTTPException(status_code=400, detail="Transaction must be APPROVED before payment")
    
    access_token = get_paypal_access_token()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {
                "currency_code": "USD",
                "value": f"{req.amount:.2f}"
            },
            "description": tx.get("item_description", "Purchase")
        }],
        "payment_source": {
            "paypal": {
                "experience_context": {
                    "return_url": f"{req.return_url}?tx={req.transaction_id}",
                    "cancel_url": f"{req.return_url}?cancelled=true&tx={req.transaction_id}",
                    "user_action": "PAY_NOW",
                    "brand_name": "AgentGuard"
                }
            }
        }
    }
    
    response = requests.post(f"{PAYPAL_API_BASE}/v2/checkout/orders", json=payload, headers=headers)
    
    if response.status_code in [200, 201]:
        order_data = response.json()
        # Find the approval URL
        approval_url = next(
            (link["href"] for link in order_data.get("links", []) if link["rel"] == "payer-action"),
            None
        )
        return {
            "order_id": order_data["id"],
            "approval_url": approval_url,
            "status": "created"
        }
    else:
        raise HTTPException(status_code=500, detail=f"PayPal API error: {response.text}")

@app.post("/v1/paypal/capture-order")
def capture_paypal_order(req: CapturePayPalOrderRequest):
    """
    Capture a PayPal order after user approval
    """
    # Verify transaction exists
    tx = next((t for t in transactions_db if t["id"] == req.transaction_id), None)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    access_token = get_paypal_access_token()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.post(
        f"{PAYPAL_API_BASE}/v2/checkout/orders/{req.order_id}/capture",
        headers=headers
    )
    
    if response.status_code == 201:
        capture_data = response.json()
        # Update transaction status
        tx["status"] = "COMPLETED"
        tx["paypal_order_id"] = req.order_id
        tx["paypal_capture_id"] = capture_data.get("purchase_units", [{}])[0].get("payments", {}).get("captures", [{}])[0].get("id")
        
        # Deduct money NOW that we have the money
        USER_CONFIG["spent_today"] += tx["amount"]
        
        return {
            "status": "completed",
            "transaction_id": req.transaction_id,
            "paypal_order_id": req.order_id,
            "capture_data": capture_data
        }
    else:
        raise HTTPException(status_code=500, detail=f"PayPal capture failed: {response.text}")