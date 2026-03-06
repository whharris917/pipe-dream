# Usability Report: Template Extension (4-Level Inheritance)

**Agent:** Claude Opus 4.6 (first-time user of this system)
**Task:** Create a SafetyIncident template extending the 3-level chain
**Date:** 2026-03-05

## Inheritance Chain

```
Template (base class, graph.py)
  -> ProcedureBase (abstract: start -> [procedure_body] -> verify -> close)
    -> Diagnostic (fills procedure_body: observe -> hypothesize -> test -> [post_diagnosis] -> conclude)
      -> Incident (overrides define: custom start; defines post_diagnosis: contain -> remediate)
        -> SafetyIncident (overrides define: safety start; extends post_diagnosis: + regulatory_report + lessons_learned)
```

**Final node sequence (11 nodes):**
start -> observe -> hypothesize -> test -> contain -> remediate -> regulatory_report -> lessons_learned -> conclude -> verify -> close

---

## Was the inheritance chain clear?

**Mostly yes, with one significant comprehension hurdle.**

Reading the chain from ProcedureBase to Diagnostic was immediately clear. ProcedureBase defines a skeleton with `self.fill(g, "procedure_body")` as the extension point, and Diagnostic fills it by implementing `define_procedure_body()`. The naming convention (`fill(g, "X")` dispatches to `define_X()`) is easy to internalize.

The hurdle came at the Incident level. Incident does NOT simply fill an extension point -- it **overrides `define()` entirely**. This means it re-creates the start, verify, and close nodes from scratch, and manually calls `self.fill(g, "procedure_body")` to pull in the Diagnostic chain. This is a different extension pattern than what ProcedureBase/Diagnostic demonstrate. At the Diagnostic level, extension works by filling named slots. At the Incident level, extension works by replacing the entire `define()` method and carefully re-invoking the same `fill()` calls.

This meant I had to understand two distinct extension mechanisms:
1. **Slot filling** via `fill(g, "name")` / `define_name(g)` -- additive, non-destructive
2. **Full override** of `define()` -- replaces the skeleton, must manually preserve fill calls

Both are valid patterns, but the switch between them at layer 3 required careful reading.

---

## Could I figure out where to add new extension points?

**Yes.** The `fill()` mechanism is simple and composable. In SafetyIncident, I:

1. Overrode `define_post_diagnosis()` to call `super().define_post_diagnosis(g)` first (preserving contain/remediate from Incident), then added `regulatory_report` and `lessons_learned` nodes.
2. Inserted a `self.fill(g, "post_remediation")` call between `super().define_post_diagnosis(g)` and the new safety nodes, providing an extension point for a hypothetical 5th level.

The pattern of "call super, then add more" worked cleanly because the `_GraphBuilder` accumulates nodes in list order. New nodes added after `super()` returns are appended after the parent's nodes, which is exactly the desired sequencing.

**One subtlety:** I had to override `define()` to customize the start and close nodes (since those are defined in Incident's `define()`, not in a fillable slot). This meant I had to replicate some of Incident's structure. A more composable design might have made `define_start()`, `define_verify()`, and `define_close()` into separate overridable methods so that subclasses could customize individual nodes without replacing the whole skeleton.

---

## Was the node ID prefixing scheme clear?

**Yes, and it worked well.** The `_GraphBuilder` automatically prefixes every node ID with the template's `self.id`, so:
- `g.node("start", ...)` becomes `safety-incident.start`
- `g.node("regulatory_report", ...)` becomes `safety-incident.regulatory_report`

This is clean and predictable. The only thing to note: the template ID (`safety-incident`) is set on the SafetyIncident class, so ALL nodes in the entire chain -- even those defined by Diagnostic's `define_procedure_body()` or Incident's `define_post_diagnosis()` -- get the `safety-incident.` prefix. This is correct behavior (the document's nodes should be namespaced to the template that created them), but it means you cannot distinguish which layer of the inheritance chain contributed a given node just by looking at its ID. That is more of an observation than a problem.

---

## What challenges did I encounter with 4-level inheritance?

### Challenge 1: Deciding the extension strategy

The biggest decision was how to add my new nodes. I had three options:

1. **Override `define()` entirely** -- Full control but must replicate structure from parent
2. **Override `define_post_diagnosis()` only** -- Can't customize start/verify/close nodes
3. **Hybrid: override both `define()` and `define_post_diagnosis()`** -- Maximum flexibility

I chose option 3. `define()` was overridden to customize start, verify, and close. `define_post_diagnosis()` was overridden to extend the post-diagnosis chain with `super()` + new nodes. This gave full control while preserving the slot-filling semantics.

### Challenge 2: Understanding who calls what

At 4 levels deep, the dispatch chain becomes:
```
SafetyIncident.define()
  -> self.fill(g, "procedure_body")
    -> Diagnostic.define_procedure_body()  [inherited, since SafetyIncident doesn't override it]
      -> self.fill(g, "post_diagnosis")
        -> SafetyIncident.define_post_diagnosis()  [overridden]
          -> Incident.define_post_diagnosis()  [via super()]
```

This required mentally tracing through 4 class levels and 2 dispatch mechanisms (direct method calls vs. `fill()` dynamic dispatch). It was manageable but would benefit from documentation or a debug mode that prints the dispatch trace.

### Challenge 3: Knowing what to replicate vs. inherit

Since Incident overrides `define()` entirely, I had to look at Incident's `define()` to understand what structure to replicate. Specifically, the `self.fill(g, "procedure_body")` call is essential -- without it, the Diagnostic nodes would not appear. This is the kind of thing that would cause a silent, hard-to-debug failure if missed: the template would validate and run, but with missing nodes.

---

## Did Python's MRO cause any surprises?

**No.** The MRO for SafetyIncident is:
```
SafetyIncident -> Incident -> Diagnostic -> ProcedureBase -> Template
```

This is a simple linear chain with no diamond inheritance, so Python's C3 linearization produces the obvious order. `super()` calls in `define_post_diagnosis()` correctly resolve to `Incident.define_post_diagnosis()`. No surprises.

If the template system ever introduces mixin-style templates (e.g., `class SafetyIncident(Incident, ComplianceMixin)`), MRO could become a real concern. But for linear chains, Python's default behavior is exactly right.

---

## Design Suggestions for the Template System

Based on this exercise, a few ideas for improving the extension experience:

1. **Decompose `define()` into named sub-methods.** If `ProcedureBase.define()` called `self.define_start(g)`, `self.define_verify(g)`, and `self.define_close(g)` internally, subclasses could override individual structural nodes without replacing the entire skeleton. This would eliminate the need for full `define()` overrides at levels 3 and 4.

2. **Add a dispatch trace mode.** A `build(debug=True)` option that prints the method resolution chain would help developers understand which class contributed which nodes during template construction.

3. **Document the two extension patterns.** The README or docstring should explicitly call out that there are two ways to extend: slot filling (preferred, additive) and full override (when you need to replace structural nodes). Guidelines on when to use each would help.

4. **Consider a `define_start()` / `define_close()` convention.** These are the nodes most commonly customized by subclasses. Making them individually overridable methods (like `define_procedure_body()`) would reduce boilerplate.

---

## Validation Results

| Check | Result |
|---|---|
| `python engine.py validate templates.safety_incident` | Valid, 11 nodes, 0 errors |
| `python engine.py start ... --doc-id SINC-001` | Started successfully |
| `python engine.py map .documents/SINC-001.json --no-color` | Correct 11-node linear chain |
| Full traversal (11 respond calls) | Completed, state=complete |
| `python test_harness.py` (existing suite) | 91 passed, 0 failed |
| `python engine.py list-templates` | Shows `SafetyIncident extends Incident` |

---

## Overall Assessment

The template system is well-designed for its intended use case. Python class inheritance maps naturally onto procedure extension, and the `fill()` mechanism provides clean, named extension points. A first-time user can read the 3-level chain and produce a working 4th level in a single pass.

The main friction point is the transition from slot-filling extension (Diagnostic) to full-skeleton override (Incident). This is an inherent tension in any template system: at some point, customization needs exceed what named slots can express. The system handles this correctly -- it just requires the developer to understand both patterns.

Time from first reading `graph.py` to working, validated template: approximately 20 minutes. No false starts or debugging required. The code was self-documenting enough to work from source alone.
