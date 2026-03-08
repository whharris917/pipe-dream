# Project State

*Last updated: Session-2026-03-06-001 (2026-03-08)*

---

## 1. Where We Are Now

**Workflow engine built — experimental/provisional.** CR-110 is IN_EXECUTION (v1.1). EI-1 through EI-4 are complete (Pass). The engine has gone from nothing to a fully functional graph-based workflow system with construction/execution modes, hooks, templates, form-based input, multi-agent isolation, and a pure-convention compile renderer.

**Provisional status:** All WFE development artifacts (engine code, domain content, CR type templates, create-cr wizard, db.json) are provisional. SDLC-WFE-RS is still DRAFT. No WFE workflow has been used to manage an actual QMS document in production. Post-review under CR-110 and real-world validation are required before the engine is considered stable.

**Key design decisions (finalized):**
- Primitives: **Field** {name, type, value?, writable, parameter}, **Node** {id, fields, edges, prompt?, label?, template_id?}, **Edge** {target, condition?, traverse_hooks?}
- Two modes: construction (modify graph structure) and execution (fill fields, advance)
- Acyclic DAG always valid; replication pattern for repeating steps
- YAML storage: workflow definitions + live session state
- Multi-agent isolation via `WFE_SESSION` env var — all state under `.wfe/sessions/<id>/`
- Template system: templates define node structure; instantiation stamps `template_id` and `label` onto nodes for compile provenance
- Form-based input: `wfe draft` + `wfe submit` for structured multi-field YAML editing
- Compile: pure convention renderer — same-template nodes → table, templateless nodes → section; no domain knowledge in engine

**65 CRs CLOSED (CR-042 through CR-105, CR-108, CR-109, plus CR-091-ADD-001). 5 INVs CLOSED.**

---

## 2. The Arc

**Foundation through Quality Manual** (Feb 1-24, CR-042 through CR-105).

**DocuBuilder Genesis Sandbox** (Mar 3, CR-108). Table-primitive model proved concept, revealed design limits.

**Workflow Engine Design and Build** (Mar 3 - present, Sessions 2026-03-03 through 2026-03-07):
- Bedrock primitives distilled (Field, Node, Edge — everything else emergent)
- CR-109 executed: `qms-workflow-engine` submodule established under formal control
- CR-110: initial development CR — requirements + implementation

---

## 3. What's Built

### SDLC Document State

| Document | Version | Tests |
|----------|---------|-------|
| SDLC-QMS-RS | v22.0 EFFECTIVE | 143 requirements |
| SDLC-QMS-RTM | v27.0 EFFECTIVE | 687 tests, qualified commit 918984d |
| SDLC-CQ-RS | v2.0 EFFECTIVE | 6 requirements |
| SDLC-CQ-RTM | v2.0 EFFECTIVE | Inspection-based, qualified commit d3c34e5 |
| SDLC-WFE-RS | v0.1 DRAFT | 30 requirements (7 categories + 4 execution mode reqs) |
| Qualified Baseline | CLI-18.0 | qms-cli commit 309f217 (main) |

### Controlled Document State

| Document | Version |
|----------|---------|
| SOP-001 through SOP-007 | v21.0 / v16.0 / v3.0 / v9.0 / v7.0 / v5.0 / v2.0 EFFECTIVE |
| TEMPLATE-CR | v10.0 EFFECTIVE |
| TEMPLATE-VAR | v3.0 EFFECTIVE |
| TEMPLATE-ADD | v2.0 EFFECTIVE |
| TEMPLATE-VR | v3.0 EFFECTIVE |

### Workflow Engine Capabilities (qms-workflow-engine) — *Experimental/Provisional*

| Module | Description |
|--------|-------------|
| `wfe/graph.py` | Field (block hint), Node (scaffold flag), Edge, Graph; lifecycle + reopen(); DAG invariant |
| `wfe/session.py` | Navigation (go, home); fill(), advance(); WFE_SESSION multi-agent isolation |
| `wfe/render.py` | Text rendering of current node state |
| `wfe/persistence.py` | YAML save/load; round-trips all field/edge/node attributes |
| `wfe/template.py` | Template struct; instantiate() stamps template_id + label; default field values |
| `wfe/form.py` | draft/submit workflow for structured multi-field YAML input |
| `wfe/hooks.py` | Hook registry; fire() with parameterized hook names (name:p1:p2) |
| `wfe/builtin_hooks.py` | Engine hooks: init_target_graph, build_node_chain, save_workflow, save_template, compile_to_file; generic parameterized hooks: validate_field_in_db, lookup_entity_props, set_workspace, pull_from_workspace, load_workflow, extend_chain |
| `wfe/compile.py` | BFS traversal; scaffold nodes excluded; same-template → table; templateless → section |
| `wfe/database.py` | MockDatabase backed by db.json |
| `wfe/cli.py` | Stateless CLI; loads builtins then local workflow_hooks.py (if present) |
| `db.json` | Domain entity data: controlled_submodules, submodule_properties (cr_type, is_sdlc_governed) |
| `workflows/` | create-workflow.yaml, create-template.yaml, create-cr.yaml (routing wizard), cr-non-code.yaml, cr-code-no-submodule.yaml, cr-non-sdlc-submodule.yaml, cr-sdlc.yaml |
| `templates/` | ei.yaml (vr_required writable), commit-ei.yaml |
| `compiled/` | example-cr.md, create-cr.md |

---

## 4. Open QMS Documents

| Document | Status | Context |
|----------|--------|---------|
| CR-110 | IN_EXECUTION v1.1 | Workflow engine development. EI-1–4 Pass. EI-5 (RS update), EI-6 (push + pointer), EI-7 (post-exec) pending. |
| CR-107 | DRAFT v0.1 | Unified Document Lifecycle. On hold — superseded by engine. |
| CR-106 | DRAFT v0.1 | System Governance. Depends on CR-107. On hold. |
| CR-091-ADD-001-VAR-001 | PRE_APPROVED v1.0 | Type 2 VAR. VR title bug + SOP-004/TEMPLATE-VR alignment gap. |
| CR-001 | IN_EXECUTION v1.0 | Legacy. Candidate for cancellation. |
| CR-020 | DRAFT v0.1 | Legacy test document. Candidate for cancellation. |
| INV-002 through INV-006 | Various | Legacy investigations. Low priority. |
| CR-036-VAR-002, CR-036-VAR-004 | IN_EXECUTION v1.0 | Legacy. Low priority. |

---

## 5. Forward Plan

### Immediate: CR-110 EI-5, 6, 7

**EI-5 — Update SDLC-WFE-RS:** Add requirements discovered during development (all provisional):
- Multi-agent session isolation (`WFE_SESSION`, namespaced state under `.wfe/sessions/<id>/`)
- `nodelist` field type (YAML list-of-dicts for structured multi-node input)
- Form-based input (`wfe draft`, `wfe submit`)
- Hook system (register/dispatch, HookContext, HookResult, enter/exit/traverse hooks; parameterized names)
- Builtin hooks: engine construction hooks + generic parameterized domain hooks
- Template system (Template struct, instantiate(), template_id provenance, label, defaults)
- Compile feature (`wfe compile`, compile_graph(), BFS traversal, convention-based rendering)
- `Node.scaffold`: authoring-only nodes excluded from compiled output
- `Field.block`: paragraph-body display hint for compiled sections
- `Graph.reopen()`: COMMITTED → DRAFT for pre-approval revision
- First-principles authoring model: generated CR graphs start as DRAFT with blank fields
- CR type workflow templates (cr-non-code, cr-code-no-submodule, cr-non-sdlc-submodule, cr-sdlc)
- `db.json`: external domain entity data consumed by generic hooks

**EI-6 — Push submodule + update pointer:**
- Push all qms-workflow-engine commits to GitHub (head: `e5e3df4`)
- Update pipe-dream submodule pointer
- Commit pipe-dream

**EI-7 — Post-execution commit and route:**
- Final commit, route CR-110 for post-review
- QA reviews execution evidence

### Next Arc: QMS Workflow Integration (Post CR-110)

With the engine built (provisionally), the next questions are validation and integration:
- Does the create-cr wizard work in real QMS practice? (first real use will surface gaps)
- `create-var.yaml` — VAR authoring workflow
- Hook implementations for QMS MCP tools (route, approve, etc.) as traverse/exit hooks
- Decide whether WFE-authored CRs replace or supplement the existing QMS document flow

### On Hold: CR-107 / CR-106

Both superseded by the engine. May need cancellation or significant revision.

---

## 6. Backlog

### Ready (no blockers)

| Item | Effort | Source |
|------|--------|--------|
| Fix CLI title metadata propagation | Small | CR-091-ADD-001-VAR-001 |
| Align SOP-004 Section 9C.4 with TEMPLATE-VR | Small | CR-091-ADD-001-VAR-001 |
| Govern checkin.py bug fix (commit `532e630`) via CR | Trivial | INV-012 |
| Delete `.QMS-Docs/` | Trivial | CR-103 |
| Standardize metadata timestamps to UTC ISO 8601 | Small | Session-2026-02-26-001 |

### Bundleable

**Identity & Access Hardening** (~1 session) — proxy header validation, Git MCP access control
**Agent Hub Robustness** (~1-2 sessions) — C3 (root user), H4 (no hub shutdown on GUI exit), M6/M8/M9/M10
**GUI Polish** (~1-2 sessions) — H6, M3/M4/M5/M7, L3-L6

### Deferred

| Item | Rationale |
|------|-----------|
| Remove EFFECTIVE status / rename to APPROVED | High disruption, low value |
| Metadata injection into viewable rendition | No current pain point |
| Consolidate SDLC namespaces into system registry | Depends on CR-106 |
| Interactive document write protection (REQ-INT-023) | Deferred pending engine-based interaction design |
| Remove stdio transport option from MCP servers | Low priority |
| Propagate Quality Manual cleanup from workshop | Medium effort, not blocking |

---

## 7. Gaps & Risks

**WFE is experimental/provisional.** The engine and all domain content (create-cr, CR type templates, db.json) were built iteratively during CR-110 EI-4. SDLC-WFE-RS is DRAFT. No WFE workflow has been used in production QMS practice. Post-review (EI-7) and real-world use are required before treating any WFE artifact as stable.

**SDLC-WFE-RS needs EI-5 updates.** 30 cornerstone requirements written pre-implementation; significant capabilities added during development (hooks, templates, compile, form input, scaffold, block, reopen, builtin hooks, CR templates, db.json) are not yet formally captured.

**qms-workflow-engine has unpushed commits.** Head at `e5e3df4`; pipe-dream submodule pointer stale. Addressed in EI-6.

**Legacy QMS debt.** Nine open documents from early iterations. Bulk cleanup recommended.

**Container security.** C3 (root user) remains the last critical code review finding.

**CR-107/CR-106 stale.** Both on hold; interaction design content superseded by engine.

**checkin.py bug fix needs governance.** Commit `532e630` patched an `UnboundLocalError`. Needs a proper CR.
