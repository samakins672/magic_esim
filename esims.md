# eSIM Pricing and Vendor Management

This guide explains how eSIM plan pricing is stored, surfaced to the product, and controlled for each supported vendor integration. It is intended for operations engineers and product managers who update pricing or vendor settings through the Django admin console.

## 1. Data Model Overview

Purchased or manually created plans are stored in the `eSIMPlan` model. Each record captures the catalog metadata that was active when the order was placed along with audit information that powers the customer dashboard.

| Field | Purpose |
| --- | --- |
| `name`, `slug`, `package_code` | Identifiers that originate from the upstream vendor catalogue and are used when reconciling API responses. |
| `price` | Decimal amount stored exactly as billed. This value feeds every place in the UI that shows what a customer paid. |
| `currency_code` | Currency symbol accompanying price displays and payment reconciliation. |
| `volume`, `duration`, `support_top_up_type` | Plan allowances that drive plan usage calculations. |
| `seller` | Records which vendor (for example `esimaccess` or `esimgo`) fulfilled the plan; used when determining which API integration to call. |
| `order_no`, `iccid`, `payment` | Keys used to look up live usage and match orders to payment records. |
| `expires_on`, `activated_on`, `date_created` | Support expiration and lifecycle tracking in the customer portal. |

> The model definition lives in `esim/models.py` and is registered with the Django admin site for inline editing.【F:esim/models.py†L1-L32】【F:esim/admin.py†L1-L4】

## 2. Where Pricing Appears

Pricing is surfaced in two distinct contexts:

1. **Live catalogue browsing** – When customers browse available plans, the API layer fetches fresh data from vendor endpoints. The view enriches those responses with formatted price strings so that the storefront can display consistent currency markups.
   * eSIMAccess packages are sorted and formatted in `eSIMPlanListView`, where raw prices are converted using `((price / 10000) * 2)` to match existing markup rules.【F:esim/views.py†L84-L127】
   * eSIMGo bundles are fetched by the same view and formatted with `(price * 2)` before being returned to the client.【F:esim/views.py†L138-L200】
2. **Purchased plan management** – When querying historic purchases (for example in dashboards), the application reloads the stored `eSIMPlan.price`, reuses the same markup formatter, and exposes both the original amount and a user-friendly `formattedPrice` field.【F:esim/views.py†L360-L419】【F:esim/views.py†L444-L559】

Because both paths eventually reference the saved `price` column, updating the value in the database updates every downstream usage.

## 3. Updating Prices in Django Admin

You can correct or override pricing for existing plans directly from the Django admin interface. The admin is especially useful when reconciling charges against vendor invoices or applying goodwill adjustments.

1. **Sign in** to the Django admin panel using a superuser account.
2. Navigate to **eSIM Plans** under the eSIM app.
3. Click an individual plan record to edit it. Key fields you may adjust:
   * `Price` – enter the final amount that should display to customers. Decimal precision is enforced, so use two decimal places (e.g., `19.99`).
   * `Currency code` – aligns the amount with the appropriate currency symbol.
   * `Seller` – only change if the order was fulfilled by a different vendor than recorded.
   * `Expires on` – extend or shorten plan validity when issuing extensions.
4. Press **Save**. The admin automatically persists the changes, and subsequent API calls will output the updated pricing because every serialization step reads from the database column described above.

> Tip: For bulk adjustments, export plan records, edit them offline, and re-import using the admin’s built-in action set or a management command. This ensures markup logic remains consistent with the stored values.

## 4. Vendor Integrations

The project integrates with two upstream vendors. Configuration is driven by environment variables to keep credentials out of source control.

### eSIMAccess

* **Catalogue** – `POST {ESIMACCESS_HOST}/api/v1/open/package/list` using the `RT-AccessCode` header. The same credentials power order placement and plan usage lookups.【F:esim/utils.py†L7-L55】【F:esim/views.py†L80-L137】【F:esim/views.py†L360-L434】
* **Order fulfilment** – `order_esim_profile` submits the amount you charge along with the package code. The vendor returns an `orderNo`, which is stored on the plan record for future reconciliation.【F:esim/utils.py†L62-L85】

### eSIMGo

* **Catalogue** – `GET {ESIMGO_HOST}/catalogue` or `/catalogue/bundle/<package_code>` with the `x-api-key` header. Responses are filtered and formatted locally before returning to the client.【F:esim/utils.py†L17-L55】【F:esim/views.py†L138-L200】

### Required Environment Variables

Add the following keys to your deployment environment (`.env`, platform secrets, etc.):

| Variable | Description |
| --- | --- |
| `ESIMACCESS_HOST` | Base URL for the eSIMAccess API. |
| `ESIMACCESS_ACCESS_CODE` | Access token used for every eSIMAccess request. |
| `ESIMGO_HOST` | Base URL for the eSIMGo API. |
| `ESIMGO_API_KEY` | API key required for catalogue requests to eSIMGo. |

The helper utilities read these values at import time, so restart long-running processes after any change to ensure fresh configuration is loaded.【F:esim/utils.py†L1-L85】

## 5. Applying Pricing Adjustments Programmatically

While the admin console is ideal for one-off edits, development teams may need to change markups globally. Two common approaches are:

1. **Adjust formatting multipliers** – Update the conversion logic in `eSIMPlanListView` if the markup strategy changes (for example, switch from `* 2` to `* 1.5`). Remember to apply the same rule to both catalogue and purchased-plan branches so the UI remains consistent.【F:esim/views.py†L84-L200】【F:esim/views.py†L360-L559】
2. **Automated migrations or scripts** – Write a Django management command that iterates over `eSIMPlan` records and recalculates `price` based on the latest vendor feed before saving. Because the admin exposes the same model, manual and automated edits coexist without conflicts.

## 6. Operational Checklist

* Confirm vendor credentials before changing prices; failed API calls might hide catalogue items, leading to empty storefronts.
* After updating price rules or individual records, spot-check the storefront or API responses to verify the new values show as expected.
* When switching a plan’s `seller`, ensure the `package_code` exists in the new vendor’s catalogue to avoid downstream order failures.
* Document any manual overrides in your change management logs; the `date_created` and `activated_on` timestamps help correlate customer communications with backend edits.【F:esim/models.py†L24-L29】

With these practices, you can confidently maintain accurate eSIM pricing while keeping vendor integrations in sync.
