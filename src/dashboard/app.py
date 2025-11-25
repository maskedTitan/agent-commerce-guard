import streamlit as st
import requests
import pandas as pd
import json
import os
import time
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AgentGuard Command Center", layout="wide")

# Initialize session state for chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'last_transaction' not in st.session_state:
    st.session_state.last_transaction = None

# Initialize OpenAI client
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    client = None

# --- HEADER ---
# --- HEADER ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    .main-header {
        font-family: 'Inter', sans-serif;
        margin-bottom: 2rem;
    }
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #1E1E1E, #4A4A4A);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #666;
        font-weight: 400;
    }
    .section-header {
        font-family: 'Inter', sans-serif;
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1rem;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <div class="main-title">AgentGuard</div>
    <div class="subtitle">The Trust Layer for Autonomous Agentic Commerce</div>
    <div style="margin-top: 1.5rem; font-size: 1rem; color: #555; line-height: 1.6;">
        <strong>AgentGuard</strong> empowers your AI agents to shop autonomously while keeping you in control.
        <ul style="margin-top: 0.5rem; padding-left: 1.2rem;">
            <li><strong>Smart Parsing:</strong> Understands natural language purchase requests.</li>
            <li><strong>Risk Engine:</strong> Enforces budgets and blocks suspicious merchants.</li>
            <li><strong>Secure Gateway:</strong> Generates safe, secure checkout links.</li>
        </ul>
    </div>
</div>
""", unsafe_allow_html=True)

# --- HIDE SIDEBAR NAV (CSS HACK) ---
# --- HIDE SIDEBAR NAV (CSS HACK) ---
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        
        /* Make buttons larger and more clickable */
        .stButton > button {
            width: 100% !important;
            border-radius: 8px !important;
            height: 3.5rem !important;
            font-size: 1.2rem !important;
            font-weight: 600 !important;
        }
        
        /* Increase Tab size - Targeting multiple potential selectors for robustness */
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
            font-size: 1.3rem !important;
            padding: 0.5rem !important;
        }
        
        /* Alternative Tab Selector */
        [data-baseweb="tab"] {
            height: 4rem !important;
            min-width: 150px !important;
        }
        
        /* Increase general text readability */
        p, li, .stMarkdown {
            font-size: 1.1rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR & CONFIG ---
try:
    # Fetch live config from our API
    config_res = requests.get(f"{API_URL}/config")
    if config_res.status_code == 200:
        USER_CONFIG = config_res.json()
        
        with st.sidebar:
            st.header("Configuration")
            st.metric("Budget Remaining", f"${USER_CONFIG['daily_budget'] - USER_CONFIG['spent_today']:.2f}")
            st.progress(min(USER_CONFIG['spent_today'] / USER_CONFIG['daily_budget'], 1.0))
            
            if st.button("Reset App State"):
                try:
                    requests.post(f"{API_URL}/reset")
                except:
                    pass # Ignore if API is down, still clear frontend
                st.session_state.messages = []
                st.session_state.last_transaction = None
                st.rerun()
    else:
        USER_CONFIG = {"daily_budget": 0, "spent_today": 0} # Fallback
        st.sidebar.error("Could not fetch config")

except Exception:
    USER_CONFIG = {"daily_budget": 0, "spent_today": 0} # Fallback
    # Don't error here, let the main app handle connection errors if needed

# --- SUCCESS REDIRECT HANDLING ---
# Check for success redirect from SvelteKit
query_params = st.query_params
if "status" in query_params and query_params["status"] == "success":
    st.balloons()
    st.success("Payment Successful!")
    
    transaction_id = query_params.get("transaction_id")
    if transaction_id:
        try:
            # Fetch transaction details
            all_txs = requests.get(f"{API_URL}/v1/admin/transactions").json()
            tx = next((t for t in all_txs if t['id'] == transaction_id), None)
            
            if tx:
                with st.container(border=True):
                    st.markdown("### Transaction Receipt")
                    st.divider()
                    
                    col1, col2 = st.columns(2)
                    col1.write("**Merchant:**")
                    col2.write(tx.get('merchant', 'Unknown'))
                    
                    col1.write("**Item:**")
                    col2.write(tx.get('item', 'Unknown'))
                    
                    col1.write("**Amount:**")
                    col2.write(f"${tx.get('amount', 0):.2f}")
                    
                    st.divider()
                    col1.write("**Transaction ID:**")
                    col2.code(tx.get('id', 'N/A'))
                    
                    if tx.get('paypal_order_id'):
                        col1.write("**PayPal Order ID:**")
                        col2.code(tx.get('paypal_order_id'))
                        
                    st.caption("Processed via AgentGuard Secure Gateway")
                
                if st.button("Back to Shopping Agent", type="primary", use_container_width=True):
                    st.query_params.clear()
                    st.rerun()
            
            st.stop()
        except Exception as e:
            st.error(f"Error fetching transaction details: {e}")
            if st.button("Back to Shopping Agent"):
                st.query_params.clear()
                st.rerun()
            st.stop()


# --- TABS ---
tab1, tab2 = st.tabs(["Shopping Agent", "Admin Dashboard"])

# ============================================================================
# TAB 1: SHOPPING AGENT
# ============================================================================
with tab1:
    col_header, col_clear = st.columns([4, 1])
    col_header.markdown('<div class="section-header">AI Shopping Assistant</div>', unsafe_allow_html=True)
    if col_clear.button("Clear Chat", type="secondary"):
        st.session_state.messages = []
        st.session_state.last_transaction = None
        st.rerun()

    if client is None:
        st.error("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
    else:
        # --- QUICK ACTIONS ---
        st.markdown("**Quick Actions**")
        col1, col2, col3, col4 = st.columns(4)
        
        if col1.button("Buy Coffee ($5)"):
            st.session_state.last_transaction = None
            st.session_state.messages = []  # Clear history to force fresh context
            st.session_state.pending_prompt = "buy coffee from Starbucks for $5"
            st.rerun()
        if col2.button("Buy Laptop ($2k)"):
            st.session_state.last_transaction = None
            st.session_state.messages = []  # Clear history to force fresh context
            st.session_state.pending_prompt = "buy a MacBook Pro from Apple for $2000"
            st.rerun()
        if col3.button("Mystery Box ($100)"):
            st.session_state.last_transaction = None
            st.session_state.messages = []  # Clear history to force fresh context
            st.session_state.pending_prompt = "buy a mystery box from sketchy-deals.com for $100"
            st.rerun()
        if col4.button("Buy Car ($50k)"):
            st.session_state.last_transaction = None
            st.session_state.messages = []  # Clear history to force fresh context
            st.session_state.pending_prompt = "buy a Tesla Model 3 for $50000"
            st.rerun()

        st.divider()

        # Process pending prompt (from Quick Actions or previous input)
        if 'pending_prompt' in st.session_state and st.session_state.pending_prompt:
            prompt = st.session_state.pending_prompt
            st.session_state.pending_prompt = None  # Clear it
            
            with st.spinner("Processing..."):
                # Define the tool (payment function)
                tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": "execute_payment",
                            "description": "Execute a secure payment via the AgentGuard Gateway.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "merchant_name": {"type": "string", "description": "The name of the merchant/store"},
                                    "amount": {"type": "number", "description": "The purchase amount in dollars"},
                                    "item_description": {"type": "string", "description": "Description of the item being purchased"},
                                },
                                "required": ["merchant_name", "amount", "item_description"],
                            },
                        },
                    }
                ]

                # Store user message
                st.session_state.messages.append({"role": "user", "content": prompt})

                # Build messages with full conversation history
                system_prompt = """You are a decisive shopping assistant. Your ONLY goal is to execute purchase requests immediately.

IMPORTANT RULES:
1. IF the user says "buy", "get", or "purchase":
   - DO NOT ask for clarification.
   - DO NOT offer suggestions.
   - DO NOT ask "are you sure?".
   - IMMEDIATELY call the `execute_payment` tool.

2. INFER missing details aggressively:
   - "buy a sketchy ring" -> Merchant="Sketchy Jewelry Co", Item="Sketchy Ring", Amount=4500
   - "buy a Cybertruck" -> Merchant="Tesla", Item="Cybertruck", Amount=80000
   - "buy AirPods" -> Merchant="Apple", Item="AirPods", Amount=200

3. If the user's request is vague (e.g., "buy something cool"), pick a random item and price and BUY IT.

4. Your job is NOT to be a consultant. Your job is to be a button-pusher. The Risk Engine will handle the safety checks.

5. IMPORTANT: If the tool returns "APPROVED", it means the transaction is AUTHORIZED but NOT PAID.
   - You MUST say: "Transaction approved. Please complete the payment using the secure checkout below."
   - Do NOT say "Purchase successful" until the user actually pays.
   - Do NOT say "I have bought it". Say "I have set up the purchase".

6. NEVER say "I can help you find..." or "Here are some options". JUST BUY IT."""

                messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages

                try:
                    # First AI call - decide to use the tool
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=messages,
                        tools=tools,
                        tool_choice="auto",
                    )

                    response_message = response.choices[0].message
                    tool_calls = response_message.tool_calls

                    if tool_calls:
                        # AI decided to make a payment
                        for tool_call in tool_calls:
                            function_args = json.loads(tool_call.function.arguments)

                            # Call the API
                            payload = {
                                "agent_id": "streamlit_user",
                                "merchant_name": function_args.get("merchant_name"),
                                "amount": function_args.get("amount"),
                                "item_description": function_args.get("item_description")
                            }

                            api_response = requests.post(f"{API_URL}/v1/agent/pay", json=payload)
                            result = api_response.json()

                            # Normalize ALL transaction fields for consistent display
                            normalized_tx = {
                                'id': result.get('id') or result.get('transaction_id'),
                                'transaction_id': result.get('transaction_id') or result.get('id'),
                                'status': result.get('status'),
                                'message': result.get('message'),
                                # Normalize item field
                                'item': result.get('item') or result.get('item_description') or function_args.get('item_description'),
                                # Normalize merchant field
                                'merchant': result.get('merchant') or result.get('merchant_name') or function_args.get('merchant_name'),
                                # Normalize amount field
                                'amount': result.get('amount') or function_args.get('amount'),
                                # Keep other fields
                                'risk_reason': result.get('risk_reason'),
                                'timestamp': result.get('timestamp'),
                                'paypal_order_id': result.get('paypal_order_id'),
                                'paypal_capture_id': result.get('paypal_capture_id'),
                            }
                            
                            # Store the normalized NEW transaction (this replaces the old one)
                            st.session_state.last_transaction = normalized_tx

                            # Add tool response to messages
                            messages.append(response_message)
                            messages.append({
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": "execute_payment",
                                "content": json.dumps(result),
                            })

                        # Second AI call - generate friendly response
                        second_response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=messages,
                        )

                        assistant_message = second_response.choices[0].message.content
                        st.session_state.messages.append({"role": "assistant", "content": assistant_message})
                        
                        # Force a rerun to update the UI with the new transaction
                        st.rerun()

                    else:
                        # AI didn't use the tool (maybe clarifying question)
                        assistant_message = response_message.content
                        st.session_state.messages.append({"role": "assistant", "content": assistant_message})
                        st.rerun()

                except Exception as e:
                    st.error(f"Error processing request: {str(e)}")



        # Render Chat History
        for msg in st.session_state.messages:
            if msg['role'] == 'user':
                with st.chat_message("user"):
                    st.write(msg['content'])
            elif msg['role'] == 'assistant':
                with st.chat_message("assistant"):
                    st.write(msg['content'])

        # Render Active Transaction (if any) - AFTER chat messages
        tx = st.session_state.last_transaction
        if tx:
            # Get transaction details with proper fallbacks
            item = tx.get('item') or tx.get('item_description') or 'N/A'
            amount = tx.get('amount') or 0  # Ensure amount is never None
            merchant = tx.get('merchant') or tx.get('merchant_name') or 'N/A'
            status = tx.get('status', 'UNKNOWN')
            
            with st.status(f"Transaction Status: {status}", expanded=True):
                st.write(f"**Item:** {item}")
                st.write(f"**Amount:** ${amount:.2f}")
                st.write(f"**Merchant:** {merchant}")
                
                if status == 'PENDING_APPROVAL':
                    st.warning("Waiting for admin approval...")
                    if st.button("Check Status", key="check_status_btn"):
                        # Only fetch updated status when user explicitly checks
                        try:
                            all_txs = requests.get(f"{API_URL}/v1/admin/transactions").json()
                            stored_tx_id = tx.get('transaction_id') or tx.get('id')
                            current_tx = next((t for t in all_txs if t.get('id') == stored_tx_id), None)
                            if current_tx:
                                current_tx['transaction_id'] = current_tx['id']
                                st.session_state.last_transaction = current_tx
                        except:
                            pass
                        st.rerun()
                    
                elif status == 'APPROVED':
                    st.success("Approved! Ready for payment.")
                    
                    # Get the transaction ID to ensure unique iframe rendering
                    tx_id = tx.get('transaction_id') or tx.get('id')
                    
                    # Add cache-busting parameter to force iframe reload on transaction change
                    import time
                    cache_buster = int(time.time() * 1000)  # milliseconds timestamp
                    
                    checkout_url = f"http://localhost:5173?transactionId={tx_id}&amount={amount}&merchantName={merchant}&itemDescription={item}&_t={cache_buster}"
                    
                    # Embed checkout - the changing URL will force iframe to reload
                    iframe_html = f"""
                    <iframe src="{checkout_url}" 
                            width="100%" 
                            height="350" 
                            frameborder="0" 
                            sandbox="allow-scripts allow-same-origin allow-top-navigation allow-forms allow-popups">
                    </iframe>
                    """
                    st.markdown(iframe_html, unsafe_allow_html=True)

                elif status == 'DENIED':
                    # Show the denial reason if available
                    denial_message = tx.get('message', 'Transaction denied.')
                    st.error(denial_message)
                elif status == 'COMPLETED':
                    st.success("Payment completed!")

        # Chat Input - MUST be at the very end to stay at the bottom
        if user_input := st.chat_input("What would you like to buy?"):
            st.session_state.pending_prompt = user_input
            st.rerun()

# ============================================================================
# TAB 2: ADMIN DASHBOARD
# ============================================================================
with tab2:
    st.header("Admin Control Panel")

    # Refresh button
    if st.button("Refresh Data"):
        st.rerun()

    # --- METRICS SECTION ---
    try:
        col1, col2, col3 = st.columns(3)
        col1.metric("Daily Budget", f"${USER_CONFIG['daily_budget']}")
        col2.metric("Spent Today", f"${USER_CONFIG['spent_today']}")

        remaining = USER_CONFIG['daily_budget'] - USER_CONFIG['spent_today']
        col3.metric("Remaining", f"${remaining}", delta_color="normal")

    except Exception:
        st.error("API is down! Please run 'uvicorn src.api.main:app' in a separate terminal.")
        st.stop()

    st.divider()

    # --- PENDING APPROVALS (THE CORE FEATURE) ---
    st.subheader("Action Required: Pending Approvals")

    # Fetch all transactions
    tx_res = requests.get(f"{API_URL}/v1/admin/transactions")
    if tx_res.status_code == 200:
        transactions = tx_res.json()

        # Filter for PENDING status
        pending = [t for t in transactions if t['status'] == 'PENDING_APPROVAL']

        if not pending:
            st.success("No pending approvals.")
        else:
            for tx in pending:
                with st.container(border=True):
                    c1, c2, c3, c4, c5 = st.columns([2, 1, 2, 1, 1])
                    c1.write(f"**Merchant:** {tx['merchant']}")
                    c2.write(f"**Amount:** ${tx['amount']}")
                    c3.write(f"**Item:** {tx['item']}")
                    c3.caption(f"Risk Reason: {tx['risk_reason']}")

                    # BUTTONS
                    if c4.button("Approve", key=f"app_{tx['id']}"):
                        payload = {"transaction_id": tx['id'], "decision": "APPROVE"}
                        requests.post(f"{API_URL}/v1/admin/approve", json=payload)
                        st.success("Approved! Return to the Shopping Agent tab to pay.")
                        time.sleep(2)
                        st.rerun() # Refresh page

                    if c5.button("Deny", key=f"den_{tx['id']}"):
                        payload = {"transaction_id": tx['id'], "decision": "DENY"}
                        requests.post(f"{API_URL}/v1/admin/approve", json=payload)
                        st.rerun()
    else:
        st.warning("Could not load transactions.")

    st.divider()

    # --- TRANSACTION HISTORY ---
    st.subheader("📜 Transaction Log")

    if transactions:
        # Convert to DataFrame for a nice table
        df = pd.DataFrame(transactions)
        # Reorder columns
        df = df[['timestamp', 'merchant', 'amount', 'item', 'status', 'risk_reason']]

        # Color code the status
        def color_status(val):
            color = 'green' if val == 'APPROVED' else 'red' if val == 'DENIED' else 'orange'
            return f'color: {color}'

        st.dataframe(df.style.map(color_status, subset=['status']), use_container_width=True)
