# Graph Template Design: The Copernican View

**Author:** Claude (Orchestrator)
**Date:** 2026-03-05
**Context:** Design exploration for template inheritance, document instantiation, and structural enforcement in the QMS Graph Engine

---

## The Diagnosis: Why the Current Design Has Epicycles

The `qms-graph-design.md` proposed a beautiful vision: "the entire QMS is a single graph." But implementing it requires:

- **Ticket-scoped nodes** -- custom steps that exist only for one ticket
- **Draft overlays** -- proposed graph changes that aren't live yet
- **Source provenance** -- `source: template` vs `source: author` on every node at runtime
- **Three-layer mutability rules** -- different editing permissions depending on lifecycle phase
- **Extension point insertion logic** -- live graph modification during traversal
- **Construction vehicle mechanics** -- a ticket that can write to the graph it's riding on

Each of these is a special accounting mechanism needed because one graph is serving three roles simultaneously: blueprint, work product, and execution environment. Each mechanism exists to answer the question: "which hat is this node wearing right now?"

That's the epicycle. The complexity comes from one thing pretending to be three things.

---

## The Copernican Insight

**Templates are graphs. Documents are graphs. They are separate graphs.**

A template is not a region of a shared graph that tickets ride through. A template is a **specification** -- a complete graph directory -- that gets **copied** to produce a new graph (the document). The document is self-contained. It doesn't reference the template at runtime. It was *born from* the template, the way a casting is made from a mold.

The mold and the casting are separate objects. The mold shapes the casting, but once cast, the object stands on its own. You don't need to track "which part of this casting came from the mold" at runtime -- it's obvious: everything did.

### What this eliminates

| Epicycle | Why it existed | Why it disappears |
|----------|---------------|-------------------|
| Ticket-scoped nodes | Custom steps can't live in the shared graph | The document IS its own graph -- author's nodes are first-class nodes in it |
| Draft overlays | Template authoring can't modify the live graph | Template authoring produces a NEW graph directory -- it's never "live" until approved |
| Source provenance at runtime | Engine needs to know which nodes are template vs author | The engine doesn't care. Provenance is a build-time record, not a runtime property |
| Three-layer mutability | Different editing rules for template/drafting/execution | Mutability is lifecycle status (QMS metadata), not graph structure |
| Construction vehicle | Tickets need to write to the graph they ride on | Authoring workflows produce NEW graphs. They don't modify themselves |
| Extension point insertion | Live topology modification during traversal | Extension points are consumed at build time, producing a finished graph |

### What remains

One concept: **a graph**. One operation: **traversal**. Everything else is build tooling that produces graphs from other graphs.

---

## The Design

### Three kinds of graphs

| Kind | Has extension points? | Has locked nodes? | Created by |
|------|----------------------|-------------------|------------|
| **Root template** | Yes | No | Authoring (meta-workflow or manual) |
| **Derived template** | Optionally | Yes (from parent) | `extend` operation |
| **Document** | No (consumed) | Yes (from template) | `instantiate` operation |

All three are the same data structure: a directory of YAML node files plus a `_graph.yaml` metadata file. The engine doesn't distinguish between them. It loads a directory and traverses.

### Two build-time operations

**`extend`** -- produce a child template from a parent template:

```
parent-template/     ->  build extend  ->     child-template/
  _graph.yaml                                  _graph.yaml (extends: parent)
  pre-commit.yaml                              pre-commit.yaml (locked: true)
  post-commit.yaml                             setup-env.yaml (new)
                                               implement.yaml (new)
                                               run-ci.yaml (new)
                                               post-commit.yaml (locked: true)
```

1. Copy parent nodes -> mark `locked: true`
2. Insert child nodes at parent's extension points
3. Re-wire edges
4. Result is a complete, self-contained template directory

**`instantiate`** -- produce a document from a template:

```
code-cr-template/    ->  build instantiate  ->  CR-109/
  _graph.yaml                                   _graph.yaml (instance_of: code-cr)
  pre-commit.yaml                               pre-commit.yaml (locked: true)
  setup-env.yaml                                setup-env.yaml (locked: true)
  run-ci.yaml                                   run-ci.yaml (locked: true)
  post-commit.yaml                              post-commit.yaml (locked: true)
                                                implement-collision.yaml (new, by author)
                                                write-tests.yaml (new, by author)
```

1. Copy template nodes -> mark `locked: true`
2. Author adds custom nodes at extension points
3. Re-wire edges
4. Result is a complete, self-contained document directory

### One traversal engine

The engine loads a graph directory (or multiple directories for composition with library subgraphs like `review-approval/`). It creates a ticket. It presents prompts, collects responses, evaluates edges, runs hooks. It does not know about templates, inheritance, locking, or lifecycle phases. It just traverses.

### One enforcement field

```yaml
node:
  id: exec-base.pre-commit
  locked: true          # Cannot be deleted or structurally modified
  prompt: "Create pre-execution baseline commit"
  evidence_schema:
    commit_hash: { type: text, required: true }
  edges:
    - to: code-cr.setup-env
```

`locked: true` means:
- **Cannot be deleted** (editing tools refuse)
- **Edges cannot be re-wired** (structural topology is fixed)
- **Evidence schema cannot be changed** (evidence requirements are fixed)
- **Prompt and context CAN be specialized** (human-readable text can be tailored per-document)

The engine ignores this field entirely. It's checked by editing tools and validated by the `validate` command.

---

## Extension Points

An extension point is an annotation on an edge that says "derived graphs can insert nodes here":

```yaml
# In parent template: pre-commit.yaml
node:
  id: exec-base.pre-commit
  prompt: "Create pre-execution baseline commit"
  edges:
    - to: exec-base.post-commit
      extension_point: execution-body    # Insertion allowed here
```

During `extend` or `instantiate`:
1. Build tool finds the edge with `extension_point: execution-body`
2. New nodes are inserted between the two endpoints
3. Edge is re-wired: `pre-commit -> new-step-1 -> ... -> new-step-N -> post-commit`
4. The `extension_point` annotation is consumed (removed from the output)

If no nodes are inserted, the edge remains as-is (direct connection).

A derived template can define its OWN extension points on its new nodes, allowing further derivation:

```yaml
# In code-cr template: run-ci.yaml
node:
  id: code-cr.run-ci
  prompt: "Run CI pipeline"
  edges:
    - to: exec-base.post-commit
      extension_point: post-ci-steps    # Instances can insert here
```

---

## Composition vs. Derivation

Two fundamentally different relationships between graphs:

**Derivation** (template -> document): build-time copy + lock. Produces a new directory. No runtime dependency on the source.

**Composition** (document + library subgraphs): runtime loading. Multiple directories loaded into one graph. Shared infrastructure.

```
code-cr-template/          <-- derivation (build-time)
     | instantiate
     v
CR-109/                    <-- the document
     + review-approval/    <-- composition (runtime)
     + deviation-handling/  <-- composition (runtime)
     | traverse
     v
ticket (cursor + evidence)
```

Template subgraphs (cr-lifecycle, inv-lifecycle) are **derived** -- copied per-document because they vary per-instance (different execution items, different scope).

Library subgraphs (review-approval, deviation-handling) are **composed** -- loaded at runtime because they're the same for every document.

---

## Lifecycle: External to the Graph

The graph engine doesn't encode lifecycle phases. The QMS metadata system does:

| Lifecycle Phase | What's mutable | Enforced by |
|----------------|---------------|-------------|
| **Template authoring** | Everything | Nothing (it's a new template) |
| **Document drafting** | Author nodes; template content (prompts/context) | `locked` field on template nodes |
| **Pre-approval review** | Nothing (under review) | QMS status check |
| **Execution** | Only ticket responses (evidence) | QMS status + engine (writes only to ticket, never to graph) |
| **Post-closure** | Nothing | QMS status check |

The engine already enforces "execution" correctly: it writes to the ticket, never to the graph files. The other phases are QMS workflow concerns -- they're checked by the CLI and editing tools, not by the traversal engine.

---

## Template Evolution

When a template is updated (new version of code-cr-template), what happens to existing documents?

**Nothing.** Each document is its own graph. It was copied from the template at creation time. It doesn't maintain a live reference. Template updates don't propagate to existing documents -- just like updating a class definition doesn't change existing objects.

New documents created after the update get the new template. This is correct behavior: you don't retroactively change an in-progress CR because the template changed. If an existing document needs the new structure, that's a formal deviation (VAR).

---

## How This Maps to What Exists

| Current component | Role in new design | Changes needed |
|------------------|--------------------|----------------|
| `engine.py` | The traversal engine | **None.** It already just traverses. |
| `generate.py` | Build tool for `instantiate` | Add `locked: true` to inherited nodes. Add `sort_keys=False` (done). |
| `meta/` workflow | Authoring workflow (produces templates) | Add extension point authoring support |
| `build-template/` workflow | Another authoring workflow | Same |
| `cr-lifecycle/` | **Template** (not a shared subgraph) | Add extension points, mark as template in metadata |
| `inv-lifecycle/` | **Template** | Same |
| `review-approval/` | **Library subgraph** (shared, composed at runtime) | No changes |
| `deviation-handling/` | **Library subgraph** | No changes |
| `test-harness.py` | Test infrastructure | Add template derivation/instantiation tests |

### New components needed

| Tool | Purpose |
|------|---------|
| `build.py extend` | Produce child template from parent template |
| `build.py instantiate` | Produce document from template |
| `build.py freeze` | Mark all nodes locked (pre-approval transition) |
| `engine.py diff` | Compare template vs document (structural validation) |
| `engine.py validate` (enhanced) | Check locked-node integrity |

### `_graph.yaml` additions

```yaml
graph:
  id: code-cr
  type: template              # template | document | library
  extends: executable-base    # Parent template (derivation)
  instance_of: code-cr        # Source template (instantiation)
  extension_points:
    - id: execution-body
      after: exec-base.pre-commit
      before: exec-base.post-commit
```

---

## The Design at a Glance

```
                    AUTHORING                     BUILD                      RUNTIME


              +----------------+
              | meta-workflow  | -- traversal -->  root template graph
              | (a graph)      |                     (a directory)
              +----------------+                         |
                                                         | extend
                                                         v
                                               derived template graph
                                                  (a directory)
                                                         |
                                                         | instantiate
                                                         v
                                                 document graph          <-- engine loads
                                                  (a directory)              and traverses
                                                         |                         |
                                                         |                         v
                                                         |                     ticket
                                                         |                  (cursor + evidence)
                                                         |
                                              + review-approval/   <-- composed at runtime
                                              + deviation-handling/ <-- (library subgraphs)
```

**Everything is a graph. Graphs are separate. Operations produce new graphs from existing graphs. The engine just traverses.**

---

## Summary

The entire enforcement model reduces to:

1. **One data structure:** A graph (directory of YAML node files + `_graph.yaml` metadata)
2. **Two build operations:** `extend` (template -> template) and `instantiate` (template -> document). Both copy + lock.
3. **One enforcement field:** `locked: true` on nodes. Checked by editing tools. Ignored by engine.
4. **One traversal engine:** Loads directories. Traverses with tickets. Knows nothing about templates.

The complexity of "how do I track template provenance at runtime" disappears because there IS no template at runtime -- just a document graph. The complexity of "how do I enforce structural integrity during traversal" disappears because the engine never modifies graph structure -- it only writes to tickets. The complexity of "how do I manage three layers of mutability" disappears because lifecycle is external metadata, not engine state.

**Templates, derived templates, and documents are all just graphs. They differ only in how they were created and what constraints they carry. The engine treats them all the same.**
