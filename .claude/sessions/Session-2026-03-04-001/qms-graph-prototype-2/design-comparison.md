# Python Templates vs YAML Templates: Design Comparison

**Date:** 2026-03-05
**Context:** Should QMS Graph templates be defined as Python classes (with native inheritance) or YAML files (with build-tool-based inheritance)?

---

## The Two Approaches

### YAML Approach (Prototype 1)
Templates are directories of YAML node files. Inheritance requires a custom `extend` build tool that copies parent nodes, marks them locked, and inserts child nodes at extension points.

### Python Approach (Prototype 2)
Templates are Python classes with a `define()` method. Inheritance uses native Python class inheritance. Extension points are method calls that dispatch to subclass overrides.

---

## Comparison

| Dimension | YAML | Python |
|-----------|------|--------|
| **Template definition** | Write YAML files (structured data) | Write Python class (code) |
| **Inheritance** | Custom `extend` build tool | Native `class Child(Parent)` |
| **Extension points** | Edge annotation + build tool | Method override (`define_*()`) |
| **Validation** | Custom `validate` command | Import-time errors + unit tests |
| **Browsability** | `ls template/`, `cat node.yaml` | Read Python module, trace MRO |
| **Git diffs** | Trivially readable YAML diffs | Code diffs requiring class knowledge |
| **Agent reading** | Direct file reads, structured data | Must understand Python class API |
| **Agent writing** | Fill in known fields | Write correct Python methods |
| **IDE support** | YAML schema validation | Full autocomplete, refactoring |
| **Testing** | Custom test harness | Standard pytest |
| **Error messages** | "Key not found" | Python tracebacks with line numbers |
| **Computed nodes** | Not possible | Loops, conditionals, functions |
| **Type safety** | None (runtime validation only) | IDE + linter catch typos at write time |

---

## What Python Gains

### 1. Inheritance is free
```python
class CodeCR(ExecutableBase):
    def define_execution_body(self, g):
        g.node("setup-env", prompt="Set up test environment", ...)
```
No custom build tool. No `extends:` metadata parsing. No node copying logic. Python's method resolution order handles everything.

### 2. Extension points are just methods
The parent calls `self.define_execution_body(g)`. The child overrides it. If no child overrides, the default (empty) runs. This is the Template Method pattern -- one of the most fundamental OOP patterns.

### 3. Validation at definition time
A broken template (missing node ID, bad evidence type) fails when you import the module, not when a ticket reaches the broken node 30 steps in.

### 4. Computed templates
```python
def define_execution_body(self, g):
    for i, ei in enumerate(self.execution_items):
        g.node(f"ei-{i+1}", prompt=ei["description"], evidence=ei["schema"])
```
Templates can generate nodes dynamically from data. YAML can't do this without a preprocessor.

### 5. Composition via mixins
```python
class CodeCR(ExecutableBase, ReviewCycleMixin):
    ...
```
Reusable graph fragments become mixins. No multi-directory loading needed.

---

## What Python Loses

### 1. Browsability
With YAML, `ls template/` shows the graph. `cat step.yaml` shows a node. With Python, you must read the class hierarchy and understand the builder API.

**Mitigation:** Templates can `compile()` to YAML for inspection. The source of truth is Python; YAML is a derived view.

### 2. Agent authoring friction
An agent creating a template via the meta-workflow would need to produce valid Python code. YAML fields are more forgiving.

**Mitigation:** Template creation is infrequent. The meta-workflow can still produce Python (agents write code all the time). Or: keep the meta-workflow producing YAML, and treat Python templates as the "advanced" authoring path.

### 3. Separation of data and logic
YAML is pure data. Python templates blur the line: is a computed node data or logic?

**Mitigation:** Convention. Templates should be declarative -- `define()` calls `g.node()` and `g.edge()`, nothing else. No business logic in templates.

---

## Agent Usability Analysis

### For traversal (answering prompts): No difference
The engine presents the same prompts regardless of source. Agents interact with the Graph object, not the template source.

### For template reading: YAML is slightly easier
YAML files are self-contained. Python requires tracing class hierarchy. But agents are good at reading Python code.

### For template writing: Python is easier for complex templates
Agents write Python code constantly. Writing a Template subclass with `define()` methods is natural. YAML requires knowing the exact schema.

### For template extending: Python wins decisively
`class MyTemplate(ParentTemplate)` is unambiguous. The YAML approach requires understanding the `extend` build tool, extension point annotations, and the build pipeline.

---

## Recommendation

**Use Python for template definition.** Rationale:

1. **Inheritance is the hard problem**, and Python solves it natively
2. **Template authoring is rare** (create once, use many times) -- optimize for the common case (traversal), which is identical either way
3. **Extension points as methods** are simpler than edge annotations + build tools
4. **The engine doesn't change** -- it works with Graph objects regardless of source
5. **YAML remains available** for inspection via `compile()` -- best of both worlds
6. **Agents can write Python** -- they do it all day. A Template subclass is no harder than any other class

The key insight: the complexity of inheritance disappears completely with Python classes. The YAML approach requires us to BUILD inheritance (custom tools, extension point annotations, node copying, edge re-wiring). The Python approach gives us inheritance for FREE.

---

## Prototype Architecture

```
qms-graph-prototype-2/
  graph.py              # Template, Node, Field, Graph, GraphBuilder
  engine.py             # Ticket, Evaluator, CLI (start/status/respond/map/history)
  templates/
    procedure_base.py   # Base: start -> [extension] -> verify -> close
    diagnostic.py       # Extends base: adds diagnosis steps
    repair.py           # Extends base: adds repair steps
    incident.py         # Extends diagnostic: adds escalation
    logic_puzzle.py     # Standalone: no inheritance
  test_harness.py       # Automated tests
```

Documents are JSON files containing the serialized graph + ticket state. Created by `instantiate()`, loaded by the engine. Independent of the template source after creation.
