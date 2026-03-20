# Session-2026-03-19-002

## Current State (last updated: architecture articles complete)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current task:** Session complete
- **Blocking on:** Nothing
- **Next:** Per PROJECT_STATE forward plan

## Progress Log

### Session Start
- Read previous session notes (Session-2026-03-19-001)
- Read PROJECT_STATE.md, SELF.md, START_HERE.md
- Initialized session

### Feature: Gate condition labels on workflow node cards
- **Problem:** Proceed gate conditions (e.g., `table_has_columns AND table_has_rows`) were invisible on rendered workflow cards. Backend serialization only extracted `field_truthy` condition keys — all other condition types were silently dropped.
- **Root cause:** `_serialize_definition()` in `renderer.py` filtered `requires` to only `field_truthy` type conditions. The card renderer already had a `.fc-gate` section but received empty data for non-field gates.
- **Fix 1 — Backend (`renderer.py`):** Added `_gate_labels(gate)` helper that recursively walks the gate expression tree and produces human-readable labels for all 6 condition types (`field_truthy`, `field_equals`, `field_not_null`, `set_membership`, `table_has_columns`, `table_has_rows`) plus NOT/AND/OR composites. Replaced lossy extraction with `_gate_labels()` call. Also serializes `gate_op` when not AND.
- **Fix 2 — Frontend (`agent_observer.html`):** OR gates now join labels with ` or ` instead of `, ` for clear semantics.
- Backward compatible — `requires` is still a list of strings; field-based gates show field keys as before.
- Committed and pushed (submodule `1cc9b09`, parent `5680be9`)

### Architecture Articles
Three documents written to the session folder:

1. **`agent-portal-article.md`** — Technical exposition of the Agent Portal. Covers current architecture (YAML runtime, affordance model, feedback model, topology visualization), the bijective mapping principle as central invariant, the convergence trajectory from sandbox to universal QMS interaction paradigm, and recursive self-extension via the builder.

2. **`workflow-platform-article.md`** — Reframes the engine as a general-purpose platform through four analogies (game engine, programming language, app store, international standard). Argues the agentic ecosystem is in its pre-engine era and needs a workflow runtime, not more workflow applications.

3. **`workflow-platform-deployed.md`** — Present-tense platform reference document. Describes the system as deployed and in use. Covers collaboration mode (observer affordances resolved into interactive UI controls, human executes same POSTs as agent), multi-executor workflows with role-scoped affordances, and adoption patterns (QMS, SDLC, regulatory compliance, process iteration).

### Core Design Principle: Lossless, Non-Additive, and Representationally Free
Discussion with the Lead distilled the project's core architectural principle beyond "agent first" to a general software design constraint:

- **Lossless:** Every semantic element the engine produces must appear in every projection. No omission.
- **Non-additive:** No projection may introduce semantic elements not in the engine's output. No invention.
- **Representationally free:** Projections choose how to represent, never whether to represent. Multiple renderers coexist by varying form, not content.

Formalized in **`lossless-non-additive-representationally-free.md`** — covers the principle statement, definitions, the semantic-representational boundary with conformance tests, rationale, architectural consequences, and relationship to existing concepts (MVC, Redux, HATEOAS).
