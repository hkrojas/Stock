# AI Backend Full Sequential Execution Prompt

Copy and paste the following prompt into Antigravity or a similar AI coding tool.

```text
Read and follow these files strictly and in this exact order:

1. docs/AI_BACKEND_MASTER_EXECUTION_BLOCK.md
2. docs/AI_BACKEND_IMPLEMENTATION_RULES.md
3. docs/AI_BACKEND_DOMAIN_INVARIANTS.md
4. docs/AI_BACKEND_API_CONVENTIONS.md
5. docs/AI_BACKEND_ROADMAP.md
6. docs/AI_BACKEND_PHASE_1_FOUNDATION.md
7. docs/AI_BACKEND_PHASE_2_DATA_INTEGRITY.md
8. docs/AI_BACKEND_PHASE_3_INVENTORY_ENGINE.md
9. docs/AI_BACKEND_PHASE_4_ORDERS_AND_DISPATCH.md
10. docs/AI_BACKEND_PHASE_5_BUILDING_INVENTORY_LIFECYCLE.md
11. docs/AI_BACKEND_PHASE_6_PURCHASES_AND_IMPORTS.md
12. docs/AI_BACKEND_PHASE_7_SECURITY_AND_MOBILE_READINESS.md

Your mission:
Execute all backend phases in sequence, from Phase 1 through Phase 7, but with these non-negotiable rules:

GLOBAL RULES
- Work on backend only.
- Do not modify frontend-spa unless explicitly required later by a separate instruction.
- Do not combine phases.
- Do not skip phases.
- Do not start a new phase until the current phase is fully completed.
- If a phase is incomplete, stop immediately and do not continue to the next phase.
- Keep public API contracts as stable as possible unless a change is strictly necessary.
- Prefer small, coherent, reviewable commits.
- Respect the domain invariants and API conventions from the docs.

PHASE EXECUTION RULES
For each phase:
1. Read the corresponding phase document again before making changes.
2. Implement only the work allowed in that phase.
3. Do not include work from later phases, even if it seems convenient.
4. When the phase is finished, output a PHASE GATE REPORT.
5. Only continue to the next phase if and only if the PHASE GATE REPORT says:
   - Status: COMPLETE
   - Next phase allowed: YES

PHASE GATE REPORT FORMAT
Use exactly this structure after every phase:

PHASE GATE REPORT
Phase: <phase number and name>
Status: COMPLETE or INCOMPLETE

Files changed:
- ...

Migrations added/updated:
- ...

Acceptance criteria check:
- [x] criterion 1
- [x] criterion 2
- [ ] criterion 3

Compatibility impact:
- ...

Open risks:
- ...

Next phase allowed:
- YES or NO

HARD STOP RULE
If any acceptance criterion for the current phase is not satisfied:
- mark Status: INCOMPLETE
- mark Next phase allowed: NO
- stop execution
- do not begin the next phase

PHASE ORDER
Execute in this exact order only:
1. Phase 1 — Foundation and Safety
2. Phase 2 — Data Integrity and Invariants
3. Phase 3 — Inventory Engine and Stock Ledger
4. Phase 4 — Orders and Dispatch Workflow Hardening
5. Phase 5 — Building Inventory Lifecycle
6. Phase 6 — Purchases and Catalog Imports
7. Phase 7 — Security, Observability, and Mobile Readiness

QUALITY RULES
- Endpoints orchestrate; services decide; models persist.
- Do not leave critical workflow logic duplicated in endpoints.
- Do not silently clamp requested quantities.
- Do not silently ignore invalid rows in purchases or imports.
- Do not preserve unsafe startup bootstrap behavior.
- Prefer migrations over runtime schema mutation.
- Protect inventory consistency and workflow transitions explicitly.
- Keep stock mutations auditable.

FINAL DELIVERY RULE
At the very end, if all phases are fully completed, output a final summary with:
1. all phases completed
2. files changed by phase
3. migrations added by phase
4. breaking changes or compatibility notes
5. remaining risks, if any

Now begin with Phase 1 only.
If Phase 1 is not fully complete, stop there.
If Phase 1 is complete, continue to Phase 2, and so on, always respecting the hard gate rule.
```
