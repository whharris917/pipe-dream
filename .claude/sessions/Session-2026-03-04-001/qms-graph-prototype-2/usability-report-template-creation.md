# Usability Report: Creating a New Template (Code Review)

**Agent:** Claude (first-time user of this system)
**Task:** Create a `CodeReview` template extending `ProcedureBase`, validate it, run a document through it, and report on the experience.
**Date:** 2026-03-05

---

## What I Built

A `CodeReview` template (`templates/code_review.py`) that extends `ProcedureBase` and models a structured code review process:

```
start (inherited) -> submit_code -> static_analysis -> [review_steps extension point] -> review -> feedback -> resolution -> verify (inherited) -> close (inherited)
```

- 5 custom nodes with domain-specific evidence fields
- 1 extension point (`self.fill(g, "review_steps")`) for injecting custom review steps
- Uses all three field types: `text`, `enum`, `integer`
- Includes a `performer="reviewer"` on the review node to model role separation

**Validation:** 8 nodes, 0 errors.
**Full run:** 8 steps to completion, all evidence captured correctly.

---

## Was it clear how to create a new template?

**Yes, very clear.** The pattern is immediately obvious after reading one or two existing templates:

1. Subclass `ProcedureBase` (or `Template` for standalone)
2. Set class attributes: `id`, `name`, `description`
3. Override `define_procedure_body(self, g)` (for ProcedureBase subclasses)
4. Call `g.node(...)` for each step with evidence fields
5. Edges are auto-generated as linear sequence unless explicitly overridden

The entire process of reading the codebase and creating a working template took about 5 minutes of active work. The API surface is small and the conventions are consistent across all existing templates.

**Key clarity factor:** The `_GraphBuilder` auto-linear edge behavior means you just define nodes in order and they chain together automatically. This eliminates the most common source of boilerplate and errors. You only need `g.edge()` for non-linear flows (branching, looping).

---

## Did I understand extension points (self.fill)?

**Yes, with one small caveat.**

The mechanism is straightforward: call `self.fill(g, "name")` at the point in the node sequence where you want extensibility, and subclasses override `define_name(self, g)` to inject nodes there. This maps cleanly to the "template method" design pattern from OOP.

What made it intuitive:
- The naming convention is consistent: `self.fill(g, "X")` dispatches to `define_X(self, g)`
- The Diagnostic template demonstrates it clearly with `self.fill(g, "post_diagnosis")`
- The Repair template reinforces the pattern with `self.fill(g, "repair_steps")`
- ProcedureBase itself uses `self.fill(g, "procedure_body")` as the primary extension point

**The caveat:** The `fill()` method also supports a `fills` parameter on `instantiate()` for runtime data injection (not just subclass overrides). I understood this from reading the code in `graph.py`, but none of the existing templates demonstrate this runtime fills path. A test or example showing `instantiate(doc_id, fills={"review_steps": [...]})` would make this dual nature more obvious.

---

## Was the ProcedureBase inheritance intuitive?

**Extremely intuitive.** This is native Python class inheritance, which is the most natural mechanism possible. There is no custom DSL, no configuration language, no decorator magic -- just:

```python
class CodeReview(ProcedureBase):
    def define_procedure_body(self, g):
        # your nodes here
```

The inherited `start`, `verify`, and `close` nodes appear automatically. The subclass only defines what is unique to its domain. This is a very clean separation.

The `list-templates` command confirms the inheritance relationship:
```
templates.code_review.CodeReview extends ProcedureBase
```

**One observation:** The `abstract = True` flag on ProcedureBase is a class-level convention, not enforced by Python's `abc.ABC`. This is fine -- it is checked by `list-templates` and `load_template_class` to skip abstract templates. But a developer unfamiliar with the system might not realize that `abstract` is meaningful until they read `engine.py`.

---

## API Friction and Confusion

### Friction points (minor)

1. **Response file requirement for `respond`:** Every response must be written to a JSON file and passed via `--response-file`. For interactive testing this means creating a temp file for each step. An inline `--response '{"key": "value"}'` option or stdin pipe support would reduce friction significantly during development/testing.

2. **No `--dry-run` for respond:** When testing a new template, I had to trust that my response would validate. A dry-run mode that validates without advancing the cursor would be useful for exploration.

3. **Node ID prefixing is implicit:** The `_GraphBuilder.node()` method silently prefixes every node ID with `{template_id}.`. So when I write `g.node("submit_code", ...)`, the actual node ID becomes `code-review.submit_code`. This is logical but not documented in any docstring. I discovered it by reading `_GraphBuilder.node()`. For a first-time user who only read the templates, the prefix behavior would be a surprise when they see it in the JSON output.

4. **Integer field validation is strict on type:** The engine checks `isinstance(val, int)` for integer fields. When constructing JSON response files manually, JSON integers work fine. But if someone passed `"7"` (a string) it would fail validation. This is correct behavior, but a coercion option or a clearer error message mentioning the expected type would help.

### Things that caused zero confusion

- `Field` constructor: The `(type, required, values, hint)` signature is clean and self-documenting.
- `g.node()` keyword arguments: `prompt`, `context`, `evidence`, `performer`, `terminal` -- all obvious.
- Auto-linear edges: Just define nodes in sequence and they connect. Brilliant simplicity.
- `validate`, `start`, `respond`, `status`, `history`, `map` -- the CLI verbs form a coherent workflow.

---

## What Could Be Improved

### High value

1. **Inline response support:** `python engine.py respond doc.json --response '{"key": "val"}'` would dramatically improve interactive testing speed.

2. **Interactive mode:** A `python engine.py run doc.json` command that shows each node's prompt/schema and waits for input, walking through the entire document in one session. This would make template testing much faster than the current file-per-step approach.

3. **Template scaffolding command:** `python engine.py scaffold --base procedure_base --name CodeReview` that generates a starter file with the correct imports, class structure, and extension point override stub.

### Medium value

4. **Conditional edge examples in templates:** All current templates use purely linear flows. A template demonstrating branching (e.g., "if review_verdict == reject, go back to submit_code") would help users understand edge conditions without reading engine internals.

5. **Fill point documentation:** A docstring or comment convention marking where `self.fill()` calls sit in the node sequence. The existing templates use inline comments for this, which is good, but a more formal pattern (like a decorator or named constant) could make extension points discoverable via tooling.

6. **Performer role validation:** The `performer` field accepts any string but there is no registry of valid performers. Adding a convention or validation for known performers (initiator, reviewer, approver, qa) would catch typos.

### Low value (polish)

7. **Map view could show evidence field names** as a compact schema hint next to each node.
8. **History view could show performer** in the human-readable (non-JSON) output format.

---

## Summary

The template creation experience is excellent. The system has a small, well-designed API surface that uses native Python patterns (class inheritance, method override) instead of a custom DSL. A developer who reads two existing templates can create a new one in minutes. The extension point mechanism (`self.fill`) is clean and composes well with inheritance.

The main friction is in the testing workflow (file-per-response), not in the template authoring itself. The authoring API needs no changes; the CLI tooling around it could be more interactive.

**Overall assessment:** This is a well-designed template system. The learning curve is shallow, the patterns are consistent, and the Python-native approach means there is no new "language" to learn. I would be comfortable creating more complex templates (with branching, loops, multiple extension points) based on what I learned in this session.
