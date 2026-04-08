# API Contracts - Stock SPA

This document serves as the source of truth for the communication between the Vue 3 SPA and the FastAPI backend. It categorizes endpoints by domain and specifies the expected payloads and responses.

## 1. Catalog & Products
**Base Path:** `/catalog`

| Method | Endpoint | Description | Payload |
| :--- | :--- | :--- | :--- |
| GET | `/all` | Fetch all products | `params: { q: string }` |
| GET | `/:id` | Fetch product detail | - |
| POST | `/` | Create product | `{ name, description, sku, ... }` |
| PUT | `/:id` | Update product | `{ name, description, ... }` |
| PATCH | `/:id/toggle` | Toggle product status | - |
| PUT | `/:id/sync` | Sync product with source | - |
| POST | `/preview` | Scrape product info | `params: { url: string }` |
| POST | `/import-csv` | Import CSV | `FormData: { file: File }` |
| GET | `/uploads` | List CSV upload history | - |
| DELETE | `/uploads/:id` | Delete upload record | - |

---

## 2. Users & Authentication
**Base Path:** `/auth` & `/users`

| Method | Endpoint | Description | Payload |
| :--- | :--- | :--- | :--- |
| POST | `/auth/token` | Login (OAuth2 Password) | `FormData: { username, password }` |
| GET | `/users/me` | Get current user info | - |
| GET | `/users/` | List users by role | `params: { role: string }` |
| GET | `/users/:id` | Get user detail | - |
| POST | `/users/` | Create user | `{ email, full_name, role, ... }` |
| PUT | `/users/:id` | Update user | `{ email, full_name, ... }` |
| DELETE | `/users/:id` | Delete user | - |

---

## 3. Buildings
**Base Path:** `/buildings`

| Method | Endpoint | Description | Payload |
| :--- | :--- | :--- | :--- |
| GET | `/` | List all buildings | - |
| GET | `/unassigned` | List unassigned buildings | - |
| GET | `/:id` | Get building detail | - |
| POST | `/` | Create building | `{ name, address }` |
| PUT | `/:id` | Update building | `{ name, address }` |
| DELETE | `/:id` | Delete building | - |
| POST | `/assign` | Assign admin to buildings | `{ admin_id, building_ids }` |

---

## 4. Orders
**Base Path:** `/orders`

| Method | Endpoint | Description | Payload |
| :--- | :--- | :--- | :--- |
| GET | `/` | List orders | `params: { status, building_id }` |
| GET | `/:id` | Get order detail | - |
| POST | `/` | Create initial order | `{ building_id }` |
| POST | `/:id/items` | Add item to order | `{ product_id, quantity }` |
| DELETE | `/:id/items/:iid` | Remove item from order | - |
| POST | `/:id/items/:iid/update` | Update item quantity | `{ quantity }` |
| POST | `/:id/submit` | Finalize/Submit order | - |
| POST | `/:id/reopen` | Reopen order | - |
| POST | `/:id/cancel` | Cancel order | - |
| POST | `/:id/receive` | Confirm reception | - |
| GET | `/consumption-report`| Consumption history | `params: { building_id }` |

---

## 5. Dispatch
**Base Path:** `/dispatch`

| Method | Endpoint | Description | Payload |
| :--- | :--- | :--- | :--- |
| GET | `/pending-orders` | List consolidatable orders| - |
| POST | `/consolidate` | Create batch from orders | `[order_id, ...]` |
| GET | `/history` | List batch/dispatch history| - |
| GET | `/batch/:id` | Get batch detail | - |
| GET | `/batch/:id/picking` | Get picking list | - |
| POST | `/batch/:id/confirm` | Finalize dispatch batch | - |
| POST | `/batch/:id/reject-order/:oid` | Reject specific order | `params: { rejection_note }` |
| GET | `/batch/:id/export/buildings` | Export PDF by building | - |
| GET | `/batch/:id/export/consolidated` | Export PDF consolidated | - |

---

## 6. Inventory
**Base Path:** `/inventory`

| Method | Endpoint | Description | Payload |
| :--- | :--- | :--- | :--- |
| GET | `/` | List current inventory | `params: { building_id }` |
| POST | `/` | Direct stock entry | `{ product_id, building_id, quantity }` |
| POST | `/:id/consume` | Record consumption | `{ quantity, note }` |
| POST | `/:id/adjust` | Record adjustment | `{ quantity, reason }` |

---

## 7. Purchases
**Base Path:** `/purchases`

| Method | Endpoint | Description | Payload |
| :--- | :--- | :--- | :--- |
| GET | `/` | List purchase orders | - |
| GET | `/:id` | Purchase order detail | - |
| POST | `/` | Create purchase order | `{ items: [{ product_id, quantity }] }` |

---

## 8. Analytics
**Base Path:** `/analytics`

| Method | Endpoint | Description | Payload |
| :--- | :--- | :--- | :--- |
| GET | `/superadmin` | Superadmin metrics | - |
| GET | `/manager` | Manager metrics | - |
| GET | `/admin` | Building admin metrics | - |

---

## Global Naming Conventions
- **IDs**: Always UUID strings.
- **Null Safety**: Collections default to `[]`.
- **Error Semantics**:
    - `401`: Token expired/invalid -> Redirect to Login.
    - `403`: Insufficient permissions -> Dashboard Empty State.
    - `409`: Conflict (e.g., SKU duplicate) -> Institutional Alert.
    - `422`: Validation error -> Form inline feedback.
