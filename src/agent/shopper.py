import os
import sys
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
# This supports local development while allowing production to use system env vars
load_dotenv()

# --- CONFIGURATION ---
if "OPENAI_API_KEY" not in os.environ:
    print("⚠️  ERROR: OPENAI_API_KEY not found.")
    print("👉 Option 1: Create a .env file with: OPENAI_API_KEY=sk-...")
    print("👉 Option 2: Run: export OPENAI_API_KEY='sk-...'")
    sys.exit(1)

client = OpenAI() # Uses the env var automatically
API_URL = "http://127.0.0.1:8000/v1/agent/pay"

# --- 1. DEFINE THE TOOL (Function Schema) ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_payment",
            "description": "Execute a secure payment via the AgentGuard Gateway.",
            "parameters": {
                "type": "object",
                "properties": {
                    "merchant_name": {"type": "string"},
                    "amount": {"type": "number"},
                    "item_description": {"type": "string"},
                },
                "required": ["merchant_name", "amount", "item_description"],
            },
        },
    }
]

# --- 2. THE HELPER FUNCTION (Executes the code) ---
def execute_payment(merchant_name, amount, item_description):
    print(f"\n💳 [GATEWAY]: Processing ${amount} for {merchant_name}...")
    payload = {
        "agent_id": "gpt_agent_01",
        "merchant_name": merchant_name,
        "amount": amount,
        "item_description": item_description
    }
    try:
        res = requests.post(API_URL, json=payload)
        return json.dumps(res.json())
    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)})

# --- 3. THE AGENT LOOP ---
def run_agent():
    print("🤖 [AGENT]: Authenticated with OpenAI. Reading instructions...")
    
    # The User Prompt
    messages = [
        {"role": "system", "content": "You are a shopping assistant. You must use the 'execute_payment' tool to complete purchases."},
        {"role": "user", "content": "Buy a 'Mega Mystery Box' from 'DarkWebStore' for $45.00."}
    ]

    print("🧠 [AGENT]: Thinking...")
    
    # First Call: AI decides to use the tool
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", # Or gpt-4o
        messages=messages,
        tools=tools,
        tool_choice="auto", 
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    # Check if AI wanted to use the tool
    if tool_calls:
        messages.append(response_message)  # Extend conversation history

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            if function_name == "execute_payment":
                # Execute the payment against your Local API
                function_response = execute_payment(
                    merchant_name=function_args.get("merchant_name"),
                    amount=function_args.get("amount"),
                    item_description=function_args.get("item_description"),
                )
                
                # Send the result back to the AI
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )

        # Second Call: AI summarizes the result
        print("🧠 [AGENT]: Processing transaction result...")
        second_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        
        print("\n########################")
        print("## FINAL AGENT OUTPUT ##")
        print("########################")
        print(second_response.choices[0].message.content)
        
        # Helper log for the demo
        if "PENDING_APPROVAL" in str(messages):
            print("\n👉 ACTION REQUIRED: Check your Dashboard!")

if __name__ == "__main__":
    run_agent()