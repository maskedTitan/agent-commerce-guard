# Product Requirements Document (PRD)
**Project:** Agentic Commerce "Delegated Auth" Protocol
**Status:** Draft

## 1. Problem Statement
AI Agents are becoming capable of executing complex shopping tasks. However, current payment flows fail for agents because:
1.  **Security:** Users cannot safely share raw credentials (password/CVV) with an autonomous script.
2.  **Bot Detection:** Payment gateways aggressively block non-human behavior, causing high decline rates for legitimate agent transactions.
3.  **Lack of Control:** Users fear "runaway spending" (e.g., an agent buying 100 items by mistake).

## 2. Proposed Solution
A "Delegated Authority" framework where PayPal issues a scoped, budget-limited token specifically for AI Agents. This allows agents to transact autonomously within strict guardrails defined by the user.

## 3. User Personas
*   **The "Power Shopper" (Primary):** Early adopter of AI tools. Wants to automate mundane tasks (grocery reordering, travel booking) but demands total control over spending limits.
*   **The Merchant (Secondary):** Wants to accept orders from AI agents but needs assurance that the transaction won't be charged back as "unauthorized."

## 4. User Stories
| ID | As a... | I want to... | So that... |
| :--- | :--- | :--- | :--- |
| **US.1** | User | Set a daily spending limit (e.g., $50) for my Agent | I don't wake up to an empty bank account. |
| **US.2** | User | Receive a push notification for "High Risk" attempts | I can manually approve or deny suspicious agent activity. |
| **US.3** | Agent | Receive a specific error code when a limit is reached | I can gracefully inform the user instead of crashing. |
| **US.4** | Risk System | Differentiate between "Agent" and "Human" traffic | We can adjust fraud rules without penalizing real humans. |

## 5. Functional Requirements
### A. The "Vault" API (Backend)
*   **Endpoint:** `POST /v1/agent/pay`
*   **Logic:** Must check `amount` against `daily_budget_remaining`.
*   **Logic:** Must check `merchant_id` against `blocked_merchants`.
*   **Output:** Return `STATUS: APPROVED`, `STATUS: DECLINED`, or `STATUS: PENDING_AUTH`.

### B. The "Command Center" (Frontend)
*   Dashboard must display real-time budget utilization.
*   "Approval Queue" for transactions flagged as `PENDING_AUTH`.

## 6. Success Metrics (KPIs)
*   **North Star:** "Agent TPV" (Total Payment Volume processed by Agents).
*   **Risk Metric:** Fraud Loss Rate (Target: < 5 basis points).
*   **UX Metric:** % of transactions completed without human intervention (Target: > 80%).

## 7. Corner Cases & Risks
*   **Scenario:** Agent gets stuck in a loop and tries to buy the same item 50 times in 1 minute.
    *   *Mitigation:* Implement Rate Limiting (max 5 transactions/hour).
*   **Scenario:** User approves a transaction, but the item goes out of stock.
    *   *Mitigation:* API must support "Auth & Capture" separation.