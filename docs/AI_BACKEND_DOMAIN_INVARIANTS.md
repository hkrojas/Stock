# AI Backend Domain Invariants

## Purpose
This file defines the business invariants that backend code must protect.

AI agents must treat these rules as higher priority than convenience or UI assumptions.

## Global Principles
- The backend is the authority.
- The database should enforce what it reasonably can.
- The backend should reject invalid transitions explicitly.
- Silent correction is forbidden for stock and workflow operations.
- Every stock mutation must be attributable.

## Identity and Ownership Invariants

### Users
- Only allowed roles may perform management actions.
- Role-sensitive operations must be checked in the backend, not only in the SPA.
- Superadmin and manager capabilities must be explicit, not inferred loosely.

### Buildings
- A building can have at most one directly assigned admin at a time if using the current single-admin model.
- Building reassignment must not silently orphan active operational state.

## Order Invariants

### Drafts
- There must be at most one active draft order per building.
- Draft uniqueness must not depend only on application-level `first()` queries.

### State Machine
Suggested order states:
- `draft`
- `submitted`
- `processing`
- `partially_dispatched` (future-ready)
- `dispatched`
- `delivered`
- `cancelled`
- `rejected` (optional explicit future state)

Rules:
- `draft -> submitted`
- `submitted -> draft` only if workflow explicitly allows reopen
- `submitted -> processing`
- `processing -> dispatched`
- `dispatched -> delivered`
- `draft/submitted -> cancelled`
- invalid transitions must fail explicitly

### Items
- Order item quantity must always be positive.
- Order items must not be duplicated for the same order/product unless intentionally merged.
- Product snapshot fields should reflect order-time data, not mutable current product data.

## Dispatch Batch Invariants
- A batch must contain only valid eligible orders.
- A batch must not consolidate the same order more than once.
- A batch-product aggregation row must be unique per batch/product.
- Confirming a batch must be idempotent or explicitly conflict on repeat.
- Rejecting an order from a batch must rebuild aggregate totals correctly.

## Central Inventory Invariants
- Central stock must never become negative.
- Reserved stock must never exceed available stock.
- Dispatch must consume reserved or validated stock, not unchecked raw stock.
- Purchases must increase stock only through auditable movements.
- Manual stock correction must be audited with reason and actor.

## Building Inventory Invariants
- A building can have only one inventory row per product.
- Building inventory quantity must never become negative.
- Receiving a dispatched order must be safe against duplicate confirmation.
- Consumption cannot silently clamp to available stock.
- Adjustments must be distinguishable from real consumption.

## Inventory Movement / Ledger Invariants
Each inventory-affecting event should carry:
- actor
- timestamp
- movement type
- quantity
- source/target context
- reference entity id
- optional reason

Suggested movement types:
- `purchase`
- `reserve`
- `release`
- `dispatch`
- `receive`
- `consume`
- `adjust`
- `return`
- `transfer_out`
- `transfer_in`
- `shrinkage`

Rules:
- movement records are append-only
- movement records should not be silently rewritten to hide history
- stock numbers should be derivable or at least reconcilable from movements

## Purchase Invariants
- Purchase creation must be atomic.
- Invalid lines must fail the whole operation, not be skipped silently.
- Purchase total should match line items.
- Inventory increase from purchases must be auditable.

## Catalog Import Invariants
- Product matching rules must be explicit.
- Name-only collision handling is unsafe and should be treated carefully.
- Catalog metadata update and stock mutation are different concerns.
- Bulk import should be previewable before commit.

## API Behavior Invariants
- Repeating the same mutating request should not create duplicate business effects when idempotency is expected.
- Business conflicts should return conflict-style responses, not generic server errors.
- Authorization failures should be explicit and consistent.
- Missing entities should not be conflated with forbidden ownership.

## What AI Agents Must Never Do
- Never auto-correct over-consumption by truncating quantity.
- Never silently skip invalid purchase rows.
- Never rely only on frontend route guards for protection.
- Never implement stock changes in the SPA.
- Never keep startup code that mutates production data.
- Never add a feature that bypasses these invariants for convenience.
