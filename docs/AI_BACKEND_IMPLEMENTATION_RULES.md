# AI Backend Implementation Rules

## Purpose
This file defines execution rules for AI coding agents working on the backend.

These rules are operational. Follow them during every backend refactor phase.

## Primary Objective
Make the FastAPI backend the durable, auditable, conflict-safe core for the SPA and future mobile clients.

## Non-Negotiable Rules
- FastAPI is the source of truth.
- Do not move business logic into the SPA.
- Do not hide backend weaknesses with frontend workarounds.
- Do not silently auto-correct stock requests.
- Do not silently ignore invalid rows in critical write flows.
- Do not keep startup code that mutates production data.

## Refactor Scope Rules
- Work in phases.
- Keep each PR/change set small and focused.
- Do not mix architecture cleanup with feature expansion unless the change is inseparable.
- If a breaking API change is unavoidable, document it explicitly.

## Coding Structure Rules
- Endpoints orchestrate; services decide; models persist.
- Prefer explicit service methods for mutations.
- Keep transaction boundaries in services, not scattered across endpoints.
- Prefer explicit domain errors over generic exceptions.
- Make side effects visible.

## Database Rules
- Prefer migrations over runtime schema mutation.
- Prefer DB constraints for true invariants.
- If an invariant cannot be fully expressed in DB, enforce it in service layer explicitly.
- Never rely only on `first()` queries to preserve uniqueness under concurrency.

## Concurrency Rules
For operations involving stock or workflow transitions:
- assume retries can happen
- assume users can click twice
- assume two operators can act at the same time
- assume mobile/network delays will create duplicate intent

Therefore:
- use idempotency or explicit conflict behavior
- use locking/version checks where required
- keep stock mutation and audit creation in one transaction

## API Rules
- Keep `/api/v1` stable unless change is justified.
- Return consistent error semantics.
- Repeated critical operations must be idempotent or explicitly conflict.
- Never use GET endpoints for hidden mutation.
- Avoid endpoint behavior that sometimes creates and sometimes silently reuses without clear contract.

## Validation Rules
- Reject negative or impossible quantities.
- Reject invalid state transitions.
- Reject ownership violations.
- Reject malformed business requests clearly.
- Never clamp a user-requested quantity silently.

## Auditability Rules
Any operation that changes stock or workflow state should preserve:
- actor
- timestamp
- entity reference
- quantity or state delta
- reason/context when applicable

If a future operator cannot understand why stock changed, the implementation is insufficient.

## Migration Rules
- Prefer additive migrations first.
- Include data cleanup notes when adding new constraints.
- Do not assume legacy data is clean.
- If cleanup is risky, stop and document manual intervention requirements.

## Backward Compatibility Rules
- Preserve current SPA compatibility when possible.
- If contract changes are needed, provide a migration note for frontend updates.
- Do not rename fields casually in early phases.
- Transitional compatibility is acceptable; silent semantic ambiguity is not.

## Testing Expectations
Even if a formal test suite is incomplete, critical flows should be testable in isolation:
- draft creation
- order submit
- dispatch consolidate
- dispatch confirm
- receive order
- consume building inventory
- create purchase

Agents should favor code organization that makes these tests easy to add.

## Commit / Change Discipline
Every implementation batch should report:
1. files changed
2. migration impact
3. behavior changes
4. compatibility concerns
5. remaining risks

## Anti-Patterns AI Agents Must Avoid
- giant refactors touching every module at once
- endpoint-level business logic duplication
- silent partial success for critical writes
- optimistic assumptions without conflict handling
- weakening domain rules for UI convenience
- using generic `Exception` paths for domain failures
- mixing demo seed logic with production startup

## Preferred Delivery Style
When implementing a phase:
- start with a short execution plan
- modify only the files needed for that phase
- keep changes coherent
- explain any intentional tradeoff
- leave clear next steps for the following phase
