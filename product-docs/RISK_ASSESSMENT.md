# Risk & Compliance Assessment

## 1. Threat Model: "The Rogue Agent"
**Risk:** An AI Agent is prompt-injected (hacked) by a malicious website to drain the user's wallet.
**Impact:** Critical (Financial Loss).
**Control:** 
*   **Hard Limits:** Daily budget caps are immutable by the agent.
*   **Merchant Whitelisting:** Users can restrict agents to specific domains (e.g., "Only allow Amazon and Walmart").

## 2. Regulatory Compliance (KYC/AML)
**Risk:** Agents being used for money laundering (structuring payments to avoid detection).
**Control:** 
*   All Agent tokens are tied to a fully KYC'd (Know Your Customer) human identity.
*   Agents inherit the risk profile of the parent account.

## 3. Privacy
**Risk:** Agent sharing personal data (shipping address) with untrusted API endpoints.
**Control:** 
*   The Connector acts as a proxy. The Agent sends the request to PayPal, and PayPal injects the shipping info directly to the merchant (Agent never sees the raw address data).

## 4. Iframe Security
**Risk:** Clickjacking or malicious redirection within the embedded checkout.
**Control:**
*   **Sandboxing:** The checkout iframe uses the `sandbox` attribute to restrict scripts and top-level navigation.
*   **CORS Policy:** Strict Cross-Origin Resource Sharing (CORS) policies prevent unauthorized domains from interacting with the checkout flow.
*   **Token Scoping:** PayPal tokens are generated server-side and are scoped only for the specific transaction amount and merchant.