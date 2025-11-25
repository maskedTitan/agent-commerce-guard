# Agentic Commerce Connector (POC)

### 🚀 Project Overview
**Domain:** FinTech / AI Agents
**Stack:** Python, FastAPI, Streamlit, OpenAI
**Status:** Proof of Concept

### 💡 The Problem
AI Agents (LLMs) are becoming autonomous shoppers, but they lack a secure "financial brain."
*   If an Agent tries to buy a $2,000 item, who stops it?
*   If an Agent buys from a scam site, how do we detect it?

### 🛠 The Solution
This project implements a **"Delegated Authority" Middleware** for AI Agents with a unified visual interface.

**Core Components:**
1.  **The Vault (API):** A risk engine that auto-denies transactions over budget or from blocked merchants
2.  **The Shopping Agent:** An intelligent OpenAI-powered assistant with natural language understanding and conversation memory
3.  **The Dashboard:** A unified Streamlit interface with two modes:
    - **Shopping Agent Tab:** Chat-based interface for making purchases
    - **Admin Dashboard Tab:** Human-in-the-loop approval system for suspicious transactions

### ✨ Key Features
- **Conversational AI**: Type natural language requests like "buy a Cybertruck" or "get me AirPods"
- **Product Knowledge**: Agent knows typical prices and merchants (e.g., Cybertruck → Tesla, ~$80k)
- **Conversation Memory**: Maintains context across multiple messages
- **Secure PayPal Checkout**: Integrated SvelteKit app for safe, sandboxed payment processing
- **Modern UI**: Sleek, accessible dashboard with "Command Center" aesthetic
- **Multi-Layer Security**:
  - Budget enforcement ($10,000 daily limit)
  - Amount thresholds (>$5,000 requires approval)
  - Risk keyword detection (item + merchant)
  - Merchant pattern matching (blocks scam/dark/suspicious sites)
- **Real-time Oversight**: Instant approval/denial from admin dashboard

### 🎥 Demo Flow
1.  User types: **"buy AirPods from a scammy website"** in the Shopping Agent tab
2.  API flags transaction as `PENDING_APPROVAL` (Suspicious merchant detected)
3.  Dashboard shows the pending transaction with risk details
4.  Human reviews and clicks **"Approve"** or **"Deny"**
5.  Transaction status updates in real-time

### 📦 How to Run

**1. Setup**
```bash
git clone https://github.com/YOUR_USERNAME/agent-commerce-guard
cd agent-commerce-guard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2. Configure Environment Variables**

Create a `.env` file in the project root (for local development):
```bash
cp .env.example .env
# Edit .env and add your keys:
# OPENAI_API_KEY=sk-proj-your-actual-key-here
# PAYPAL_CLIENT_ID=your-paypal-client-id
```

Or export directly (alternative method):
```bash
export OPENAI_API_KEY='sk-proj-your-actual-key-here'
export PAYPAL_CLIENT_ID='your-paypal-client-id'
```

**Note for Production:** Never use `.env` files in production. Use environment variables injected by your deployment platform (Docker, Kubernetes, AWS, etc.). See `.env.example` for details.

**3. Run the Services**

Open three terminal windows:

**Terminal 1 - Start the API (Risk Engine):**
```bash
cd agent-commerce-guard
source venv/bin/activate
uvicorn src.api.main:app --reload
# API runs at http://127.0.0.1:8000
```

**Terminal 2 - Start the Dashboard:**
```bash
cd agent-commerce-guard
source venv/bin/activate
streamlit run src/dashboard/app.py
# Dashboard opens at http://localhost:8501
```

**Terminal 3 - Start the Checkout App (SvelteKit):**
```bash
cd agent-commerce-guard/src/checkout
npm install
npm run dev
# Checkout app runs at http://localhost:5173
```

**4. Use the Application**

Open http://localhost:8501 in your browser. You'll see two tabs:

**🛒 Shopping Agent Tab** - Make purchases with natural language:
```
Try these examples:
- "buy a Cybertruck"
- "get me AirPods Pro"
- "purchase a MacBook Pro from Apple for $2500"
- "buy a mystery box from sketchy-deals.com for $50" (will trigger approval)
```

**⚙️ Admin Dashboard Tab** - Review and approve flagged transactions:
- View pending approvals with risk reasons
- Approve or deny transactions with one click
- See real-time budget status ($10,000 daily, $1,000 spent)
- Review complete transaction history

**5. Test the Security Features**

Try these prompts to see the risk engine in action:

| Prompt | Expected Result | Reason |
|--------|----------------|--------|
| "buy coffee from Starbucks for $5" | ✅ Auto-Approved | Safe transaction |
| "get me a Tesla Model 3" | ⏳ Pending Approval | Amount > $5,000 |
| "buy AirPods from scammy website" | ⏳ Pending Approval | Suspicious merchant |
| "purchase mystery crypto box for $100" | ⏳ Pending Approval | Risky keywords |
| "buy a yacht for $50,000" | ❌ Denied | Exceeds budget |

---

### 🏗️ Architecture

**Backend (FastAPI)**
- RESTful API with `/v1/agent/pay`, `/v1/admin/transactions`, `/v1/admin/approve` endpoints
- Multi-layer risk analysis engine
- In-memory transaction database (POC - use PostgreSQL for production)
- Configurable budget limits and approval thresholds

**AI Agent (OpenAI GPT-3.5-turbo)**
- Function calling for structured payment execution
- Product knowledge and price inference
- Conversation memory using session state
- Natural language understanding

**Frontend (Streamlit)**
- Dual-tab interface for shopping and administration
- Real-time transaction status updates
- Chat-based interaction with history
- Color-coded transaction logs
- **Modern UI** with custom CSS for accessibility

**Secure Checkout (SvelteKit)**
- Embedded iframe integration
- PayPal Orders API v2 implementation
- Sandboxed payment processing

### 🔒 Security Layers

**1. Blocked Merchants List**
- Hard deny for known fraudulent sites
- Configured in `USER_CONFIG["blocked_merchants"]`

**2. Budget Enforcement**
- Daily spending limit: $10,000
- Tracks cumulative spending
- Hard deny when budget exceeded

**3. Amount Threshold**
- Transactions ≥ $5,000 require human approval
- Configurable via `require_approval_over`

**4. Item Risk Keywords**
- Detects: crypto, gift card, casino, mystery, hacked, stolen
- Flags for human review

**5. Merchant Risk Keywords** ⭐ NEW
- Detects: scam, dark, hack, fraud, suspicious, fake, shady
- Pattern matching on merchant name
- Prevents social engineering attacks

### 📝 File Structure

```
agent-commerce-guard/
├── src/
│   ├── api/
│   │   └── main.py           # FastAPI risk engine
│   ├── agent/
│   │   └── shopper.py        # CLI agent (legacy - optional)
│   ├── dashboard/
│   │   └── app.py            # Unified Streamlit UI
│   └── checkout/             # SvelteKit PayPal App
│       ├── src/routes/
│       │   └── +page.svelte  # Checkout UI
│       └── package.json
├── product-docs/
│   ├── PRD.md                # Product requirements
│   └── RISK_ASSESSMENT.md    # Security threat model
├── .env.example              # Environment variable template
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

### 🚀 Future Enhancements

- [ ] Persistent database (PostgreSQL + SQLAlchemy)
- [ ] Rate limiting (max 5 transactions/hour)
- [ ] User authentication and multi-user support
- [ ] Transaction history export (CSV/JSON)
- [ ] Email/SMS notifications for pending approvals
- [ ] Machine learning-based fraud detection
- [x] Integration with real payment gateways (Stripe, PayPal)
- [ ] Webhook support for external systems

### 📄 License

This is a proof-of-concept project for educational purposes.