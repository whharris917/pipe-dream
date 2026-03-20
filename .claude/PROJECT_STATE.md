# Project State

*Last updated: Session-2026-03-19-002 (2026-03-19)*

---

## 1. Where We Are Now

**Unified Workflow Engine with full-capability builder.** The WFE v2 Agent Portal runs on a single formalized runtime interpreting YAML workflow definitions. Supports three control-flow primitives beyond sequential: **router** (automatic conditional branching), **fork** (parallel paths), and **merge** (convergence). The **Create Workflow builder** can now author 100% of workflows the engine interprets — no hand-editing of YAML required.

**What's running now:** Flask web app at `http://127.0.0.1:5000` with:
- Sidebar navigation (Home, QMS, Workspace, Inbox, Templates, Workflow Sandbox, Quality Manual, Agent Portal, Workshop)
- Quality Manual browser with working cross-references
- Initiate Workflow page with decision tree + document creation buttons
- CR authoring form with all pre-approval sections
- Template Editor and Workflow Sandbox
- **Agent Portal** with unified workflow engine:
  - **Unified Runtime** (`runtime/`) — single engine interpreting YAML definitions
  - **3 built-in workflows**: Create CR, Create Executable Table, Create Workflow (builder)
  - **Custom workflows**: Published to `data/custom_workflows/`, discovered at startup (Create Deviation, Incident Response, Parallel Investigation, Comprehensive Change Assessment)
  - **Agent Observer** — 4 renderers (Simple light/dark × default/verbose) + 3 experimental + Raw. Simple is the new default (promoted from Experimental-D).
  - **Content primitives**: Fields (text/boolean/select/computed), Tables (7 column types, execution engine), Lists (add/edit/remove/reorder/focus)
  - **Control-flow primitives**: Sequential (proceed), Conditional navigation (when/target), Router (automatic multi-way), Fork (parallel branches), Merge (convergence)
  - **Execution engine**: Cell action lifecycle (fill/amend, sign/re-sign), cascade revert exemption, sequential issue numbering, node pause control
  - **Expression language**: Unified gates, visibility, acceptance criteria, navigation guards, router conditions, fork gates (AND/OR/NOT composites)
  - **Feedback model**: POST returns structured diff (outcome/new/modified fields + affordances)
  - **HATEOAS API**: Resource-oriented endpoints, parameterized affordances
  - **Builder**: Full engine parity — 44 actions authoring all primitives
- **Schematic Layout Engine** (`static/schematic.js`):
  - Unified pipeline: `definitionToSpine → flattenSpine → treeOrderLines → layout → renderHybrid`
  - Content-agnostic: callers provide `nodeRenderer(item, status)` callback returning arbitrary HTML
  - DOM measurement drives layout — nodes expand to fit any content
  - Node handles: `handleY` (fraction) or `handlePx` (fixed offset) control wire attachment point
  - Interactive collapse/expand: branch-points clickable to hide/show descendants (default on)
  - Auto-collapse: `focusNode` option shows only the path to the current node (used by workflow banner)
  - Gate nodes use inline SVG hexagons; split nodes use CSS border-radius + bars
  - Collapse-wire: dashed horizontal connector between collapsed branch-point and continuation
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

**ELK.js Integration + Banner Redesign** (Mar 15). Integrated ELK.js (Eclipse Layout Kernel) for the lifecycle banner — Sugiyama layered algorithm handles layer assignment, crossing minimization, and coordinate placement automatically. Banner uses horizontal layout with collapsed fork placeholders (branch labels stacked in dashed-border cards). Defined edge visual language: solid green (flow), dashed orange (router), dotted purple (goto), dotted blue (back). Full chart retains hand-rolled grid layout; banner delegates to ELK.

**Builder Full Engine Parity** (Mar 15). Rewrote `builder_handler.py` to close all gaps between the Create Workflow builder and the runtime engine. 44 actions (was 29): 15 new + 6 modified. Builder now authors option sets, column types, all 4 field types, dynamic options, side effects, computed fields, visible_when, lists with item_schema, tables with column_type_catalog, expression-tree gates, conditional navigation, pause/execution flags. Dogfooded by building and executing a 12-node Comprehensive Change Assessment workflow through the live API.

**Spine Model Schematic Renderer** (Mar 16). Designed a canonical representation for workflow topology: three recursive segment types (Step, Gate/OR, Split/AND). Built a canvas-based schematic renderer at `/workshop` using electrical schematic conventions. Monochrome palette with shape-based semantics: hexagons for decision gates, double-bar rectangles for parallel forks, rounded pills for steps. Dotted vertical bars for conditional branches, solid for parallel. Iterative layout engine with node-center convergence, per-label convergenceX maps, and even node spacing across branch spans. Five example workflows from simple sequential to deeply nested router-inside-fork. Established key structural guarantee: all branches must converge (every workflow bounded by final Close).

**Unified HTML-over-Canvas Rendering** (Mar 18). Replaced pure-canvas schematic rendering with `renderHybrid()` — nodes are real HTML divs positioned by the layout engine over a canvas that draws only topology wires/bars. Callers provide a `nodeRenderer(item, status)` callback returning arbitrary HTML. Two built-in renderers: compact pills (banner, standalone, workshop) and rich cards (detailed flowchart). CSS lives in `schematic.js`, injected once on first use. Measurement-first approach: DOM heights and widths measured in hidden container, injected into spine, layout adapts. Implicit sequential proceed targets resolved during definition serialization.

**Schematic Engine Hardening + Interactivity** (Mar 19). Comprehensive audit and refinement of the schematic layout engine. Removed vestigial height heuristics — DOM measurement is the sole source of truth. Replaced CSS clip-path gate hexagons with inline SVG polygons for correct stroke rendering. Fixed measurement/render context mismatch for fixed-width card layouts. Added node handle concept (`handleY`/`handlePx`) so wires attach at configurable points — detailed flowchart wires pass through card headers. Built interactive collapse/expand as an engine service: branch-points are clickable by default, spine pruning + re-render handled internally. Added `focusNode` auto-collapse for workflow banners — only the path to the current node is shown. Promoted Experimental-D to Simple renderer (new default). Removed old Simple and Schematic renderers. Added Workshop to sidebar navigation.

**Gate Condition Labels on Node Cards** (Mar 19). Fixed lossy gate serialization in `_serialize_definition()` — previously only `field_truthy` conditions were extracted into `requires`, silently dropping `table_has_columns`, `table_has_rows`, `field_equals`, `field_not_null`, and `set_membership`. Added `_gate_labels()` recursive walker that produces human-readable labels for all condition types and composites. OR gates join with ` or ` for semantic clarity. Card renderer now surfaces proceed gate requirements on workflow node cards.

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

### WFE v1 (Experimental/Provisional — being superseded)

CLI-based graph engine in `qms-workflow-engine/wfe/`. Functional but design replaced.

### WFE v2 — Unified Workflow Engine (Active)

| Component | Description |
|-----------|-------------|
| `wfe-ui/runtime/` | Unified workflow engine — interprets YAML definitions, implements handler protocol |
| `wfe-ui/runtime/schema.py` | Dataclasses: NodeDef, FieldDef, RouteDef, BranchDef, ForkDef, etc. |
| `wfe-ui/runtime/actions.py` | Action dispatcher — proceed, fork, route, switch_branch, merge |
| `wfe-ui/runtime/renderer.py` | Page renderer — affordances, fork state, definition serialization |
| `wfe-ui/runtime/evaluator.py` | Expression evaluator — AND/OR/NOT composites, field/table conditions |
| `wfe-ui/builder_handler.py` | Create Workflow meta-tool — full engine parity (44 actions) |
| `wfe-ui/engine/` | Table execution engine — PlanEngine, criteria evaluator, gating, locking |
| `wfe-ui/app.py` | Flask infrastructure — routes, SSE, feedback diffing, state persistence, discovery |
| `wfe-ui/static/schematic.js` | Schematic layout engine — spine model, renderHybrid, collapse/expand, focusNode |
| `wfe-ui/templates/agent_observer.html` | Agent Observer — Simple renderer (promoted from Exp-D) + 3 experimental + Raw |
| `wfe-ui/templates/workshop.html` | Interactive workshop — test harness for schematic rendering |
| `wfe-ui/data/custom_workflows/` | Published custom workflows (Create Deviation, Incident Response, Parallel Investigation, Comprehensive Change Assessment) |
| `wfe-ui/ENGINE.md` | Comprehensive engine reference documentation |
| `wfe-ui/TAXONOMY.md` | Taxonomy of workflow building blocks |

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

1. **ENGINE.md / TAXONOMY.md updates** — Document router, fork, merge primitives + builder expansion
2. **Flowchart scoping** — Full flowchart should only render for Create Workflow; add "View Workflow Diagram" to Agent Portal dashboard for other workflows
3. **Hot reload** — Endpoint to re-discover workflows without server restart
4. **Rate limiter fix** — Move before mutation or remove (see deviation report)
5. **SDLC-WFE-RS rewrite** — Requirements spec for v2 engine

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
| Fix rate limiter silent-drop bug | Small | Session-2026-03-14-003 deviation |

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

**v1 engine is in limbo.** Functional but being superseded. No clear deprecation plan yet.

**SOPs are being phased out.** The UI will eventually replace SOPs as the authoritative source of process knowledge. During transition, both exist.

**SDLC-WFE-RS needs full rewrite.** v1 requirements don't apply to the unified engine.

**Legacy QMS debt.** Nine open documents from early iterations. Bulk cleanup recommended.

**qms-workflow-engine submodule pointer** should be kept current with pushes.

**Rate limiter bug.** `_process_agent_action` rate limit fires after mutation, discarding successful state changes. Documented via Create Deviation workflow.

**ENGINE.md / TAXONOMY.md are stale.** Need updates to document router, fork, merge primitives + builder expansion.

**Exp-D flowchart over-renders.** Full flowchart currently renders for all workflows in the observer. Should only render for Create Workflow; others should access it via a dedicated "View Workflow Diagram" option.
