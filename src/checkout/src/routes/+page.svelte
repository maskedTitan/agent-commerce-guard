<script>
    // @ts-nocheck
    import { onMount } from "svelte";
    import { loadScript } from "@paypal/paypal-js";

    let paid = false;
    let error = null;
    let transactionId = "";
    let amount = "";
    let merchantName = "";
    let itemDescription = "";

    onMount(async () => {
        const params = new URLSearchParams(window.location.search);
        transactionId = params.get("transactionId");
        amount = params.get("amount");
        merchantName = params.get("merchantName");
        itemDescription = params.get("itemDescription");

        if (!transactionId || !amount) {
            error = "Missing transaction details";
            return;
        }

        try {
            const paypal = await loadScript({
                clientId:
                    import.meta.env.VITE_PAYPAL_CLIENT_ID ||
                    "ARlx7CgH_ptjjy-eWPu6ZBBox604ONYKDERdGzmyVdW0s3nMWRnf_gjI738desC3n6rNoKyn5ugnGb7c",
                currency: "USD",
            });

            if (paypal) {
                await paypal
                    .Buttons({
                        createOrder: async (data, actions) => {
                            // Call backend to create order
                            const response = await fetch(
                                "http://127.0.0.1:8000/v1/paypal/create-order",
                                {
                                    method: "POST",
                                    headers: {
                                        "Content-Type": "application/json",
                                    },
                                    body: JSON.stringify({
                                        transaction_id: transactionId,
                                        amount: parseFloat(amount),
                                        return_url: window.location.href, // Not used for popup flow but required by API
                                    }),
                                },
                            );

                            if (!response.ok) {
                                const err = await response.json();
                                throw new Error(
                                    err.detail || "Failed to create order",
                                );
                            }

                            const orderData = await response.json();
                            return orderData.order_id;
                        },
                        onApprove: async (data, actions) => {
                            // Call backend to capture order
                            const response = await fetch(
                                "http://127.0.0.1:8000/v1/paypal/capture-order",
                                {
                                    method: "POST",
                                    headers: {
                                        "Content-Type": "application/json",
                                    },
                                    body: JSON.stringify({
                                        order_id: data.orderID,
                                        transaction_id: transactionId,
                                    }),
                                },
                            );

                            if (!response.ok) {
                                const err = await response.json();
                                throw new Error(
                                    err.detail || "Failed to capture order",
                                );
                            }

                            // Redirect parent window to success page
                            window.top.location.href = `http://localhost:8501/?status=success&transaction_id=${transactionId}`;
                        },
                        onError: (err) => {
                            error = err.message;
                        },
                    })
                    .render("#paypal-button-container");
            }
        } catch (err) {
            error = err.message;
        }
    });
</script>

<main class="container">
    {#if error}
        <div class="error-state">
            <h2>Payment Error</h2>
            <p>{error}</p>
        </div>
    {:else if paid}
        <div class="success-state">
            <div class="success-icon">✓</div>
            <h1>Payment Complete</h1>
            <p class="redirect-text">Redirecting...</p>
        </div>
    {:else}
        <div class="checkout-card">
            <div class="checkout-header">
                <div class="lock-icon">🔒</div>
                <h1>Secure Checkout</h1>
            </div>

            <div class="amount-display">
                <div class="amount-label">Total</div>
                <div class="amount-value">${amount}</div>
            </div>

            <div class="transaction-details">
                <div class="detail-row">
                    <span class="detail-label">Merchant</span>
                    <span class="detail-value">{merchantName}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Item</span>
                    <span class="detail-value">{itemDescription}</span>
                </div>
            </div>

            <div id="paypal-button-container"></div>

            <div class="security-note">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <path
                        d="M6 0L1 2V6C1 8.76 3.24 11 6 11C8.76 11 11 8.76 11 6V2L6 0Z"
                        fill="#6b7280"
                    />
                </svg>
                Secured by PayPal
            </div>
        </div>
    {/if}
</main>

<style>
    :global(body) {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
            Helvetica, Arial, sans-serif;
        background: #f9fafb;
        margin: 0;
        padding: 0;
        min-height: 100vh;
    }

    .container {
        padding: 12px;
        max-width: 480px;
        margin: 0 auto;
    }

    .checkout-card {
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
        overflow: hidden;
    }

    .checkout-header {
        text-align: center;
        padding: 12px 16px 10px;
        background: linear-gradient(to bottom, #ffffff, #f9fafb);
        border-bottom: 1px solid #e5e7eb;
    }

    .lock-icon {
        font-size: 16px;
        margin-bottom: 4px;
    }

    .checkout-header h1 {
        margin: 0;
        font-size: 1rem;
        font-weight: 600;
        color: #111827;
    }

    .amount-display {
        text-align: center;
        padding: 16px 16px;
        background: #f9fafb;
    }

    .amount-label {
        font-size: 0.75rem;
        color: #6b7280;
        margin-bottom: 2px;
        font-weight: 500;
    }

    .amount-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #111827;
        letter-spacing: -0.02em;
    }

    .transaction-details {
        padding: 12px 16px;
        background: white;
    }

    .detail-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid #f3f4f6;
    }

    .detail-row:last-child {
        border-bottom: none;
    }

    .detail-label {
        font-size: 0.8125rem;
        color: #6b7280;
        font-weight: 500;
    }

    .detail-value {
        font-size: 0.8125rem;
        color: #111827;
        font-weight: 600;
        text-align: right;
        max-width: 60%;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    #paypal-button-container {
        padding: 12px 16px 16px;
        background: white;
    }

    .security-note {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 5px;
        padding: 10px;
        font-size: 0.6875rem;
        color: #6b7280;
        background: #f9fafb;
        border-top: 1px solid #e5e7eb;
    }

    /* Success State */
    .success-state {
        text-align: center;
        padding: 32px 16px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
    }

    .success-icon {
        width: 50px;
        height: 50px;
        margin: 0 auto 12px;
        background: #10b981;
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        font-weight: bold;
    }

    .success-state h1 {
        margin: 0 0 6px;
        font-size: 1.25rem;
        color: #111827;
    }

    .redirect-text {
        color: #6b7280;
        font-size: 0.8125rem;
    }

    /* Error State */
    .error-state {
        text-align: center;
        padding: 32px 16px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
    }

    .error-state h2 {
        color: #dc2626;
        margin: 0 0 6px;
        font-size: 1.125rem;
    }

    .error-state p {
        color: #6b7280;
        font-size: 0.875rem;
    }
</style>
