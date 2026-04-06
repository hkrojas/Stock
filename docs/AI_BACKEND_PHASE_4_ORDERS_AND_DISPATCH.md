# AI Backend Phase 4 — Orders and Dispatch Workflow Hardening

## Phase Goal
Formalize and harden the order and dispatch lifecycle so repeated requests, concurrent operators, and future mobile clients do not corrupt workflow state.

This phase is about workflow correctness and idempotent state transitions.

## In Scope
- Define explicit order state machine.
- Define explicit dispatch-batch state machine.
- Make submit/consolidate/confirm/receive conflict-safe.
- Normalize rejection semantics.
- Prepare backend support for partial fulfillment and backorders.
- Keep stock-aware workflow orchestration in services.

## Out of Scope
- Frontend UX redesign.
- Forecasting or planning logic.
- Procurement strategy.
- Advanced notification systems.

## Current Problems This Phase Must Solve
- Order transitions are handled across endpoints without a formal state machine.
- Repeated requests can create ambiguous results.
- Dispatch workflow relies on late validation.
- Rejection and retry semantics are not formalized enough.
- Current order/dispatch lifecycle is not yet designed for partial fulfillment.

## Target Order State Machine
Recommended order states:
- `draft`
- `submitted`
- `processing`
- `partially_dispatched`
- `dispatched`
- `delivered`
- `cancelled`
- `rejected` (optional if distinct from returned-to-submitted semantics)

Allowed transitions must be explicit.

Minimum required transitions:
- `draft -> submitted`
- `submitted -> draft` only if reopen is explicitly allowed
- `submitted -> processing`
- `processing -> partially_dispatched` or `processing -> dispatched`
- `partially_dispatched -> dispatched`
- `dispatched -> delivered`
- `draft/submitted -> cancelled`

Any other transition must fail explicitly.

## Target Dispatch Batch State Machine
Recommended batch states:
- `pending`
- `reserved`
- `partially_dispatched`
- `dispatched`
- `cancelled`

Minimum flow:
- pending batch created from eligible orders
- stock reserved/validated
- dispatch confirmed
- orders updated consistently

## Concrete Tasks

### 1. Formalize Order State Validation
Implement service-level transition validation.

Requirements:
- transitions must be centralized
- invalid transitions must raise domain errors
- repeated legal-looking requests must be conflict-safe

Acceptance:
- order state changes are no longer ad hoc endpoint behavior

### 2. Formalize Dispatch Batch State Validation
Implement service-level transition validation for dispatch batches.

Requirements:
- batch confirmation must not run twice silently
- invalid repeated confirmation must conflict or be idempotent by design
- removing/rejecting an order from a batch must preserve batch integrity

Acceptance:
- dispatch lifecycle is explicit and protected

### 3. Make Critical Mutations Idempotent or Conflict-Safe
Operations to harden:
- submit order
- reopen order
- cancel order
- consolidate orders into batch
- confirm dispatch
- receive order

Allowed behaviors:
- true idempotency
- or explicit `409 Conflict`

But behavior must be deliberate and documented.

Acceptance:
- network retries do not create ambiguous state corruption

### 4. Normalize Rejection Semantics
When an order is rejected from a batch:
- order state must become explicit and predictable
- batch aggregates must rebuild correctly
- reservation/release interactions must remain correct
- rejection note semantics must be preserved

Acceptance:
- rejection path is deterministic and auditable

### 5. Prepare for Partial Fulfillment
Even if full partial-dispatch support is not exposed yet, backend design should be ready for it.

Prepare model/service thinking for:
- order lines partially fulfilled
- batch confirms less than originally requested
- remaining quantities stay pending/backordered

Acceptance:
- later partial-dispatch work will not require breaking the state model again

### 6. Keep Workflow Logic in Services
Required service candidates:
- `OrderWorkflowService`
- `DispatchWorkflowService`

Responsibilities:
- transition validation
- orchestration of stock reservation/consumption interactions
- batch/order synchronization
- rejection semantics
- receive semantics

Acceptance:
- endpoints become orchestration-only wrappers

## Transaction Guidance
The following must happen in protected transaction boundaries:
- submit order if it affects reservation-ready workflow semantics
- consolidate into batch
- reject from batch
- confirm dispatch
- receive order

Do not update order state, batch state, and stock effects in separate loose commits.

## Definition of Done
- order state machine is explicit
- batch state machine is explicit
- critical operations are idempotent or conflict-safe
- rejection behavior is deterministic
- backend is ready for partial fulfillment evolution
- workflow orchestration lives in services

## Guidance for AI Agents
- Do not invent hidden transitions.
- Do not let repeated actions succeed ambiguously.
- Do not leave workflow behavior distributed across many endpoints.
- Do not couple workflow correctness to frontend sequence assumptions.

## Deliverables Expected from an Implementation PR
- service-layer workflow code
- any migration/model changes required
- clear transition rules
- compatibility notes for API consumers
- explicit note on idempotency/conflict semantics per critical endpoint
