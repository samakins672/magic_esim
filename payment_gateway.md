# Payment Gateway Integration Guide

This document explains how payment gateways are wired into the Magic eSIM codebase and provides a step-by-step checklist for adding or maintaining a gateway across the backend API and frontend checkout flow.

## 1. Current Architecture Overview

The payment flow is coordinated by a combination of Django backend services and template-driven frontend interactions:

* **Data model** – Payments are persisted through `billing.models.Payment`, which stores the gateway identifier, checkout URL, on-chain address (for crypto providers), transaction identifiers, and status timestamps.【F:billing/models.py†L5-L43】
* **Serializer** – `billing.serializers.PaymentSerializer` controls which fields can be written by clients and which are populated by gateway logic, preventing users from overriding gateway-managed attributes.【F:billing/serializers.py†L1-L15】
* **API views** – `billing.views.PaymentListCreateView`, `PaymentStatusCheckView`, and `UpdatePendingPaymentsView` encapsulate gateway-specific branching for charge creation, callback polling, and scheduled status refreshes.【F:billing/views.py†L1-L197】
* **Gateway helpers** – Concrete integrations (e.g., CoinPayments and HyperPay MPGS) live in `billing/utils.py` where reusable request helpers and status utilities reside.【F:billing/utils.py†L1-L183】【F:billing/utils.py†L200-L289】
* **Configuration** – Environment-driven credentials are declared in `magic_esim/settings.py` and loaded from deployment secrets (see section 3.1).【F:magic_esim/settings.py†L239-L274】
* **Checkout UI** – The customer-facing payment selection is rendered in `templates/checkout.html`, with submission handled via `static/backend/checkout.js` which posts the gateway choice to the API and redirects the user to the provider checkout link.【F:templates/checkout.html†L209-L276】【F:static/backend/checkout.js†L1-L126】【F:static/backend/checkout.js†L142-L210】

Understanding these touchpoints is key before extending the system with an additional provider.

## 2. Adding a New Payment Gateway (Backend API)

### 2.1 Prepare configuration
1. **Gather credentials** – Determine the secret keys, merchant IDs, webhook URLs, or other settings the provider requires.
2. **Declare settings** – Add new entries under the payment configuration block in `magic_esim/settings.py`, following the existing CoinPayments and HyperPay MPGS variables. Always use `config('KEY')` so that secrets remain externalized.【F:magic_esim/settings.py†L239-L274】
3. **Update deployment secrets** – Ensure the `.env` files used for local development, staging, and production expose the new keys. Document required values for DevOps.

### 2.2 Implement gateway helper
1. **Create a helper module** – Extend `billing/utils.py` with a dedicated class or function encapsulating API calls (authentication, charge creation, status lookup, refunds, etc.). Mirror the structure used by `CoinPayments` and `create_mpgs_checkout` to keep logic centralized and testable.【F:billing/utils.py†L1-L183】【F:billing/utils.py†L200-L289】
2. **Normalize responses** – Return dictionaries with consistent fields (`status`, `message`, `payment_id`, `checkout_url`, `timeout`, etc.) so the view logic can remain uniform.
3. **Handle errors explicitly** – Raise `requests.RequestException` or return structured error states that the serializer can surface as validation errors.

### 2.3 Branch inside API views
1. **Charge creation** – Add a new `elif` block inside `PaymentListCreateView.perform_create` keyed on `payment.payment_gateway`. Use your helper to create the transaction, populate `Payment` fields (`payment_url`, `gateway_transaction_id`, `expiry_datetime`, etc.), and set `status='PENDING'` when creation succeeds.【F:billing/views.py†L31-L123】
2. **Status polling** – Extend `PaymentStatusCheckView.get` to look up transactions for your gateway. Map provider status codes into the canonical `PENDING`, `COMPLETED`, and `FAILED` states, and set `date_paid` when a payment is confirmed.【F:billing/views.py†L124-L197】
3. **Bulk updates** – Update `UpdatePendingPaymentsView` so the scheduled refresh job is aware of the new gateway when iterating through pending payments.【F:billing/views.py†L198-L266】
4. **Serializer defaults** – If the new gateway requires different default currencies or payment methods, adjust defaults on the `Payment` model or override values in the view before saving.

### 2.4 Webhooks (optional but recommended)
* If the provider supports webhooks/IPNs, create a dedicated Django view to receive callbacks, verify signatures, and update the `Payment` instance. Reuse the `CoinPayments` IPN pattern (`COINPAYMENTS_IPN_URL`) as guidance.【F:billing/views.py†L31-L123】

### 2.5 Testing
* Add unit tests in `billing/tests.py` covering charge creation success/failure paths and status mapping.
* Where possible, use the provider’s sandbox and record fixtures for deterministic tests.

## 3. Adding a New Payment Gateway (Frontend)

### 3.1 Expose the gateway in the checkout template
1. **Radio button** – Insert a new `.onePaymentOption` block in `templates/checkout.html` with a unique `id` and `value` matching the backend gateway string. Provide an accessible label and icon or badge for visual parity.【F:templates/checkout.html†L209-L276】
2. **Availability cues** – If the gateway is region-specific or not generally available, use the `disabled` attribute or tooltips to set expectations (see the Stripe example in the template for styling).【F:templates/checkout.html†L257-L276】

### 3.2 Update checkout JavaScript
1. **Form submission** – Ensure the new gateway is supported wherever the selected value is read. The existing script reads the radio value dynamically, so no change is required unless conditional front-end logic is needed.【F:static/backend/checkout.js†L162-L210】
2. **Plan pre-processing** – If the gateway mandates a currency or pricing adjustment, modify the plan loading logic to set `#paymentForm [name="currency"]` and `#paymentForm [name="price"]` appropriately before submission.【F:static/backend/checkout.js†L49-L123】【F:static/backend/checkout.js†L129-L210】
3. **Post-submit handling** – Confirm that the backend response returns a `payment_url`. The script opens the checkout link in a new tab and redirects the current window to `/orders`; adapt this behavior if the new provider requires an embedded flow.【F:static/backend/checkout.js†L173-L205】

### 3.3 Static assets
* Add the provider logo to `static/new/assets/misc/` and reference it in the template.
* If the gateway exposes additional UI (modals, inline forms), encapsulate new scripts in `static/backend/` and include them after `checkout.js`.

## 4. Managing Gateways in Production

### 4.1 Monitoring payment health
* **Manual status checks** – Use `PaymentStatusCheckView` by visiting `/api/payments/status/<ref_id>/` for both CoinPayments and HyperPay MPGS transactions to force a refresh when investigating support tickets.【F:billing/views.py†L124-L197】
* **Automated sweeps** – Schedule regular calls to `/api/payments/update-pending/` to reconcile pending payments created within the last 48 hours. This view normalizes statuses across gateways and timestamps successful payments.【F:billing/views.py†L198-L266】

### 4.2 Timeout and expiry handling
* Persisted `expiry_datetime` values drive customer messaging about when payment links expire. Always record the timeout provided by the gateway (see `create_mpgs_checkout` and the CoinPayments response mapping).【F:billing/views.py†L45-L123】【F:billing/utils.py†L200-L289】
* When adding gateways without a natural expiry, either set `expiry_datetime=None` or calculate a sensible deadline to keep the UI consistent.

### 4.3 Refunds and cancellations
* Implement provider-specific refund helpers in `billing/utils.py` as needed and expose staff-only administrative endpoints for issuing refunds.
* Update `Payment.status` to `'FAILED'` for provider-cancelled transactions so the order history reflects the final state.【F:billing/models.py†L11-L43】

## 5. Notes on Existing Gateways

### 5.1 CoinPayments
* **Currency pairing** – Charges are initiated with `currency1` set to the customer’s selected currency (defaults to USD) and `currency2='BTC'`. Developers integrating altcoins should update the `Payment` currency before invoking the API and adjust `currency2` accordingly.【F:billing/views.py†L45-L80】
* **Credentials** – Requires `COINPAYMENTS_PUBLIC_KEY`, `COINPAYMENTS_PRIVATE_KEY`, and `COINPAYMENTS_IPN_URL`. Ensure the IPN route is exposed publicly so CoinPayments can push status updates.【F:magic_esim/settings.py†L239-L256】
* **Status mapping** – CoinPayments returns descriptive strings (`Waiting for buyer funds...`, `Cancelled / Timed Out`, etc.) that are translated into platform statuses inside the views. Preserve these mappings when refactoring to avoid misreporting payment success.【F:billing/views.py†L131-L197】

### 5.2 HyperPay MPGS
* **Regional endpoints** – HyperPay provisions MPGS merchants in regional clusters. For GCC/UAE tenants the sandbox and production APIs are served from `https://test.oppwa.com` (`https://oppwa.com` in production). EU-registered tenants instead use the `eu-test.oppwa.com` (`eu-prod.oppwa.com`) cluster, so update `MPGS_API_BASE_URL` and `MPGS_CHECKOUT_URL` accordingly when deploying.【F:.env.example†L31-L36】
* **Checkout sessions** – Hosted checkout links are generated via the MPGS REST API and require Basic authentication using `merchant.<ID>` credentials. The helper returns a session ID along with a prebuilt redirect URL and calculated expiry timestamp.【F:billing/utils.py†L200-L289】
* **Status polling** – Order status codes such as `CAPTURED`, `APPROVED`, or `PENDING` are normalized within the API views so they map cleanly onto the platform’s canonical states.【F:billing/views.py†L84-L197】
* **Redirect flow** – Customers complete payment on the MPGS hosted page and the platform polls `/api/payments/status/<ref_id>/` to reconcile state after the redirect.【F:billing/views.py†L84-L197】

## 6. Developer Checklist

Before opening a pull request for a new gateway, confirm the following:

- [ ] Settings variables and environment secrets are documented and loaded.
- [ ] Gateway helper in `billing/utils.py` covers charge creation and status retrieval.
- [ ] `PaymentListCreateView`, `PaymentStatusCheckView`, and `UpdatePendingPaymentsView` include gateway-specific branches.
- [ ] Frontend radio option, icon, and JavaScript adjustments are in place.
- [ ] Sandbox tests (manual or automated) validate happy path and failure scenarios.
- [ ] Operational runbooks include monitoring and support instructions for the new provider.
