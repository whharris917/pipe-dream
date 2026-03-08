# Session-2026-03-07-001

## Current State (last updated: Step 1 complete)
- **Active document:** CR-110 (IN_EXECUTION v1.0)
- **Current task:** Step 1 complete — engine built and create-workflow works end-to-end
- **Blocking on:** Nothing
- **Next:** Step 2 — use create-workflow to build other workflows (ei-template already exists; build create-cr, create-var, etc.)
- **Subagent IDs:** None active

## Design Decisions Made This Session

See `workflow-engine-design-v2.md` for full design document. Key decisions:

1. **Everything is graph execution** — one verb, no phase distinction at engine level
2. **EIs as nodes** — central purpose of the engine; EIs are nodes with standard field structure
3. **Prerequisites = incoming edges** — graph topology encodes prerequisites
4. **Edge conditions over topology variation** — VR/VAR edges always exist; field conditions drive traversal
5. **Uniform EI template** — all EIs identical structure; `commit-ei` is a fixed-parameter variant
6. **Template execution = instantiation** — authoring IS executing templates; output is execution graph
7. **Hooks** — enter-node, exit-node, traverse-edge triggers; can block operations; integrate with external state
8. **Mock database** — JSON file in qms-workflow-engine/; hooks read/write; seam for real QMS later
9. **Bootstrap strategy** — Step 1: minimal engine + hand-authored create-workflow; Step 2: build everything else using create-workflow

### Architecture clarifications (this session):
10. **Engine is domain-agnostic** — `wfe/hooks.py` contains ONLY infrastructure (REGISTRY, register, fire, HookResult, HookContext). No domain concepts in engine code.
11. **Domain hooks in workflow_hooks.py** — QMS-specific hook implementations live at qms-workflow-engine/ root, auto-loaded by CLI (like pytest's conftest.py). Engine never imports them.
12. **create-workflow is generic** — No EI/VR/VAR terminology. Agent fills chain_template, bookend_template, param_names, item_list. Hook reads these from node fields. Workflow is domain-agnostic.
13. **load_from copies to .wfe/** — Session always works from .wfe/ copy so source workflow files are never overwritten by fill/persist.
14. **workflows/ takes priority over .wfe/** in name resolution — so `wfe load my-workflow` always loads the canonical definition.

## CR-110 Execution Status
- EI-1 through EI-5 complete (work done in previous session)
- EI-6: Step 1 engine implementation — now complete (this session)
- CR-110 execution table NOT yet updated with outcomes
- Will update CR after Step 2 work is far enough along

## Progress Log

### Session Start
- New session: Session-2026-03-07-001
- Read all SOPs (001-007), all TEMPLATE/ files, QMS-Policy, START_HERE, QMS-Glossary
- CR-110: IN_EXECUTION v1.0, not checked out; inbox empty

### Design Session
- Long design conversation with Lead
- Established v2 engine architecture (see workflow-engine-design-v2.md)
- Key insight: EIs as nodes, templates, hooks, mock database, bootstrap strategy
- Design document written to session folder

### Step 1: Python Engine — COMPLETE

**New files created:**
- `wfe/graph.py` — updated: Field.parameter, Edge.traverse_hooks, Node.enter_hooks/exit_hooks, checkout() copies hooks, add_field() accepts parameter
- `wfe/hooks.py` — pure infrastructure: REGISTRY, register, fire, HookResult, HookContext
- `wfe/template.py` — FieldSpec, EdgeTemplate, Template, TemplateLibrary, instantiate()
- `wfe/database.py` — MockDatabase backed by db.json
- `wfe/session.py` — rewritten: workspace, lazy templates/db, hook dispatch in go()/advance(), load_from copies to .wfe/
- `wfe/persistence.py` — updated: save/load parameter, enter_hooks, exit_hooks, traverse_hooks
- `wfe/render.py` — fixed node.slots bug; updated HELP_TEXT
- `wfe/cli.py` — rewritten: auto-loads workflow_hooks.py; new commands: template, instantiate, db, workspace
- `wfe/__init__.py` — updated exports
- `workflow_hooks.py` — domain hook implementations: init_target_graph, build_node_chain, save_workflow, check_document_approved
- `templates/ei.yaml` — EI template: task_description (param), vr_required (param), execution fields (writable), edges to {var}/{vr}/{next}
- `templates/commit-ei.yaml` — commit-ei template: fixed task_description, commit_hash (writable), edge to {next} with commit_hash!= condition
- `workflows/create-workflow.yaml` — fully generic: home → define → done; agent fills workflow_name, chain_template, bookend_template, param_names, item_list

**Key design correction:**
- Lead flagged: EI/VR/VAR terminology should NOT appear in engine code (it's domain-specific)
- Fixed: Engine hooks.py has zero domain knowledge; workflow_hooks.py is the domain layer
- Fixed: create-workflow.yaml is fully generic (no mention of EIs, VRs, etc.)
- Fixed: build_node_chain reads config from node fields, not hardcoded; condition extracted from template's {next} edge

**Smoke tests passed:**
- Import all modules
- Load create-workflow.yaml + templates
- Execute create-workflow end-to-end → produces sample-cr.yaml with commit-ei bookends + 3 ei nodes
- Navigate sample-cr: commit_hash!= gate works (fill required before advance)
- create-workflow.yaml stays clean (session saves to .wfe/ copy)
