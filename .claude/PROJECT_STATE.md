# Project State

*Last updated: Session-2026-03-21-003 (2026-03-21)*

---

## 1. Where We Are Now

**Unified Workflow Engine with external state provider framework.** The WFE v2 Agent Portal runs on a single formalized runtime interpreting YAML workflow definitions. Supports three control-flow primitives beyond sequential: **router** (automatic conditional branching), **fork** (parallel paths), and **merge** (convergence). The **Create Workflow builder** can author 100% of workflows the engine interprets. **External state providers** can now be plugged in — providers conform to the engine's affordance protocol and are referenced declaratively from YAML.

**What's running now:** Flask web app at `http://127.0.0.1:5000` with:
- Sidebar navigation (Home, QMS, Workspace, Inbox, Templates, Workflow Sandbox, Quality Manual, Agent Portal, Workshop)
- Quality Manual browser with working cross-references
- Initiate Workflow page with decision tree + document creation buttons
- CR authoring form with all pre-approval sections
- Template Editor and Workflow Sandbox
- **Agent Portal** with unified workflow engine:
  - **Unified Runtime** (`engine/runtime/`) — single engine interpreting YAML definitions
  - **3 built-in workflows**: Create CR, Create Executable Table, Create Workflow (builder)
  - **Custom workflows**: Published to `data/custom_workflows/`, discovered at startup (Create Deviation, Incident Response, Parallel Investigation, Comprehensive Change Assessment, Provider Test)
  - **Agent Observer** — 4 renderers (Simple light/dark × default/verbose) + 3 experimental + Raw
  - **Content primitives**: Fields (text/boolean/select/computed), Tables (7 column types, execution engine), Lists (add/edit/remove/reorder/focus)
  - **Control-flow primitives**: Sequential (proceed), Conditional navigation (when/target), Router (automatic multi-way), Fork (parallel branches), Merge (convergence)
  - **Execution engine**: Cell action lifecycle (fill/amend, sign/re-sign), cascade revert exemption, sequential issue numbering, node pause control
  - **Expression language**: Unified gates, visibility, acceptance criteria, navigation guards, router conditions, fork gates, **provider_state** conditions (AND/OR/NOT composites)
  - **Affordance generation**: Delegated via AffordanceSource protocol — each primitive answers "What is possible?" for itself; node collects and numbers
  - **External state providers**: ExternalStateProvider protocol (query/get_affordances/execute/evaluate), ProviderRegistry, workflow-level declaration with `$field_ref` bindings, node-level expose/affordances, dot-separated resource URLs (`ext.{provider}.{action}`)
  - **Feedback model**: POST returns structured diff (outcome/new/modified fields + affordances)
  - **HATEOAS API**: Resource-oriented endpoints, parameterized affordances
  - **Builder**: Full engine parity — 44 actions authoring all primitives
- **Schematic Layout Engine** (`app/static/schematic.js`):
  - Unified pipeline: `definitionToSpine → flattenSpine → treeOrderLines → layout → renderHybrid`
  - Content-agnostic: callers provide `nodeRenderer(item, status)` callback returning arbitrary HTML
  - DOM measurement drives layout — nodes expand to fit any content
  - Node handles: `handleY` (fraction) or `handlePx` (fixed offset) control wire attachment point
  - Interactive collapse/expand: branch-points clickable to hide/show descendants (default on)
  - Auto-collapse: `focusNode` option shows only the path to the current node (used by workflow banner)
  - Gate nodes use inline SVG hexagons; split nodes use CSS border-radius + bars
- **Workshop** (`/workshop`): Interactive test harness for spine model rendering with 8+ example workflows

**CR-110** is IN_EXECUTION (v1.1). EI-1-4 Pass. Remaining EIs (5-7) will need to be scoped to reflect the redesign pivot.

**65 CRs CLOSED. 5 INVs CLOSED.**

---

## 2. The Arc

**Foundation through Quality Manual** (Feb 1-24, CR-042 through CR-105).

**Workflow Engine v1** (Mar 3-7, CR-108 through CR-110). CLI-based graph engine. Proved concepts but revealed design limits.

**Workflow Engine v2 — UI-Driven Redesign** (Mar 8-12). Built a web UI and Agent Portal sandbox. Proved field-based and table-based workflow patterns. Four separate handler implementations.

**Unified Workflow Engine** (Mar 14). Clean-room rewrite formalizing the patterns discovered in v2. Single runtime replacing 4 handlers. Added lists, conditional navigation, dynamic options, side effects. Complex demo workflow (Incident Response) exercises all features. Comprehensive documentation (ENGINE.md, TAXONOMY.md).

**Engine Hardening** (Mar 15). Six architectural refinements from test-run feedback: node pause control, sequential issue numbering, cascade revert exemption, cell action lifecycle (fill/amend/re-sign), hierarchical renderer selection, unified cell highlighting. Blueprint renderer for workflow definitions. Removed lifecycle concept entirely — banner derived from node titles. Deep clean of all vestigial code.

**Experimental-D Visual Renderer** (Mar 15). Flowchart-style visualization of workflow definitions. Multiple iterations: HTML+CSS cards → SVG overlay → pure SVG (abandoned) → HTML cards with absolute positioning + SVG edge layer. Post-render height correction.

**Parallel Execution Primitives** (Mar 15). Three new control-flow primitives: router (automatic conditional branching), fork (parallel branch split), merge (implicit convergence). Complete rewrite of Exp-D renderer to grid-based layout with orthogonal-only edge routing. Builder extended to support authoring all three primitives. Demo workflow (Parallel Investigation) exercises router → fork → merge across three severity paths.

**ELK.js Integration + Banner Redesign** (Mar 15). Integrated ELK.js for lifecycle banner. Horizontal layout with collapsed fork placeholders. Edge visual language: solid green (flow), dashed orange (router), dotted purple (goto), dotted blue (back).

**Builder Full Engine Parity** (Mar 15). Rewrote `builder_handler.py` — 44 actions authoring all primitives. Dogfooded via 12-node Comprehensive Change Assessment workflow.

**Spine Model Schematic Renderer** (Mar 16). Canonical representation for workflow topology: three recursive segment types (Step, Gate/OR, Split/AND). Canvas-based renderer with electrical schematic conventions.

**Unified HTML-over-Canvas Rendering** (Mar 18). `renderHybrid()` — nodes are real HTML divs over canvas topology wires. Measurement-first approach.

**Schematic Engine Hardening + Interactivity** (Mar 19). DOM measurement as sole source of truth. Inline SVG gate polygons. Node handles. Interactive collapse/expand. `focusNode` auto-collapse. Promoted Experimental-D to Simple renderer (default).

**Gate Condition Labels on Node Cards** (Mar 19). Fixed lossy gate serialization. `_gate_labels()` recursive walker for all condition types.

**Architecture Formalization** (Mar 19). Core principle: **Lossless, Non-Additive, and Representationally Free**.

**Repository Restructure** (Mar 20). Removed v1 CLI engine (~5,174 lines). Restructured `wfe-ui/` into `engine/` + `app/`. Split `agent_observer.html` into 7 JS renderer files. Removed dead ELK.js code.

**Documentation Consolidation** (Mar 20). Consolidated three docs into two: README.md (user-facing intro/tutorial) and ENGINE.md (comprehensive technical reference absorbing TAXONOMY.md).

**AffordanceSource Protocol + External State Providers** (Mar 20). Refactored affordance generation from a 7-step monolith into recursive delegation — each primitive (field, list, navigation, proceed, fork, action, table, execution) implements `get_affordances()` and answers "What is possible?" for itself. Built the External State Provider framework on top: providers implement `ExternalStateProvider` protocol (query/get_affordances/execute/evaluate), register at application startup, and are referenced declaratively from workflow YAML. Providers are just another AffordanceSource — no special casing anywhere.

**Documentation + Builder Banner Unification + Condition Labels** (Mar 21). Updated ENGINE.md and README.md to document AffordanceSource protocol, external state providers, and provider_state conditions. Unified the Create Workflow builder's rendering with all other workflows — builder now uses the runtime's `_build_lifecycle()` and emits `banner_definition` for its own schematic banner. Auto-collapse now preserves first/last nodes for context. Condition labels on schematic diagrams are highlighted: green for taken router routes and active fork branches.

**Multi-Instance Workflows + Unified Renderer Architecture** (Mar 21). Transformed the engine from single-instance-per-type to multi-instance. Instance IDs are 8-char hex UUIDs. URLs now `/agent/{type}/{instance_id}/{resource}`. Dashboard redesigned as instance manager. Auto-migration of legacy state files. Established the **Unified Renderer Principle**: every page in the UI is a projection of agent-renderable state. The human HTML view and the Agent Observer are both renderers of the same `{state, instructions, affordances}` canonical representation. The Agent Observer becomes a "view mode" toggle on each page, not a separate URL. Sub-workflow embedding designed (plan saved) — blocked on unified renderer groundwork.

**LNARF Portal Renderer + Audit** (Mar 21). First page-specific renderer: Agent Portal. Human view is now a JS renderer (`portal.js`) projecting the canonical `{state, instructions, affordances}` GET payload — no hardcoded content in the template. Performed full LNARF audit: fixed 5 losses (affordance labels/IDs discarded, `state.page` dropped), 2 additions (`/observe` URL invention, API meta line). Content negotiation on `GET /agent/{wf_id}/{inst_id}` — same URL serves JSON or HTML observer. POST `/new` creates only (no navigation). Renamed `/reset` to `/delete`. Agent/human action parity enforced: every button traces to an affordance, every affordance has a button.

**Observer Simplification + Sidebar Integration** (Mar 21). Retired 3 experimental renderers (exp-a/b/c), dark theme, verbose mode — ~1,100 lines removed. Two renderers remain: Human (light) and Agent (raw JSON). Registry stripped from hierarchical format/verbosity/style system to simple two-mode toggle. Observer page now extends `base.html` — gains sidebar navigation. Purple border delineates renderer territory on both portal and observer pages. Consistent Human/Agent + Full/Feedback toggle buttons across all pages.

**Interactive Affordances + Error Rendering** (Mar 21). Human renderer now projects affordances as interactive controls: text inputs (pre-filled with current value), option buttons (highlighted active state), and dropdowns (for many/long options). Field affordances render inline with their fields; standalone actions (Proceed, Go back) render in a separate Actions bar. Error feedback renders as a red banner. Fixed annotated options bug — affordance parameters now emit raw values while field state keeps display annotations. Removed rate limiter. Fixed `wfEsc` to escape quotes in HTML attributes.

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

### Unified Workflow Engine (Active)

| Component | Description |
|-----------|-------------|
| `engine/runtime/` | Unified workflow engine — interprets YAML definitions, implements handler protocol |
| `engine/runtime/schema.py` | Dataclasses: NodeDef, FieldDef, RouteDef, BranchDef, ForkDef, ProviderDef, ProviderNodeDef, etc. |
| `engine/runtime/affordances.py` | AffordanceSource protocol — delegated affordance generation (FieldSource, ListSource, NavigationSource, ProceedSource, ForkSource, ActionSource, TableSource, ExecutionSource, ProviderSource) |
| `engine/runtime/providers.py` | ExternalStateProvider protocol, ProviderRegistry, binding resolution |
| `engine/runtime/actions.py` | Action dispatcher — proceed, fork, route, switch_branch, merge, provider_action |
| `engine/runtime/renderer.py` | Page renderer — state building, provider querying, field exposure, definition serialization |
| `engine/runtime/evaluator.py` | Expression evaluator — AND/OR/NOT composites, field/table/provider_state conditions |
| `engine/builder.py` | Create Workflow meta-tool — full engine parity (44 actions) |
| `engine/execution/` | Table execution engine — PlanEngine, criteria evaluator, gating, locking |
| `app/app.py` | Flask infrastructure — routes, SSE, feedback diffing, multi-instance state persistence, discovery, provider registration, content negotiation |
| `app/static/schematic.js` | Schematic layout engine — spine model, renderHybrid, collapse/expand, focusNode |
| `app/static/renderers/portal.js` | Portal renderer — LNARF-conforming projection of GET /agent payload |
| `app/templates/agent_observer.html` | Agent Observer — Human renderer + Agent (raw JSON), extends base.html |
| `app/templates/base.html` | Base template with view toggle (Agent View for SSE pages, Raw for renderer-driven pages) |
| `app/templates/agent.html` | Agent Portal — payload-driven template, loads portal renderer + Raw toggle |
| `app/templates/workshop.html` | Interactive workshop — test harness for schematic rendering |
| `data/custom_workflows/` | Published custom workflows (Create Deviation, Incident Response, Parallel Investigation, Comprehensive Change Assessment, Provider Test) |
| `docs/ENGINE.md` | Comprehensive engine reference documentation |
| `docs/FAITHFUL-PROJECTION.md` | Design document: faithful projection architecture for human-agent parity |

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

### Immediate

1. **LNARF renderers for remaining pages** — Extend the portal renderer pattern to workflow instance pages and other routes
2. **Sub-workflow embedding** — Nest workflows inside workflows (plan in session folder). Depends on multi-instance support (done).
3. **Hot reload** — Endpoint to re-discover workflows without server restart
4. **SDLC-WFE-RS rewrite** — Requirements spec for v2 engine
5. **Real provider implementation** — QMS provider bridging qms-cli into the workflow engine

### CR-110 Remaining EIs

EI-5 (RS update), EI-6 (push + pointer), EI-7 (post-exec) remain valid. The RS will reflect the unified engine.

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

**SOPs are being phased out.** The UI will eventually replace SOPs as the authoritative source of process knowledge. During transition, both exist.

**SDLC-WFE-RS needs full rewrite.** v1 requirements don't apply to the unified engine.

**Legacy QMS debt.** Nine open documents from early iterations. Bulk cleanup recommended.

**qms-workflow-engine submodule pointer** should be kept current with pushes.

**LNARF renderer rollout.** Portal page is LNARF-conforming with page-specific renderer. Workflow instance pages and other routes still use hardcoded templates.
