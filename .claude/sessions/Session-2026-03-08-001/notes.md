# Session-2026-03-08-001

## Current State (last updated: mid-session — Workflow Sandbox build)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current task:** WFE UI — Workflow Sandbox interactive graph builder
- **Blocking on:** Nothing
- **Next:** Right-click actions on annotation symbols; Source tab compiler; node/edge property editing
- **Subagent IDs:** None active

## Key Decision: UI-Driven Redesign

The Lead decided to pivot from abstract engine redesign to building a **Kneat-like web UI** that will drive the engine's development. The reasoning: visual, concrete progress is more productive than abstract design discussions.

**Strategic shift:** The WFE UI is now the primary development artifact. The engine primitives will be rebuilt to serve what the UI needs, not the other way around. All work remains within CR-110 scope — same authorized sandbox repo, same objective.

## Design Discussion Summary

Identified fundamental problems with v1 engine:
1. **Context gap:** Engine provides structure but not knowledge — prompts are one-line labels, not real instructions
2. **Phase tangle:** Authoring, execution, and rendering conflated — scaffold nodes, block fields, meta-workflows
3. **Meta-workflows are wrong pattern:** Using workflows to build other workflows creates phase confusion; authoring should be guided by canvas/template prompts, not by executing a separate workflow

Established revised principles:
- P1: Workflow is a DAG of steps with typed data slots and conditional edges
- P2: Templates define reusable step patterns with **enforcement rules** (can add, can't delete)
- P3: Execution is filling slots and advancing; graph gates progression
- P4: Filled graph IS the document; rendering is pure function of graph state (no scaffold/hidden nodes)
- P5: Guidance is layered — canvas guidance (author), authoring guidance (per template), execution guidance (per step)

**Important context from Lead:** SOPs are being phased out — the UI will eventually replace them as the authoritative source of process knowledge. Don't reference SOPs directly in UI.

Full design document: `wfe-redesign.md` in this session folder.

## Progress Log

### Session Start
- New session: Session-2026-03-08-001
- Read previous session notes (2026-03-07-001), PROJECT_STATE, QMS docs, SELF.md

### Design Discussion
- Long discussion about WFE v1 shortcomings
- Established revised design principles
- Wrote `wfe-redesign.md` design document

### UI Build — Core Pages
- Created `qms-workflow-engine/wfe-ui/` with Flask app
- Built base layout with sidebar navigation (Home, QMS, Workspace, Inbox, Quality Manual)
- **Quality Manual browser:** Renders actual markdown files from Quality-Manual/ with working cross-references
- **Home page:** Project info cards + Quick Start with "Initiate Workflow" button
- **Initiate Workflow page:** Interactive decision tree + direct document creation
- **Create Change Record form:** All pre-approval sections with authoring guidance
- **CR Authoring Workflow:** Staged: Initiation → Change Definition, with JSON persistence
- **QMS page:** Table view of all documents
- **Workspace page:** Card view of active documents
- **Implementation Plan:** Dedicated page with full table builder (add/delete rows/cols, column types, choice list, prerequisites, auto-sequential, save)

### Engine API Migration (post-compaction #1)
- Migrated remaining client-side business logic (markNA, initiateIssue, toggleHistory) to server-backed API
- Made execution state ephemeral (in-memory dict, not persisted to disk)
- Fixed audit trail history not updating immediately after changes
- Fixed cascading revert bug when Sequential Column Execution enabled
- Deleted CR-002 test data

### Template/Workflow Architecture (post-compaction #2)
- Conceptual reframing: Templates = pure data schema; Workflows = process state machine referencing template fields
- Created `CR.template.yaml` — field definitions organized by semantic category
- Created `CR.workflow.yaml` — 8-stage process: initiation → closure, with actors, field visibility/editability per stage, gates, actions, hooks
- **Template List page** (`/templates`) — catalog of document type templates
- **Unified Document Type Editor** (`/template/<slug>`) — two-tab interface:
  - Template tab: field list + form preview
  - Workflow tab: interactive SVG flow graph (nodes color-coded by actor, Bezier edges with arrow transitions, action branches as dashed curves) + stage-aware preview panel
  - Click node to select for preview; double-click to edit stage
  - Field editor modal, stage editor modal with field inclusion checklist
  - Save persists both template and workflow YAML

### Workflow Sandbox (current work)
- Added **Workflow Sandbox** page (`/sandbox`) with sidebar link
- Two-tab container: **Source** (empty — will hold live YAML later) and **Interactive Editor**
- Built interactive drag-and-drop graph builder:
  - **Nodes:** Add via toolbar button or right-click canvas; single-click header to rename
  - **Fields on nodes:** "+ New Field" button inside each node; inline text input for naming; type badge (color-coded); pencil icon opens properties popover (name, type: String/Text/Boolean/Enum/Number/Date/Signature, delete)
  - **Dynamic node height:** Nodes grow as fields are added
  - **Edges:** Drag from output port (bottom) to input port (top) of another node
  - **Auto-layout:** Full topological layered layout with smooth 300ms animated transitions (ease-in-out quadratic); dynamic gap expansion for edge annotations and tall nodes
  - **Right-click context menus:**
    - Canvas → "Add Node"
    - Node → "Add Connected Node" (creates node + edge in one action)
    - Edge → "Add Condition" / "Add Hook"
  - **Edge annotations inline with flow:**
    - Condition = orange diamond with "?" and "GATE" label, centered ON the edge path
    - Hook = blue rounded square with lightning bolt and "HOOK" label, centered ON the edge path
    - Edge segments split around symbols so control flow visually passes *through* them
    - Auto-layout expands gap between layers to accommodate annotations
  - **Selection:** Click node or edge to select (blue highlight); click canvas to deselect
  - **Edge hit targets:** Wide invisible stroke for easy clicking

### Design Document Refinements (post-compaction #3)
- **"The Form Is Not the Workflow Step"** — The form (data slots) is a noun; the workflow step (instruction to an actor) is a verb. Every stage needs an explicit instruction distinct from its field list. This is the context gap at granular level.
- **Worked Example: Implementation Plan** — Resolved earlier confusion. The plan stage is just a stage with a rich instruction + fields (the table). The preceding gate resolves classification, so the instruction can be direct rather than conditional. Protected template EIs prevent omission.
- **"The Plan Table Is a Workflow Graph"** — Rows=nodes, prerequisites=edges, sequential execution=topological constraint, audit trail=execution history, cascading revert=downstream re-evaluation. The CR workflow is recursive: it contains a nested workflow in tabular notation.
- **"One Format for All Tables"** — The YAML workflow format serves triple duty: process graphs, nested sub-graphs (tables), and templates. No separate table schema needed.
- **"Table Features Are Graph Features"** — Audit trail, cascading revert, field execution categories (non-executable/executable/auto-executed), category sequencing — all belong on engine primitives, not on a table widget. One execution semantics, two renderers.
- **Edge Cases: Minimum Templates and Minimum Workflows** — Minimum template = just fields + default lifecycle (e.g., a memo). Minimum workflow = no template needed (e.g., decision tree, guidance walkthrough). Workflows will proliferate far more than templates — they are the unit of reusable process intelligence, replacing SOPs.

### Key Architectural Insight: Workflow as Constraint Machine
- The UI is not a convenience layer on the CLI — it IS the primary process interface for both humans and agents
- Three layers identified: Document Lifecycle (CLI), Process Definition (workflow graph), Process Interface (UI/agent API)
- The CLI is insufficient for agents because it lacks the instructional, prompt-guiding, constraint-enforcing layer
- The Sandbox builds an **executable constraint machine**, not a diagram — nodes/edges/gates/hooks are the program
- Agent interaction model: query scoped state → receive only permitted affordances → work within bounds → request transition → engine evaluates gate
- Non-compliance is structurally impossible, not behaviorally discouraged
- Formalized in `workflow-as-constraint-machine.md`

### Files Created/Modified
- `wfe-ui/app.py` — Added template editor routes, sandbox route, workflow listing
- `wfe-ui/templates/base.html` — Added Templates and Workflow Sandbox sidebar links
- `wfe-ui/templates/template_list.html` — Template catalog with create dialog
- `wfe-ui/templates/template_editor.html` — Unified document type editor (template + workflow tabs)
- `wfe-ui/templates/sandbox.html` — Workflow Sandbox with interactive graph builder
- `wfe-ui/templates/doctypes/CR.template.yaml` — CR data schema
- `wfe-ui/templates/doctypes/CR.workflow.yaml` — CR workflow process schema
- `wfe-ui/templates/initiate.html` — Added workflow catalog section
- `wfe-ui/api.py` — Ephemeral execution state
- `wfe-ui/engine/persistence.py` — Simplified (removed execution state persistence)
- `wfe-ui/engine/__init__.py` — Updated exports
- `.claude/sessions/Session-2026-03-08-001/workflow-as-constraint-machine.md` — Architectural insight document
