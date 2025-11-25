import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Payment Success - AgentGuard", page_icon="🎉")

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# Get query parameters
query_params = st.query_params

if "token" in query_params and "tx" in query_params:
    paypal_order_id = query_params["token"]
    transaction_id = query_params["tx"]
    
    st.title("🎉 Payment Successful!")
    
    with st.spinner("Processing your payment..."):
        try:
            # Capture the payment
            capture_response = requests.post(f"{API_URL}/v1/paypal/capture-order", json={
                "order_id": paypal_order_id,
                "transaction_id": transaction_id
            })
            
            if capture_response.status_code == 200:
                data = capture_response.json()
                
                # Fetch transaction details
                try:
                    all_txs = requests.get(f"{API_URL}/v1/admin/transactions").json()
                    tx = next((t for t in all_txs if t['id'] == transaction_id), None)
                    
                    if tx:
                        st.success("Your payment has been processed successfully!")
                        
                        # Transaction Receipt
                        with st.container(border=True):
                            st.markdown("### 🧾 Transaction Receipt")
                            st.divider()
                            
                            col1, col2 = st.columns(2)
                            col1.write("**Merchant:**")
                            col2.write(tx.get('merchant_name', 'Unknown'))
                            
                            col1.write("**Item:**")
                            col2.write(tx.get('item_description', 'Unknown'))
                            
                            col1.write("**Amount:**")
                            col2.write(f"${tx.get('amount', 0):.2f}")
                            
                            st.divider()
                            col1.write("**Transaction ID:**")
                            col2.code(tx.get('id', 'N/A'))
                            
                            col1.write("**PayPal Order ID:**")
                            col2.code(paypal_order_id)
                            
                            st.caption("Processed via AgentGuard Secure Gateway")
                        
                        st.balloons()
                        
                        # Back to chat button
                        if st.button("🏠 Back to Shopping Agent", type="primary", use_container_width=True):
                            st.switch_page("app.py")
                    else:
                        st.warning("Payment captured, but transaction details not found.")
                        if st.button("🏠 Back to Shopping Agent", type="primary"):
                            st.switch_page("app.py")
                            
                except Exception as e:
                    st.warning(f"Payment captured successfully! (Transaction ID: {transaction_id})")
                    if st.button("🏠 Back to Shopping Agent", type="primary"):
                        st.switch_page("app.py")
            else:
                st.error(f"Payment capture failed: {capture_response.text}")
                if st.button("🏠 Back to Shopping Agent"):
                    st.switch_page("app.py")
                    
        except Exception as e:
            st.error(f"Error processing payment: {e}")
            if st.button("🏠 Back to Shopping Agent"):
                st.switch_page("app.py")

elif "cancelled" in query_params:
    st.title("❌ Payment Cancelled")
    st.warning("You cancelled the payment. No charges were made.")
    
    if st.button("🏠 Back to Shopping Agent", type="primary", use_container_width=True):
        st.switch_page("app.py")
else:
    st.title("⚠️ Invalid Request")
    st.error("No payment information found.")
    
    if st.button("🏠 Back to Shopping Agent", type="primary"):
        st.switch_page("app.py")
