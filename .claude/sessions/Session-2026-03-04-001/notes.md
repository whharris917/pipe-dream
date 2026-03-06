# Session-2026-03-04-001

## Current State (last updated: 2026-03-05 post-prototype-sprint)
- **Active document:** CR-108 (IN_EXECUTION v1.1, checked out)
- **Current EI:** EI-3 (RS + prototyping — massive prototype sprint complete)
- **Blocking on:** Nothing — awaiting Lead review of prototype
- **Next:** Lead demo of prototype; incorporate Round 2 usability feedback

## Progress Log

### Session Start
- Previous session: Session-2026-03-03-002 — massive DocuBuilder prototype session
  - 20 usability tests (all passing), RS with 35+ requirements
  - Full prototype: model.py, renderer.py, commands.py, engine.py
  - Key features: enforce/locked model, prerequisite blocking, sequential cascade, inspect, column modes, checkout/edit/checkin workflow
  - Remaining RS items: calculated columns, section visibility, work instructions, cross-document refs, property namespaces, duplicatable sections, amendability flag
- CR-108 IN_EXECUTION v1.1, checked out
- Inbox empty

### Design Discussion: Document-Centric → Workflow-Centric Reframing
- Lead identified core tension: DocuBuilder is a workflow engine wearing document editor clothes
- Key reframes discussed:
  - Documents are forms, not prose — all QMS docs are structured field completion
  - No sections needed — flat sequence of steps, no navigation overhead
  - Tables are step sequences, not data grids
  - "Authoring" = workflow design, "execution" = workflow completion
  - Templates are workflow definitions, not document blueprints
- Lead asked to ground on concrete problem: read CR-106, CR-107, SOP-005, TEMPLATE-CR
- Discussed template inheritance: base CR template with invariant bookend steps, specialized types extend without overriding
- Lead requested comprehensive research and design document

### Major Research Effort: Unified Workflow Engine Design
- Launched 5 parallel research agents:
  1. All 12+ SOPs, type refs, guides — complete state machine mapping
  2. Non-trivial CRs (CR-036/5 VARs, CR-056/3 VARs, CR-091/ADD+VR), all 14 INVs
  3. External research: BPMN, Temporal.io, Dagster, XState, Petri nets, GMP EBR, 21 CFR Part 11, ALCOA+, van der Aalst patterns, AWS Step Functions
  4. All 9 QMS templates, audit trail analysis (6 case studies)
  5. DocuBuilder prototype analysis (strengths, limitations, reframing opportunities)

### Design Document Created
- `.claude/sessions/Session-2026-03-04-001/workflow-engine-design.md`
- 14 sections covering:
  - Problem statement grounded in real QMS failures (INV-009, INV-010, INV-012, INV-014)
  - Research synthesis from 10+ external systems
  - 8 design principles (P1-P8)
  - 5 core primitives: WorkflowTemplate, WorkflowInstance, Step, Gate, Signal
  - Step anatomy with gates, outputs, evidence schema
  - Template inheritance: executable-base → code-cr → template-cr (3 levels)
  - Multi-workflow orchestration with lifecycle policies
  - SDLC coordination as gate-enforced signal chain
  - Deviation handling (inline minor / child workflow major)
  - Rendered view design for AI agent interaction
  - Current → Proposed mapping table
  - 6 open questions with recommendations
  - Migration path (6 phases, incremental)
  - Integration with CR-107 and CR-106

### Template/Instance Clarification (Lead feedback)
- Lead clarified critical distinction: templates vs instances made from templates
- Template-defined steps are inherited and CANNOT be deleted during instance drafting
- Author CAN add custom steps during drafting
- Pre-approval freezes the complete step list (template + author steps)
- Execution phase: only evidence fields writable, no structural changes
- Updated design document: Section 4.6 (Three-Layer Model), Section 8.3 (phase-specific commands), Section 9 (Instance Drafting rules), Q2 resolved
- Each step carries `source: template` or `source: author` provenance

### Session notes and PROJECT_STATE updated

### Design Principles P9 and P10 Added
- P9: The System Carries Process Knowledge, the Agent Carries Domain Knowledge
  - Agents should never need to read SOPs or memorize template conventions
  - The system tells the agent what to do next; the agent just does the work
- P10: One Interaction Model, All Layers (The Bootstrap Principle)
  - The prompting system IS a workflow — the bootstrap workflow that creates all other workflows
  - Template authoring, instance drafting, and execution all use the same pattern: answer the next prompt
  - Three-layer recursion: bootstrap → templates → instances

### Grand Unification: The QMS Graph
- Lead's breakthrough insight: the entire QMS is a single graph
- Tickets are cursors with notebooks traversing the graph
- Nodes supply prompts like a third rail supplies power to a train
- The cursor is also a construction vehicle — can lay down and modify nodes (with approval)
- Created new design document: `qms-graph-design.md` (supersedes workflow-engine-design.md)
- 11 sections: insight, graph structure, tickets, third rail, concurrent actors, construction vehicle, concept mapping, rendered view, open questions, pitch, relationship to prior work

### Deep Analysis of Open Questions
- Q1 RESOLVED: Hybrid storage (Python infrastructure + YAML/JSON template data)
- Q2 RESOLVED: No bare tickets — start region is navigation session, ticket created at document subgraph entry with identity
- Q3 RESOLVED: Delegation model (primary cursor + task cursors), not forking
- Q4 RESOLVED: Graph versioning = git versioning, no separate version tracking
- Q5 RESOLVED: Markdown is export format, ticket + graph is source of truth
- Q6 RESOLVED: Direct evolution of qms_interact
- Q7 RESOLVED: Clean break with bridge period for in-flight documents
- Q8 NEW: How does the start region work mechanically? (preliminary: lightweight/ephemeral traversal mode)
- Q9 NEW: Extension point flexibility in templates (preliminary: designated positions, multiple per template)
- Q10 NEW: Evidence schema language (preliminary: start minimal — text, enum, bool, doc_id)
- Updated construction vehicle section: two levels (local extension for instance drafting, permanent modification for template authoring)
- Ticket-scoped nodes concept: custom EIs exist only for their ticket, uniform traversal by engine

### File-Based Schema Option
- Lead asked about advantages of defining graph entirely via files (not Python code)
- Significant advantages identified: universal construction vehicle, browsable graph, human-readable git diffs, shrinks bootstrap base case
- Added as Option B alongside Option A (hybrid) in design document Section 2.1
- Q1 reopened as unsettled design decision

### Hooks and Boundary Principle
- Lead identified hooks as missing graph element
- Established hook boundary: hooks automate what agent COULD do (CLI/bash), NOT engine internals
- Three-category ownership: Engine (traversal/audit) / CLI (doc lifecycle with side effects) / Hooks (agent-level commands)
- Archive-on-supersede is checkin side effect, not a hook
- Added Section 2.5 to qms-graph-design.md

### QMS Graph Prototype Created
- `qms-graph-prototype/graph-viewer.py` — interactive graph traversal tool (~300 lines)
  - Loads YAML node files from directory, renders agent view with ANSI colors
  - Features: evidence schema validation, conditional edges, loop support, hook display
- `qms-graph-prototype/build-template/` — 13 YAML node files demonstrating:
  - Sequential flow, enum branching, loops (add-another → step-name)
  - Bool types, optional fields, hooks, conditional paths, review/revise branching
- Fixed YAML boolean parsing bug: `[yes, no]` → `["yes", "no"]` (4 files)
- End-to-end test successful (piped input traversal from start to submit)

### Three Independent Design Reviews (agents)
- Usability agent: praised prompt-driven model, recommended progress indicators, undo/back support
- Efficiency agent: confirmed minimal implementation, flagged potential over-engineering risks
- Self-improvement agent: praised recursive nature, recommended meta-metrics and reflection hooks

### Autonomous Sprint: Prototype Buildout (Lead at gym)
- **Engine v2** (`engine.py`): Upgraded with GraphMetadata, `_graph.yaml` loading, `required_when` conditional fields, improved WAIT node handling, ticket serialization
- **CR lifecycle** (31 nodes): Full lifecycle from create through closure, with deviation handling, rejection loops, scope revision, child document gates
- **INV lifecycle** (26 nodes): Full investigation with RCA, CAPAs, child CRs, post-review
- **Review-approval** (8 nodes): Reusable review/approval cycle pattern
- **Deviation handling** (8 nodes): Decision tree routing to VAR, ER, or INV
- **Test harness** (`test-harness.py`): 19 automated scenarios, all passing
- **`_graph.yaml` metadata**: Added to all 5 subgraphs — discoverability, relationships, reviewer guides
- **Round 1 usability testing**: Cold-start agent scored 7.4/10; top issues: gate expressions, WAIT ambiguity, missing metadata
- **Fixes applied**: `required_when`, improved WAIT messaging, reviewer guide in context, loop-control context
- **Round 2 usability testing**: Launched (pending)
- **DEMO.md**: Created with quick-start guide, architecture overview, test results

### YAML Key Ordering Bug Fix (qms-graph-prototype)
- `sort_keys=False` added to all 4 `yaml.dump()` calls in `generate.py`
- Without this, YAML alphabetically reorders evidence_schema keys, causing hint misassignment during instance generation

### Continuation Node Elimination (qms-graph-prototype)
- Removed `more-fields.yaml` and `more-edges.yaml` from meta-workflow
- Replaced with count-driven auto-loops using `visits_since()` and `last_response()` helpers
- Added `int`, `str`, `len`, `bool` to safe eval namespace (builtins stripped by `__builtins__: {}`)
- Eliminated 32 of 40 continuation prompts

### Template Enforcement Design: The Copernican Insight
- Recognized that a single unified graph was causing convoluted accounting (epicycles)
- Key insight: Templates, derived templates, and documents are ALL separate graphs
- Operations produce new graphs from existing graphs; the engine just traverses
- One enforcement field (`locked: true`), two build operations (`extend`, `instantiate`)
- Design document: `qms-graph-prototype/graph-template-design.md`

### Python vs YAML Design Decision
- Produced comparison across 12 dimensions: `qms-graph-prototype-2/design-comparison.md`
- Recommendation: Use Python for template definition, JSON for document serialization
- Key rationale: "Inheritance is the hard problem, and Python solves it natively"

### qms-graph-prototype-2: Python Template Prototype (30-minute sprint)
- Built complete prototype using Python class inheritance for templates
- **graph.py** (~325 lines): Field, Node, Graph, _GraphBuilder, Template base class
  - `fill()` mechanism: parent calls `self.fill(g, "name")`, child overrides `define_name()`
  - Auto-linear edges with conditional edge merging
  - `instantiate()` locks template nodes, fill nodes stay unlocked
  - `freeze()` locks everything (pre-approval transition)
  - Deep diff: compares prompts, context, performer, terminal, gate, schema, edge targets
- **engine.py** (~570 lines): Ticket, Evaluator, CLI, document I/O
  - Gate conditions: nodes block advancement unless response satisfies gate expression
  - Completed document rejection
  - Extra field warnings
  - Inline response CLI (`--response '{"key": "val"}'`)
  - Progress indicator (`total_nodes` in status)
- **7 templates** (5 hand-built, 2 agent-created):
  - ProcedureBase (abstract) → Diagnostic → Incident → SafetyIncident (4-level chain)
  - ProcedureBase → Repair
  - ProcedureBase → CodeReview (agent-created)
  - LogicPuzzle (standalone)
- **117 automated tests**, all passing
- **5 agent usability rounds**:
  1. Cold-start traversal (8/10, system highly usable from scratch)
  2. Template creation (CodeReview — intuitive, Python inheritance is right call)
  3. Template extension (SafetyIncident — 4-level chain worked, `super()` resolved correctly)
  4. Validation/diff (found 10 gaps, 2 high severity — both fixed)
  5. Final validation (5/6 pass, 3 minor findings — all fixed)
- **Iterative fixes applied**:
  - Template class loader: fixed abstract attribute inheritance, module-level filtering
  - Edge builder: merges explicit conditional edges with auto-linear fallthrough
  - Gate conditions on ProcedureBase start/verify and Incident start/verify
  - Diagnostic hypothesis loop-back (test → hypothesize when hypothesis_confirmed != "yes")
  - Incident correctly inherits loop-back (test → hypothesize, forward → contain)
