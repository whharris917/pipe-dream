# QMS Graph Prototype Demo

## What This Is

A working prototype of the "QMS Graph" — a unified graph-based system where the
entire QMS is a single traversable graph. Tickets (cursors) ride on the graph,
collecting evidence at each node. The graph supplies prompts, validates responses,
enforces gates, and fires hooks.

## Quick Start

```bash
cd qms-graph-prototype/

# Run all 19 automated test scenarios
python test-harness.py

# Validate a specific graph
python engine.py cr-lifecycle/ --validate

# Describe a graph's structure
python test-harness.py --graph cr-lifecycle --describe

# List all test scenarios
python test-harness.py --list

# Interactive traversal (try it!)
python engine.py cr-lifecycle/ --title "Change Record" --ticket CR-999
```

## What's Included

### Engine (`engine.py`)
- Graph loader with `_graph.yaml` metadata support
- Node model: prompt, context, evidence_schema, performer, edges, hooks, gates, wait
- Ticket model: cursor, responses, history, state, metadata, children
- Safe expression evaluator for edge conditions and gates
- `required_when` conditional field validation
- Interactive runner with ANSI color rendering
- Automated test runner (`AutoRunner`) with scripted responses
- Graph validation (broken edges, unreachable nodes)
- Ticket serialization to JSON

### Subgraphs (5 directories, 91 YAML nodes)

| Graph | Nodes | Description |
|-------|-------|-------------|
| `cr-lifecycle/` | 31 | Full CR lifecycle: create → draft → review → approve → execute → post-review → close |
| `inv-lifecycle/` | 26 | Full INV lifecycle: deviation → RCA → CAPAs → review → execute → close |
| `review-approval/` | 8 | Reusable review/approval pattern |
| `deviation-handling/` | 8 | Decision tree: execution failure → VAR, test failure → ER, systemic → INV |
| `build-template/` | 13 | Meta-graph for authoring new workflow templates |

### Test Harness (`test-harness.py`, 19 scenarios)

**CR Lifecycle (5):** happy path, review rejection loop, EI failure with VAR, approval rejection, scope revision full cycle

**Review/Approval (3):** happy path, request-updates loop, rejection with re-review

**INV Lifecycle (3):** happy path, CAPA failure with VAR, RCA revision loop

**Deviation Handling (4):** Type 2 VAR, test failure ER, systemic INV, Type 1 VAR blocking

**Build Template (3):** simple (no inheritance), inherited, revise-before-submit

**Validation (1):** required_when catches missing rejection comment

## Key Design Features

1. **Self-describing nodes**: Each YAML node contains its prompt, context, evidence schema, and hooks — an agent needs no external documentation to traverse the graph

2. **Conditional required fields** (`required_when`): Schema fields can be conditionally required based on other field values (e.g., `rejection_comment` required only when `decision == 'reject'`)

3. **Graph metadata** (`_graph.yaml`): Each subgraph has a metadata file declaring entry points, relationships to other graphs, performer mappings, and reviewer assignment guides

4. **Multi-performer support**: Nodes declare which role handles them (initiator, quality, reviewer, system), enabling delegation to different agents

5. **Wait nodes**: System-triggered pause points where the cursor waits for external conditions (e.g., all reviewers have submitted)

6. **Hooks with failure modes**: CLI/bash commands executed at node entry/exit, with `block` or `log` failure handling

7. **Gate conditions**: Pre-entry conditions that block traversal until satisfied (e.g., all reviewers must recommend before approval routing)

8. **Loop support**: Nodes can loop back (EI execution, CAPA execution, step definition), with responses promoted to lists on revisit

## Usability Testing Results

### Round 1 (cold-start agent, 7.4/10)
- Discoverability: 7/10 → Added `_graph.yaml` metadata
- Prompt Clarity: 8/10 → Added context to loop-control nodes
- Context Adequacy: 8/10 → Improved WAIT node messaging
- Schema Usability: 8/10 → Added `required_when`
- Flow Logic: 8/10 → Added reviewer assignment guide
- Error Handling: 6/10 → Improved gate messaging
- Agent Autonomy: 7/10 → Added reviewer mapping to context

### Round 2 (in progress)
- All Round 1 improvements incorporated
- 19/19 test scenarios passing
- Awaiting second evaluation

## Architecture Alignment

This prototype demonstrates the design principles from `qms-graph-design.md`:

- **P9**: System carries process knowledge (prompts, gates, hooks) — agent just answers
- **P10**: One interaction model at all layers (template building uses same engine as execution)
- **Third Rail**: Nodes supply prompts like a subway's third rail supplies power
- **Construction Vehicle**: `build-template` graph creates new workflow definitions
- **Delegation**: Multi-performer nodes model review/approval with different agents
