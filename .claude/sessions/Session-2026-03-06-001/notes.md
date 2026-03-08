# Session-2026-03-06-001

## Current State (last updated: 2026-03-08)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current EI:** EI-4 complete (all WFE development work); EI-5 (RS update), EI-6 (submodule push + pipe-dream pointer), EI-7 (post-exec commit) pending
- **Blocking on:** Nothing
- **Next:** EI-5 — update SDLC-WFE-RS with new requirements; then EI-6/7, route for post-review
- **Subagent IDs:** qa=a8e1bcbe1c60a3c5c (may need to respawn)
- **Framing note:** All WFE development (engine + domain content) is experimental/provisional pending RS update, post-review, and real QMS usage validation

## Progress Log

### Session Start
- Previous session: Session-2026-03-05-001
- Read SELF.md, PROJECT_STATE.md, previous session notes
- Read QMS-Policy, START_HERE, QMS-Glossary

### CR-109 (CLOSED)
- Fixed submodule count (4 not 2) + missing CLAUDE.md in Section 2.3
- Full lifecycle: pre-review -> pre-approval -> execution (6/6 EIs Pass) -> post-review -> post-approval -> CLOSED
- Key commits: baseline `26302a0`, repo `7731a8d`, execution `d474951`, closure `fefd882`

### CR-110 Drafted and Approved
- Workflow engine initial development CR
- Containment boundaries protect existing QMS
- QA pre-review: COMPLIANT (clean pass), pre-approval: APPROVED (v1.0)
- Released for execution

### CR-110 Execution
- EI-1: Pre-execution baseline commit `22cf37d`
- EI-2: Registered WFE SDLC namespace
- EI-3: Created SDLC-WFE-RS with 26 cornerstone requirements (7 categories)
- EI-4 (in progress): Built workflow engine implementation
  - graph.py: Slot, Node, Edge, Graph with lifecycle + construction + DAG invariant
  - session.py: Navigation (current node, go, home)
  - render.py: Text rendering of current node
  - persistence.py: YAML save/load
  - cli.py: Interactive REPL with all commands
  - Submodule commit `70054a4`, pipe-dream commit `07fabac`
  - All smoke tests pass (graph creation, construction, navigation, lifecycle guards, cycle detection, persistence)

### Usability Test
- Launched naive agent with minimal context ("there's a tool called wfe, figure it out")
- Agent prohibited from reading source code — can only interact with the CLI
- Testing: discoverability, intuitiveness, pain points
- Result: agent used REPL piping (wrong), then rebuilt CLI as stateless commands

### EI-5: SDLC-WFE-RS updated
- Checked out, added REQ-WFE-027 through REQ-WFE-030 (Section 4.8 Execution Mode)
- Revision summary updated; checked back in (v0.1)

### EI-4 Continued: Slot->Field rename + execution mode
- Renamed Slot->Field throughout: graph.py, persistence.py, render.py, cli.py, __init__.py
- YAML key "slots" -> "fields"; SDLC-WFE-RS updated via QMS checkout/checkin
- Added execution mode:
  - graph.py: fill_field(), evaluate_edges(), _condition_satisfied() (==, !=)
  - session.py: fill(), advance()
  - render.py: Execute section in committed mode
  - cli.py: wfe fill, wfe advance commands
- Submodule commit: 8c6c7b3
- Smoke tested: approval workflow with conditional edges, fill+advance navigates correctly

### Workflow Building Exploration (deleted)
- Read all SOPs (001-007) and all TEMPLATE/ files to understand CR/VAR structure
- Built 4 workflow YAMLs in workflows/: cr-base (14 nodes), cr-code (21 nodes), var-type1 (19 nodes), var-type2 (21 nodes)
- Lead asked whether code CR includes EIs -- identified design gap: execution phase nodes
  function as EIs but don't carry standard EI schema (task_outcome Pass/Fail, performed_by, date)
- Lead deleted the workflows; clarification on EI modeling approach pending
- Key design question: model each EI as a node with standardized fields, or treat the
  workflow as lifecycle-stage tracking with EIs living inside the document?

### Post-Compaction Work (2026-03-07)

**nodelist field type + form-based input:**
- New `nodelist` type for multi-node YAML input (list-of-dicts)
- wfe/form.py: draft/submit workflow — engine writes form.yaml with inline hints, agent edits, submits
- wfe draft + wfe submit commands in CLI
- Full semantic validation (template param checking, required field detection)

**create-workflow as prime mover (bootstrap redesign):**
- Removed redundant bare home node — first real node promoted to home via `Graph.set_home()`
- Replaced semicolon/bookend chain_template approach with `nodes: nodelist` field
- Two-pass build in `build_node_chain`: Pass 1 create all nodes → Pass 2 wire edges
- Supports both template-based (`template: ei`) and inline (`id: define, fields: [...]`) entries
- create-template workflow created via create-workflow using inline nodes (templates are derived)

**Multi-agent isolation:**
- WFE_SESSION env var namespaces all state under `.wfe/sessions/<id>/`
- `Session._make_ctx()` injects `_session_dir` into workspace for hooks

**compile feature:**
- wfe/compile.py: `compile_graph()` — BFS traversal, maps define/EI/done nodes to CR markdown
- Renders sections 1-9 from define node fields, section 10 execution table from EI nodes
- Partial execution supported: pending EI nodes show blank rows
- wfe compile [path] CLI command; compile_cr hook

**Artifacts committed (qms-workflow-engine `524d33c`):**
- wfe/hooks.py, wfe/template.py, wfe/database.py, wfe/form.py, wfe/compile.py
- workflow_hooks.py (build_node_chain, save_template, compile_cr, etc.)
- workflows/: create-workflow.yaml (hand-authored), create-template.yaml (engine-created), sample-ei-cr.yaml
- templates/: ei.yaml, commit-ei.yaml (both created via create-template)

**Reference CR studied:** CR-104 (qms init hardening, SDLC-QMS-RS v21.0, SDLC-QMS-RTM v26.0)

**compile redesign — subprocess/child workflow rendering + execution-awareness:**
- Edge.spawns_workflow, Node.child_workflows added to graph.py; round-tripped in persistence.py
- template.py: subprocess edges (spawns_workflow set) preserved even when symbolic target unresolved
- compile.py complete rewrite: execution-aware cell rendering ([EXECUTABLE]/[READY]/[BLOCKED]/N/A)
- Child Workflows column: actual instances link to compiled/ paths; potential pathways show conditions
- ei.yaml updated: var/vr subprocess edges with spawns_workflow annotations
- workflow_hooks.py: build_node_chain updated for inline spawns_workflow on edges
- example-cr.md updated showing correct subprocess rendering

**create-cr wizard workflow:**
- workflows/create-cr.yaml: branching question-driven wizard (7 nodes)
  - define → ask-code (yes/no) → ask-submodule (yes/no) → select-system → review-eis
  - review-eis → define-additional (if yes) → generate-cr → done
- New hooks in workflow_hooks.py:
  - capture_define_context, capture_code_answer, capture_submodule_answer
  - validate_submodule (checks CONTROLLED_SUBMODULES list)
  - check_sdlc_governance (SDLC_GOVERNED subset detection, writes to workspace)
  - populate_required_eis (enter hook: pre-fills required_eis based on workspace context)
  - build_cr_from_wizard (exit hook: generates workflows/{cr-id}.yaml + compiled/{cr-id}.md)
- Mock data: CONTROLLED_SUBMODULES = [flow-state, qms-cli, claude-qms, Quality-Manual, qms-workflow-engine]
             SDLC_GOVERNED = [flow-state, qms-cli, qms-workflow-engine]
- EI sets: non-code (2 EIs), non-SDLC submodule (4 EIs), SDLC (10 EIs)
- VR logic: vr_required=True only for EIs starting with "Implement"
- compiled/create-cr.md: compiled wizard representation (all [EXECUTABLE])
- End-to-end tested: all three paths verified correct

**CR-110 EI table updated:** EI-1 through EI-4 recorded as Pass. Checked in as v1.1.

**First-principles authoring model — scaffold nodes + block field:**
- `type = "text"` removed; replaced with `Field.block: bool` — explicit display hint, not a type annotation
- `Node.scaffold: bool` added — authoring-time nodes excluded from compiled output; compile BFS traverses them but skips rendering
- `Graph.reopen()` — transitions COMMITTED → DRAFT for pre-approval revision
- `create-cr.yaml` redesigned as routing-only wizard (asks code/submodule/system/needs_additional); no authoring content collected
- `build_cr_from_wizard` generates DRAFT CR graph with blank authoring fields; scaffold nodes for EI review/addition; idempotent `append_additional_eis` hook
- `capture_define_context`, `populate_required_eis` removed; replaced by `_build_base_eis` helper
- `compiled/create-cr.md` regenerated
- All 5 smoke tests pass

### Delete workflow_hooks.py (2026-03-08)
- `wfe/builtin_hooks.py` created: all generic engine hooks (init_target_graph, build_node_chain, save_workflow, save_template, compile_to_file, validate_field_in_db, lookup_entity_props, set_workspace, pull_from_workspace, load_workflow, extend_chain)
- `wfe/hooks.py`: fire() updated for parameterized hook names (name:p1:p2)
- `wfe/cli.py`: loads builtins before local hooks
- `db.json`: controlled_submodules + submodule_properties (is_sdlc_governed, cr_type)
- `templates/ei.yaml`: vr_required → writable field (was locked parameter)
- `workflows/cr-non-code.yaml`, `cr-code-no-submodule.yaml`, `cr-non-sdlc-submodule.yaml`, `cr-sdlc.yaml`: DRAFT CR type templates (2/4/4/10 EIs each)
- `workflows/create-cr.yaml`: rewritten as 5-node pure routing wizard; no domain hooks
- `workflow_hooks.py`: deleted
- Submodule commit: e5e3df4
- All smoke tests pass (parameterized dispatch, validate_field_in_db, lookup_entity_props, set_workspace, load_workflow, extend_chain, create-cr non-code path, create-cr SDLC path)

**compile redesign — pure convention renderer:**
- Realized first compile.py was domain-specific (CR section names baked in)
- Lead insight: same-template nodes project naturally to a table; this is the universal primitive
- Added `template_id: Optional[str]` to Node (set by instantiate(), round-tripped through YAML)
- Added `label: Optional[str]` to Node and Template (display name for compiled output)
  - prompt excluded from compile entirely — it's execution instruction, not document content
  - label: "Execution Items" added to ei.yaml; inline nodes accept `label:` key
- Rewrote compile.py: BFS traversal, group by template_id, tables for groups, sections for singletons
- Fallback: ID-derived label (snake → Title Case) when no label set
- Committed in qms-workflow-engine: d538b66 (template_id/compile), 435763c (label)
- Example output: qms-workflow-engine/compiled/example-cr.md
