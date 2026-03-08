# Session-2026-03-08-001

## Current State (last updated: late session — post context compaction)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current task:** WFE UI — CR authoring workflow with staged persistence + Implementation Plan table builder
- **Blocking on:** Nothing
- **Next:** Continue Implementation Plan builder refinement; execution view; other document types
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

### UI Build
- Created `qms-workflow-engine/wfe-ui/` with Flask app
- Built base layout with sidebar navigation (Home, QMS, Workspace, Inbox, Quality Manual)
- **Quality Manual browser:** Renders actual markdown files from Quality-Manual/ with working cross-references (rewrites .md links to /manual/ routes)
- **Home page:** Project info cards + Quick Start with "Initiate Workflow" button
- **Initiate Workflow page:**
  - Interactive decision tree (client-side JS) for users who don't know what document they need
  - Direct "Create a Document" buttons for experienced users (CR, INV, SOP, Template)
  - Child document note explaining VARs/ADDs/VRs/ERs come from parent docs
- **Create Change Record form:** All pre-approval sections from SOP-002 §6 with authoring guidance:
  - Title, Purpose, Scope (Context/Changes Summary/Files Affected), Current State, Proposed State, Change Description, Justification, Impact Assessment (Files/Documents/Other), Testing Summary, Implementation Plan
  - No SOP references in UI — guidance stands on its own

### CR Authoring Workflow (post-compaction)
- **Staged workflow:** Initiation → Change Definition, with persistence to JSON in `wfe-ui/data/`
- **Initiation stage:** Title, Code Impact decision tree (affects code → controlled submodule → which one → SDLC indicator), Purpose. "Initiate Change Record" assigns CR ID.
- **Change Definition stage:** All fields visible/editable, incremental saves (no `required` on definition fields)
- **Stage banner:** Full 8-stage progress indicator: Initiation → Change Definition → Pre-Review → Pre-Approval → Execution → Post-Review → Post-Approval → Closure
- **QMS page:** Table view of all documents with ID, title, stage tag
- **Workspace page:** Card view of active documents with purpose snippet
- **Implementation Plan:** Dedicated page (`/cr/<id>/plan`) with full table builder:
  - Add/delete rows and columns, insert relative to selection
  - Column types: Non-Executable (Free Text, Prerequisite) and Executable (Free Text, Choice List, Cross Reference, Signature)
  - Choice List type has inline options editor in the type picker dropdown
  - Executable columns render as locked/grey cells (not editable during authoring)
  - Prerequisite columns show a checkbox dropdown picker listing all other rows as EI-N
  - Auto-Sequential action fills prerequisites as a linear chain (each row depends on previous)
  - Tab navigation between cells, Escape to close dropdowns
  - Save persists to JSON via POST, "Saved" flash confirmation

### Files Created/Modified
- `qms-workflow-engine/wfe-ui/app.py` — Flask app: routes, persistence helpers, Quality Manual renderer
- `qms-workflow-engine/wfe-ui/templates/base.html` — Layout with sidebar
- `qms-workflow-engine/wfe-ui/templates/index.html` — Home page
- `qms-workflow-engine/wfe-ui/templates/qms.html` — Document table view
- `qms-workflow-engine/wfe-ui/templates/workspace.html` — Active document cards
- `qms-workflow-engine/wfe-ui/templates/inbox.html` — Placeholder
- `qms-workflow-engine/wfe-ui/templates/manual_index.html` — Quality Manual index
- `qms-workflow-engine/wfe-ui/templates/manual_page.html` — Quality Manual page viewer
- `qms-workflow-engine/wfe-ui/templates/initiate.html` — Initiate workflow with decision tree
- `qms-workflow-engine/wfe-ui/templates/create_cr.html` — Staged CR authoring form
- `qms-workflow-engine/wfe-ui/templates/edit_plan.html` — Implementation Plan table builder
- `qms-workflow-engine/wfe-ui/.gitignore` — Excludes `data/` directory
- `qms-workflow-engine/wfe-ui/static/` — Empty (CSS is inline for now)
