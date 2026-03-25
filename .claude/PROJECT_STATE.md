# Project State

*Last updated: Session-2026-03-25-001 (2026-03-25)*

---

## 1. Where We Are Now

**Clean-room rebuild of the Workflow Engine.** The previous engine (v2) has been deleted. A new foundation is being built from scratch on the `dev/content-model-unification` branch of qms-workflow-engine, based on the architectural plan from Session-2026-03-24-001.

**What's running now:** Minimal Flask app at `http://127.0.0.1:5000` with:
- Portal landing page with links to 3 demo pages
- **Eigenform architecture** — self-contained, self-rendering units of workflow interaction:
  - `Eigenform` base class: serialize() → JSON, render() → HTML, handle(body) → mutation
  - `TextForm`: single free-form string input with SetValueAffordance
  - `PageForm`: eigenform that contains and delegates to nested eigenforms
  - `Affordance` base class: serialize() → JSON, render() → interactive HTML (NotImplementedError enforced)
  - `Store`: JSON file persistence scoped by page/eigenform key
- **Self-sufficiency via bind()**: eigenforms bound to store/scope/url_prefix, then operate with zero-argument serialize()/render()/handle()
- **bind() returns copies**: definitions are templates, bind() produces independent instances via deepcopy
- **RESTful API**: GET /page/{id} → JSON, GET /page/{id}/view → HTML, POST /page/{id}/{key} → mutation + full page JSON
- **LNARF compliance**: JSON is canonical, HTML is faithful projection, purple "See JSON" buttons are human-only (exempt)
- **HATEOAS**: every eigenform carries affordances with explicit parameters, POST returns full page state

**Terminology:**
- **Eigenform** = self-contained unit (from German "eigen" = self)
- **Forms** = types: TextForm, BooleanForm, ChoiceForm, DisplayForm, MultiForm, TableForm, ListForm
- **PageForm** = container eigenform that delegates to children

**CR-110** is IN_EXECUTION (v1.1). EI-1-4 Pass. Remaining EIs (5-7) will need to be scoped to reflect the rebuild.

**65 CRs CLOSED. 5 INVs CLOSED.**

---

## 2. The Arc

**Foundation through Quality Manual** (Feb 1-24, CR-042 through CR-105).

**Workflow Engine v1** (Mar 3-7, CR-108 through CR-110). CLI-based graph engine. Proved concepts but revealed design limits.

**Workflow Engine v2 — UI-Driven Redesign** (Mar 8-12). Built a web UI and Agent Portal sandbox. Proved field-based and table-based workflow patterns. Four separate handler implementations.

**Unified Workflow Engine** (Mar 14). Clean-room rewrite formalizing the patterns discovered in v2. Single runtime replacing 4 handlers. Added lists, conditional navigation, dynamic options, side effects.

**Engine Hardening + Experimental Renderers + Parallel Execution** (Mar 15). Six architectural refinements, flowchart visualization, router/fork/merge primitives, builder full engine parity.

**Spine Model + Unified Rendering** (Mar 16-19). Canonical schematic representation, HTML-over-canvas rendering, DOM measurement, interactive collapse/expand, architecture formalization (LNARF).

**Repository Restructure + Documentation** (Mar 20). Removed v1 CLI engine. Restructured directories. Consolidated docs. AffordanceSource protocol + external state providers.

**Multi-Instance + LNARF Portal + Observer Simplification** (Mar 21). Transformed to multi-instance. Unified Renderer Principle. First page-specific LNARF renderer. Observer simplified to two modes. Interactive affordances. Faithful projection for all workflow pages. Agent API evaluation.

**Workshop + Focus Excision + Field Groups + Content Array** (Mar 22-23). Workshop experimentation, focus mechanism excision, renderer registry, field groups, unified content array, element type vocabulary, Element Library rebuild.

**Content Model Unification Plan** (Mar 24). Architectural audit of the engine. Developed comprehensive plan: one content array, one element protocol, one dispatch loop. Seven element types. Python-native definitions with JSON persistence. Four-phase implementation plan. Adversarial audit found and resolved 20 issues. YAML elimination decision.

**Clean-Room Rebuild** (Mar 25). Deleted all engine code. Built new foundation from scratch. Established Eigenform architecture: self-contained, self-rendering, self-sufficient units with bind() pattern. TextForm + PageForm + Affordance + Store. LNARF audit passed.

---

## 3. What's Built

### SDLC Document State

| Document | Version | Tests |
|----------|---------|-------|
| SDLC-QMS-RS | v22.0 EFFECTIVE | 143 requirements |
| SDLC-QMS-RTM | v27.0 EFFECTIVE | 687 tests, qualified commit 918984d |
| SDLC-CQ-RS | v2.0 EFFECTIVE | 6 requirements |
| SDLC-CQ-RTM | v2.0 EFFECTIVE | Inspection-based, qualified commit d3c34e5 |
| SDLC-WFE-RS | v0.1 DRAFT | 30 requirements (needs rewrite for v2) |
| Qualified Baseline | CLI-18.0 | qms-cli commit 309f217 (main) |

### Controlled Document State

| Document | Version |
|----------|---------|
| SOP-001 through SOP-007 | v21.0 / v16.0 / v3.0 / v9.0 / v7.0 / v5.0 / v2.0 EFFECTIVE |
| TEMPLATE-CR | v10.0 EFFECTIVE |
| TEMPLATE-VAR | v3.0 EFFECTIVE |
| TEMPLATE-ADD | v2.0 EFFECTIVE |
| TEMPLATE-VR | v3.0 EFFECTIVE |

### Workflow Engine — Clean-Room Rebuild (dev branch)

| Component | Description |
|-----------|-------------|
| `engine/eigenforms.py` | Eigenform base class + TextForm |
| `engine/affordances.py` | Affordance base class + SetValueAffordance |
| `engine/store.py` | JSON file store, scoped by page/key |
| `engine/page.py` | PageForm — container eigenform with delegation |
| `app/__init__.py` | Flask app factory |
| `app/routes.py` | Routes: GET JSON, GET /view HTML, POST mutation |
| `app/templates/` | Minimal templates (index.html, page.html) |
| `run.py` | Entry point |

---

## 4. Open QMS Documents

| Document | Status | Context |
|----------|--------|---------|
| CR-110 | IN_EXECUTION v1.1 | Workflow engine development. EI-1-4 Pass. |
| CR-107 | DRAFT v0.1 | Unified Document Lifecycle. On hold. |
| CR-106 | DRAFT v0.1 | System Governance. Depends on CR-107. On hold. |
| CR-091-ADD-001-VAR-001 | PRE_APPROVED v1.0 | Type 2 VAR. VR title bug + SOP-004/TEMPLATE-VR alignment gap. |
| CR-001 | IN_EXECUTION v1.0 | Legacy. Candidate for cancellation. |
| CR-020 | DRAFT v0.1 | Legacy test document. Candidate for cancellation. |
| INV-002 through INV-006 | Various | Legacy investigations. Low priority. |
| CR-036-VAR-002, CR-036-VAR-004 | IN_EXECUTION v1.0 | Legacy. Low priority. |

---

## 5. Forward Plan

### Immediate (Rebuild)

1. **Remaining eigenform types** — BooleanForm, ChoiceForm, DisplayForm, MultiForm, TableForm, ListForm
2. **Flow control** — ProceedDef, NavigationDef, RouterDef, ForkDef as page/node-level affordances
3. **Workflow definition** — Python-native WorkflowDef with nodes containing eigenforms
4. **Expression evaluator** — visible_when, gates, side_effects
5. **Builder** — Create Workflow via the engine itself

### CR-110 Remaining EIs

EI-5 (RS update), EI-6 (push + pointer), EI-7 (post-exec) remain valid. The RS will reflect the rebuilt engine.

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
| Interactive document write protection (REQ-INT-023) | Deferred pending UI-based interaction design |
| Remove stdio transport option from MCP servers | Low priority |
| Propagate Quality Manual cleanup from workshop | Medium effort, not blocking |

---

## 7. Gaps & Risks

**Engine is in rebuild.** The v2 engine code has been deleted on the dev branch. The old engine remains on main until the rebuild is ready to merge.

**SDLC-WFE-RS needs full rewrite.** v1 requirements don't apply to the rebuilt engine.

**Legacy QMS debt.** Nine open documents from early iterations. Bulk cleanup recommended.

**qms-workflow-engine submodule pointer** should be kept current with pushes.
