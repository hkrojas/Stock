# AI Backend Phase 5 — Building Inventory Lifecycle

## Phase Goal
Complete the local inventory lifecycle for buildings so receipt, usage, adjustment, return, transfer, and shrinkage are first-class backend operations.

This phase closes the operational loop after dispatch.

## In Scope
- Receipt confirmation semantics.
- Consumption semantics.
- Audited stock adjustment semantics.
- Returns from building inventory to central inventory.
- Transfers between buildings.
- Shrinkage/loss handling.
- Building-level movement visibility.

## Out of Scope
- Forecasting.
- Procurement automation.
- Frontend dashboards beyond what backend contracts need.

## Current Problems This Phase Must Solve
- Building inventory currently supports only a limited operational lifecycle.
- Consumption and adjustment are too close semantically.
- Return and transfer flows are missing.
- Shrinkage/loss events are not modeled explicitly.
- Post-dispatch corrections are not fully auditable.

## Design Principles
- Receipt is not the same as dispatch.
- Consumption is not the same as adjustment.
- Returns must restore central-state consistency.
- Transfers must preserve total stock across buildings.
- Shrinkage must be explicit and attributable.

## Core Concepts

### Receipt
- A building receives inventory only from valid dispatch/order fulfillment.
- Receipt must be conflict-safe against duplicate confirmation.
- Receipt should create auditable movement(s).

### Consumption
- Consumption reduces building inventory because materials were actually used.
- It must fail if insufficient quantity exists.
- It must not be auto-clamped.

### Adjustment
- Adjustment corrects data, not operational usage.
- It requires reason/context.
- It must be auditable as a correction.

### Return
- Return moves stock from building inventory back to central inventory.
- It must not create or destroy stock implicitly.
- It must be represented by paired movements.

### Transfer
- Transfer moves stock from one building to another.
- Total quantity across buildings should remain conserved.
- Transfer should use paired source/target movements.

### Shrinkage
- Shrinkage/loss records unrecoverable reduction.
- It must be explicit and attributable.

## Concrete Tasks

### 1. Harden Receipt Semantics
Requirements:
- duplicate receipt attempts must conflict or be idempotent by design
- receipt must update building inventory safely
- receipt must create auditable movement entries
- related order fulfillment state must remain coherent

Acceptance:
- repeated receipt requests do not inflate stock

### 2. Separate Consumption from Adjustment
Requirements:
- consumption endpoint/service fails on insufficient quantity
- adjustment endpoint/service requires explicit correction semantics
- movement/audit records distinguish real usage from correction

Acceptance:
- building inventory history is interpretable after the fact

### 3. Add Return Flow
Requirements:
- return from building to central inventory
- quantity checks at source building inventory
- paired movements or equivalent auditable record set
- central stock restored consistently

Acceptance:
- stock can be sent back without ad hoc manual correction

### 4. Add Transfer Flow
Requirements:
- source building quantity validation
- destination inventory merge/create behavior must be deterministic
- paired transfer-out / transfer-in records
- protected transaction boundary

Acceptance:
- stock can move between buildings without hidden side effects

### 5. Add Shrinkage / Loss Flow
Requirements:
- explicit movement type
- quantity and reason required
- actor recorded
- no silent reductions through generic adjustments

Acceptance:
- losses are visible and auditable

### 6. Building Inventory History Access
Prepare backend support for querying building inventory history by:
- building
- product
- movement type
- date range

Acceptance:
- building-level stock history is explainable

## Suggested Service Boundaries
Suggested services:
- `BuildingInventoryService`
- `InventoryTransferService` or transfer methods within building inventory service

Responsibilities:
- receive inventory
- consume inventory
- adjust inventory with reason
- return inventory to central
- transfer inventory between buildings
- register shrinkage

## Transaction Guidance
The following must be atomic:
- receipt into building inventory
- building-to-central return
- building-to-building transfer
- shrinkage registration with stock update

Do not commit stock mutation and movement creation separately.

## Definition of Done
- receipt is conflict-safe
- consumption does not clamp silently
- adjustment is audit-oriented
- return flow exists
- transfer flow exists
- shrinkage flow exists
- building inventory history is queryable or backend-ready

## Guidance for AI Agents
- Do not model returns/transfers as generic manual adjustments.
- Do not allow negative building stock.
- Do not merge movement semantics into vague “update quantity” behavior.
- Keep building lifecycle explicit and auditable.

## Deliverables Expected from an Implementation PR
- service-layer changes
- any model/migration changes required
- new movement semantics if needed
- endpoint contract notes
- explicit note on how duplicate receipt and transfer retries are handled
