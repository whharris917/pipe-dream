# Session-2026-03-02-001

## Current State (last updated: 2026-03-02)
- **Active documents:** CR-107 (DRAFT v0.1, content v1.0), CR-106 (DRAFT v0.1, content v0.4)
- **Current task:** Interaction architecture — design substantially complete, ready to scope into CR-107
- **Blocking on:** Nothing major — section context annotation on nodes is the one open implementation question
- **Key decisions this session:** rendering pipeline fires after interaction complete; Python graph (3 dataclasses); metadata dict as workflow realization; section model; JSON-as-UI with `_`-prefix convention; engine is a wrapper for metadata JSON edits
- **Next:** Scope CR-107 EI revision, then route

## Progress Log

### Session Start
- Previous session: Session-2026-02-27-001 — frontmatter-driven interaction design, TEMPLATE-VR-v6, tool-free QMS insight. No decisions made.
- Reviewed PROJECT_STATE.md, previous session notes, QMS docs, inbox (empty)

### CR-107 Routing Decision
- Lead explained hesitation: skeptical of straining Jinja2 to handle interaction logic, document structure, AND workflow in a single template
- Lead affirmed: frontmatter-driven metadata approach is right for non-interactive docs (RTMs, SOPs). Interactive docs need something different.
- Agreed: one concrete CR-107 addition regardless of interaction design — change placeholder format from `{{placeholder}}` to `<<placeholder>>`

### Architecture Clarification (key insight)
- Lead articulated the unified pipeline: template (defines schema in frontmatter) + metadata JSON (.meta/) → Jinja2 → rendered document
- **Critical new principle:** This rendering pipeline fires ONLY after all interactive stages are complete
- Non-interactive docs have zero interactive stages — architecturally identical, just no interaction phase
- Unification: RTMs and VRs are the same system; the difference is interactive stage count
- Jinja2 body is clean — no conditionals about workflow state, just renders fully-populated data
- Lead confirmed: schema embeds the interaction spec directly (not a separate artifact)

### Interaction Spec Format Iterations
- Wrote TEMPLATE-VR-v7.md (session folder) — four design iterations:
  1. Staged linear spec (header/steps/conclusion blocks) — too verbose
  2. Concise field-as-key format — Lead found still too verbose; type field unnecessary
  3. Directed graph model — Lead's proposal: nodes, edges, prerequisites, pass-through nodes
  4. Graph with concise node definitions (field name = node id, implicit sequential next, backward edges create loops naturally)
- Graph model final structure: 13 nodes for full VR workflow. `stamp: true` for pass-through timestamp nodes. `values: [...]` implies enum. `yes:/no:` for branching. Loops emerge from backward edges.

### Two-File Separation Insight
- Lead recognized: struggling to find an elegant single-file solution may mean the single-file constraint is wrong
- Discussed: interaction graph and rendering template are genuinely different artifacts with different engines, different lifecycles, different audiences
- Two-file proposal: `TEMPLATE-VR.graph.yaml` (interaction graph) + `TEMPLATE-VR.md` (Jinja2 rendering template)
- Non-interactive docs have no `.graph.yaml` — go straight to rendering

### Text-Based UI Form Concept (key insight — Kneat eVal inspiration)
- Lead described 3+ hour car journey reflection on GMP controlled document execution
- Core insight: agents need a constrained interface where what can't be done isn't available — like Kneat eVal
- Problem with CLI: commands flashing by are opaque to a human watching Claude Code
- **Proposal: `.interact` file as a live text-based form** — agent and human see the same thing at all times
- The form shows: completed steps (locked, audit trail), current prompt, response region, action buttons
- Visual example designed (ASCII form with box-drawing characters, COMPLETED section, CURRENT section, RESPONSE box, SUBMIT button)
- Discussed agent perception: I parse semantic markers (<<placeholder>>, [ ], labels), not visual layout. Box-drawing is for human auditors.

### Interaction Mechanics Discussion
- Three options explored for agent interaction:
  - **Option 1:** Labeled elements + CLI commands (qms interact --click N) — solves corruption but returns to commands
  - **Option 2:** Human-readable form at top + JSON/YAML response region at bottom — good balance
  - **Option 3A/3B:** Full JSON form — loses human readability
- **My recommendation:** Option 2 with delimited plain-text regions (`=== field: BEGIN ===` / `=== field: END ===`) instead of JSON — handles multi-line prose, hard to corrupt, syntactically clear for agents
- Amend button discussed: doesn't belong on current unanswered prompt; belongs on completed items or via navigation
- Added `[ ← REVIEW PREVIOUS ]` navigation button alongside `[ SUBMIT ]`
- When activated: form rewrites to show completed steps in full with `[ AMEND ]` on each, plus `[ → RETURN ]`

### Should There Be a Database?
- Lead asked how current code handles cross-document queries (e.g., all Type-1 VARs of a CR)
- Code audit: current implementation uses glob patterns on `.meta/` directories — a filesystem scan
- Critical finding: Type-1 VAR closure gate is NOT implemented — CR can close with open Type-1 VARs
- Cascade close only handles attachment-type docs (VR); VARs have no discovery logic in close path
- Architecture term: "crash-only software" (Candea & Fox) / "durable execution" — no single canonical name
- Conclusion: SQLite as a derived index (files remain truth, index rebuilt from files on startup/demand)
- Stage gate complexity: gates can reference document fields, git state, cross-document joins, external CI
- SQLite makes gate conditions declarative queries vs. imperative file-crawl code

### Python Graph Framework
- Decision: pure Python, no DSL, no additional abstraction layer; modularity and composability key
- First sketch: over-engineered (GateContext, GateResult, StateNode, zoo of classes)
- Lead course-corrected: scale back, focus specifically on .interact file workflow graph
- **Minimal design: three dataclasses, no base class, duck typed**
  - `Prompt(id, text, next, values=[], commit=False)`
  - `Stamp(id, next)`
  - `Gate(id, text, routes: dict)`
- The graph IS the start node — no Graph container needed
- Factory functions for subgraphs (e.g., `make_step(exit_no)`) solve forward reference problem naturally
- Build graphs bottom-up (conclusion first, header last) to avoid forward references
- `VR_GRAPH = make_vr_graph()` at module level — static, instantiated once

### Metadata Dict as Workflow Realization
- Lead proposed: workflow "realized" as the document's metadata dict passed and mutated node to node
- Engine is completely stateless between runs: load dict from .meta/, walk graph to first absent node id, execute, write, save, stop
- Crash resilience is free — dict persisted after each node; engine resumes at same node on restart
- No cursor file needed — current node derived from dict contents
- Per-node mutations:
  - Prompt: `dict[node.id] = {value, author, timestamp}` (+ commit if flagged)
  - Stamp: `dict[node.id] = {timestamp, commit}`
  - Gate: `dict[node.id] = chosen_value`, routes on it

### Section Model vs Loop Model (key conceptual shift)
- Initial framing: step subgraph as loop with backward edge — "execute N times"
- **Lead's correction: the document has N steps — each step is a section instance, not a loop iteration**
- No backward edges — graph is a tree, not a cycle. Cleaner topology.
- Gate's "yes" branch appends a new step sub-dict to `dict["steps"]` and enters step template in that context
- Current step is always `dict["steps"][-1]`; step nodes write into current section sub-dict
- "Adding a step" = `dict["steps"].append({})`
- Structural annotation needed: nodes must know whether they write to root dict or current section sub-dict

### JSON-as-UI
- Brainstormed JSON as the `.interact` file format
- Core convention: `_`-prefixed fields are informational (regenerated by engine on every checkin), unprefixed fields are editable (agent fills in)
- Robustness property: engine regenerates entire `_` section on checkin — agent cannot corrupt it; only editable fields persist
- Normal prompt: `_prompt`, `_options` (if enum), `_completed` (history), `_actions_available` / editable: `response`, `action`
- Review mode: triggered by `action: "review_previous"` / editable: `amend_node`, `amend_value`, `amend_reason`, `action`
- Submission: agent sets `response` (to answer) OR `action` (for navigation/amendment) — never both

### Engine as Wrapper (key architectural insight)
- Lead observation: the .interact engine is nothing but a "wrapper" for making edits to the metadata JSON
- **The metadata JSON is the only durable artifact.** The `.interact` file is ephemeral — a controlled editing interface.
- Engine has two operations only:
  - **Render:** metadata JSON + current graph node → `.interact` JSON
  - **Commit:** agent edits to `.interact` → validate → write to metadata JSON → re-render
- Engine has no state of its own — current node derivable from metadata JSON by walking graph to first unfilled node
- Crash resilience is free: metadata JSON is durable, `.interact` file is always regenerable
- Interaction-complete condition: graph walk reaches terminal node → engine writes completion signal to metadata JSON → deletes `.interact` file → Jinja2 render pipeline fires
- `.interact` file disappearing IS the signal that interaction is done
- Non-interactive docs (RTMs, SOPs): no graph, no `.interact` file, no engine — checkin validates metadata JSON directly and triggers rendering. Same pipeline, zero interaction layer.

### Open Items
- How nodes declare section context (root dict vs. `steps[-1]`) — probably a simple attribute on Prompt/Stamp nodes in the step subgraph
- Whether SQLite index is in scope for CR-107 or a separate CR
- CR-107 EI revision needed to reflect new architecture before routing
