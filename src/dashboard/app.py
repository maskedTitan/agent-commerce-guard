import streamlit as st
import requests
import pandas as pd
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AgentGuard Command Center", page_icon="🛡️", layout="wide")

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
st.title("🛡️ AgentGuard Command Center")
st.markdown("The Trust Layer for Autonomous Agentic Commerce.")
st.divider()

# --- TABS ---
tab1, tab2 = st.tabs(["🛒 Shopping Agent", "⚙️ Admin Dashboard"])

# ============================================================================
# TAB 1: SHOPPING AGENT
# ============================================================================
with tab1:
    col_header, col_clear = st.columns([4, 1])
    col_header.header("🤖 AI Shopping Assistant")
    if col_clear.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.last_transaction = None
        st.rerun()

    st.markdown("Tell me what you want to buy and I'll process it through the AgentGuard gateway.")
    st.caption("💡 Tip: Just say 'buy a Cybertruck' or 'get me AirPods' - I'll figure out the details!")

    if client is None:
        st.error("⚠️ OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
    else:
        # Chat history display
        if st.session_state.messages:
            st.subheader("💬 Conversation History")
            for msg in st.session_state.messages:
                if msg['role'] == 'user':
                    with st.chat_message("user"):
                        st.write(msg['content'])
                elif msg['role'] == 'assistant':
                    with st.chat_message("assistant"):
                        st.write(msg['content'])

        # Transaction result display
        if st.session_state.last_transaction:
            tx = st.session_state.last_transaction
            st.subheader("📋 Last Transaction")

            status_emoji = {
                'APPROVED': '✅',
                'DENIED': '❌',
                'PENDING_APPROVAL': '⏳'
            }

            status_color = {
                'APPROVED': 'green',
                'DENIED': 'red',
                'PENDING_APPROVAL': 'orange'
            }

            status = tx.get('status', 'UNKNOWN')
            with st.container(border=True):
                col1, col2 = st.columns(2)
                col1.metric("Status", f"{status_emoji.get(status, '❓')} {status}")
                col2.metric("Transaction ID", tx.get('transaction_id', 'N/A'))

                st.write(f"**Message:** {tx.get('message', 'No message')}")

                if status == 'PENDING_APPROVAL':
                    st.warning("⚠️ This transaction requires approval. Check the Admin Dashboard tab!")
                elif status == 'APPROVED':
                    st.success("✅ Transaction approved and processed!")
                elif status == 'DENIED':
                    st.error("❌ Transaction was denied by the risk engine.")

        st.divider()

        # Input form
        with st.form(key='purchase_form', clear_on_submit=True):
            st.subheader("🛍️ New Purchase Request")
            user_prompt = st.text_area(
                "What would you like to buy?",
                placeholder="Example: Buy a laptop from BestBuy for $1200\nExample: Purchase a coffee from Starbucks for $5.50",
                height=100
            )
            submit_button = st.form_submit_button("🚀 Submit Purchase Request")

        if submit_button and user_prompt:
            with st.spinner("🤖 Agent is processing your request..."):
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

                # Store user message first
                st.session_state.messages.append({"role": "user", "content": user_prompt})

                # Build messages with full conversation history
                system_prompt = """You are an intelligent shopping assistant with knowledge of products, brands, and typical prices.

IMPORTANT INSTRUCTIONS:
1. Use your knowledge to infer missing details:
   - If user says "buy a Cybertruck", you know: merchant=Tesla, item=Cybertruck, typical price=$60,000-$100,000
   - If user says "buy an iPhone 15", you know: merchant=Apple, item=iPhone 15, typical price=$799-$1,199
   - If user says "buy AirPods", you know: merchant=Apple, item=AirPods, typical price=$129-$249

2. Use the conversation history to remember previous context. If the user provided information in earlier messages, use it.

3. Only ask for clarification if you genuinely don't have enough information after using your knowledge and conversation history.

4. When you have enough information (merchant, amount, item), immediately call the execute_payment tool.

5. Use reasonable default prices based on your knowledge. If the user mentions a product without a price, use the typical market price.

Your goal is to be helpful and smart, not to ask unnecessary questions."""

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

                            # Store the transaction
                            st.session_state.last_transaction = result

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

                    else:
                        # AI didn't use the tool (maybe clarifying question)
                        assistant_message = response_message.content
                        st.session_state.messages.append({"role": "assistant", "content": assistant_message})

                    st.rerun()

                except Exception as e:
                    st.error(f"Error processing request: {str(e)}")

# ============================================================================
# TAB 2: ADMIN DASHBOARD
# ============================================================================
with tab2:
    st.header("⚙️ Admin Control Panel")

    # Refresh button
    if st.button("🔄 Refresh Data"):
        st.rerun()

    # --- METRICS SECTION ---
    try:
        # Fetch live config from our API
        config_res = requests.get(f"{API_URL}/config")
        if config_res.status_code == 200:
            data = config_res.json()

            col1, col2, col3 = st.columns(3)
            col1.metric("Daily Budget", f"${data['daily_budget']}")
            col2.metric("Spent Today", f"${data['spent_today']}")

            remaining = data['daily_budget'] - data['spent_today']
            col3.metric("Remaining", f"${remaining}", delta_color="normal")
        else:
            st.error("Could not fetch budget data.")

    except requests.exceptions.ConnectionError:
        st.error("⚠️ API is down! Please run 'uvicorn src.api.main:app' in a separate terminal.")
        st.stop()

    st.divider()

    # --- PENDING APPROVALS (THE CORE FEATURE) ---
    st.subheader("🚨 Action Required: Pending Approvals")

    # Fetch all transactions
    tx_res = requests.get(f"{API_URL}/v1/admin/transactions")
    if tx_res.status_code == 200:
        transactions = tx_res.json()

        # Filter for PENDING status
        pending = [t for t in transactions if t['status'] == 'PENDING_APPROVAL']

        if not pending:
            st.success("No pending approvals. Your Agent is behaving nicely! ✅")
        else:
            for tx in pending:
                with st.container(border=True):
                    c1, c2, c3, c4, c5 = st.columns([2, 1, 2, 1, 1])
                    c1.write(f"**Merchant:** {tx['merchant']}")
                    c2.write(f"**Amount:** ${tx['amount']}")
                    c3.write(f"**Item:** {tx['item']}")
                    c3.caption(f"⚠️ Risk Reason: {tx['risk_reason']}")

                    # BUTTONS
                    if c4.button("✅ Approve", key=f"app_{tx['id']}"):
                        payload = {"transaction_id": tx['id'], "decision": "APPROVE"}
                        requests.post(f"{API_URL}/v1/admin/approve", json=payload)
                        st.rerun() # Refresh page

                    if c5.button("❌ Deny", key=f"den_{tx['id']}"):
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
