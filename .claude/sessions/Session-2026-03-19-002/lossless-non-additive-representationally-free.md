# Lossless, Non-Additive, and Representationally Free

*A Design Principle for Engine-Projected Software Architecture*

---

## 1. Statement of the Principle

An application architecture is **lossless, non-additive, and representationally free** when it satisfies three constraints simultaneously:

1. **Lossless.** Every semantic element produced by the engine must appear in every projection. No projection may omit, suppress, or silently discard any element of the engine's output. If the engine says a gate exists and is blocked, every projection must communicate that a gate exists and is blocked. Silence is a loss of information and is non-conforming.

2. **Non-additive.** No projection may introduce semantic elements that do not originate from the engine. A projection may not invent fields, fabricate constraints, synthesize affordances, or display information that has no corresponding element in the engine's output. If it appears in the projection, it must be traceable to the engine. Untraceable content is non-conforming.

3. **Representationally free.** The engine's output carries no opinion about how it should be rendered. Projections are free to choose any representational form — textual, graphical, interactive, auditory, spatial — provided the first two constraints are satisfied. The word "locked," a lock icon, a grayed-out button, and a haptic pulse are all valid representations of the same semantic element, and all may coexist as different projections of the same engine output.

The three constraints are independent. A projection can be lossless but additive (it shows everything the engine produces, plus things it invented). A projection can be non-additive but lossy (it invents nothing, but omits things the engine produced). A projection can be representationally constrained (it preserves all semantics and invents nothing, but mandates a single visual form). Only when all three constraints hold simultaneously does the architecture achieve its intended properties.

---

## 2. Definitions

**Engine.** The single system that holds semantic authority — the exclusive source of state, constraints, affordances, and evaluations. The engine interprets declarative definitions (workflow specifications, data models, rule sets) and produces a structured output that constitutes the complete semantic content of the application at any given moment. The engine does not render, display, or present. It computes and emits.

**Projection.** Any system that consumes the engine's output and presents it to a participant — whether human or machine. A visual renderer, an API response serializer, an accessibility layer, a collaboration interface, an audio narration system, and a raw data inspector are all projections. Each is an independent exercise of representational freedom bounded by the lossless and non-additive constraints.

**Semantic element.** An atomic unit of meaning in the engine's output: a field with a value, a gate with conditions and a pass/fail state, an affordance with a label and parameters, a topology node with a position in the workflow graph, a feedback diff with an outcome and effects. Semantic elements are the things that must be preserved (lossless) and not invented (non-additive).

**Representational form.** The specific visual, textual, auditory, or interactive treatment a projection applies to a semantic element. A field value of "Critical" can be rendered as the string "Critical," as a red badge, as a dropdown with "Critical" selected, or as a spoken word. These are different representational forms of the same semantic element.

---

## 3. The Semantic-Representational Boundary

The principle defines a strict boundary between two orthogonal spaces:

**The semantic space** is the engine's domain. It contains all facts about the application's current state: what exists, what is true, what is permitted, what is blocked, what changed, and why. The semantic space is singular — there is one engine, one output, one truth. All projections consume the same semantic content.

**The representational space** is the projection's domain. It contains all choices about how semantic content is presented: layout, color, typography, interactivity, density, modality, language, animation. The representational space is plural — many projections can coexist, each making different representational choices, all consuming the same semantic content.

The boundary between these spaces is the architectural invariant. No projection may reach across the boundary to modify, extend, or reduce the semantic content. No engine output may reach across the boundary to constrain the representational form. The engine is semantically authoritative and representationally silent. The projection is representationally free and semantically subordinate.

### 3.1 Testing the Boundary

For any element visible in a projection, two questions determine conformance:

**The lossless test.** For every semantic element in the engine's output, can I find a corresponding element in the projection? If any semantic element has no corresponding representation, the projection is lossy and non-conforming.

**The non-additive test.** For every element in the projection, can I trace it to a semantic element in the engine's output? If any element in the projection has no source in the engine's output, the projection is additive and non-conforming.

Elements that fail the non-additive test fall into two categories:

- **Representational apparatus** — chrome, layout, whitespace, borders, icons used as decoration, navigation affordances intrinsic to the projection medium (scrollbars, tab stops). These are properties of the representational form, not semantic elements, and are conforming. They do not claim to represent engine state; they are infrastructure for presenting it.

- **Invented semantics** — a tooltip containing information not in the engine's output, a validation rule that exists only in the projection, a disabled state applied by CSS rather than by the engine's affordance logic, a badge that classifies an element using a taxonomy the engine does not produce. These are non-conforming.

The distinction is pragmatic: representational apparatus serves the medium; invented semantics claim to represent state. A scrollbar is apparatus. A "Warning: this field is required" message that does not originate from the engine's gate evaluation is an invented semantic.

---

## 4. Why These Three Constraints

### 4.1 Lossless: The Obligation of Completeness

The lossless constraint ensures that no participant is denied information that the engine considers relevant. If the engine produces a gate condition, every participant must be made aware of it — whether they are an AI agent reading a JSON affordance list, a human operator watching a visual observer, or a compliance auditor reviewing an audit trail.

Without the lossless constraint, projections become filters. A "simplified" view that hides gate conditions for readability, a "summary" dashboard that omits individual field values, an "executive" report that elides execution details — each of these is a lossy projection that creates an information asymmetry between participants. In governed systems, information asymmetry is a compliance failure. In collaborative systems, it is a coordination failure. In safety-critical systems, it is a hazard.

The lossless constraint does not prohibit summary or hierarchy. A projection may render a complex gate condition as a single icon — but the icon must be present, and expanding or inspecting it must reveal the full condition. Compression is not loss; omission is.

### 4.2 Non-Additive: The Prohibition on Invented Semantics

The non-additive constraint ensures that participants do not perceive state that the engine does not know about. If a button appears disabled in the projection but the engine's affordance list includes the corresponding action, the participant's perception diverges from the system's truth. If a tooltip says "Required" but the engine has no such constraint, the participant is being lied to — not maliciously, but structurally. The lie is embedded in the architecture.

Most software architectures are pervasively additive. The UI layer adds hover states that represent no model state. The form layer adds validation rules that duplicate or contradict the server's rules. The dashboard adds derived metrics that the backend does not compute. Each addition is individually defensible but collectively creates a system where no single source of truth exists — because every layer has added its own truths.

The non-additive constraint eliminates this class of problem by fiat. The engine is the sole source of semantic content. Projections present it; they do not augment it. If a semantic element is needed in the projection, it must be added to the engine, where it becomes available to all projections simultaneously and is subject to the engine's evaluation, persistence, and audit mechanisms.

This forces a specific development discipline: when a new capability is needed, the question is always "does this belong in the engine or in the renderer?" If it carries semantic content — a constraint, a state, a condition, an affordance — it belongs in the engine. If it is purely presentational — a color, a layout, an animation, an interaction pattern — it belongs in the renderer. The boundary is not a guideline; it is the architecture.

### 4.3 Representationally Free: The Permission to Vary

The representational freedom constraint ensures that the architecture does not collapse into a single mandatory rendering. Without this constraint, "lossless and non-additive" could be satisfied trivially by mandating that every projection render the engine's output as raw JSON. This would be lossless (nothing omitted), non-additive (nothing invented), and useless (no human could work with it efficiently).

Representational freedom is what makes the architecture practical. It permits a compact pill-shaped node in a workflow banner and a rich multi-section card in a detailed flowchart to coexist as projections of the same engine output. It permits a visual observer, a collaboration interface with interactive controls, and an API response with structured JSON to coexist as projections of the same page dictionary. Each is optimized for its medium and its audience while preserving the same semantic content.

Representational freedom is also what makes the architecture extensible. Adding a new projection — a mobile renderer, an accessibility-focused audio renderer, a spatial AR renderer — requires no changes to the engine. The new projection consumes the same output and exercises the same representational freedom within the same semantic constraints. The engine does not know or care how many projections exist or what representational choices they make.

---

## 5. Architectural Consequences

### 5.1 The Engine Is the Single Source of Truth

Because no projection may add semantics and no projection may omit them, the engine's output is the complete and exclusive description of the application's state. There is no "UI state" that exists only in the browser. There is no "API state" that exists only in the response serializer. There is no "display logic" that makes semantic decisions in the rendering layer. All semantic decisions are made by the engine, and the results are projected uniformly to all consumers.

This means that any question about the application's state can be answered by querying the engine. "What can the user do next?" is answered by the affordance list. "Why is this action blocked?" is answered by the gate evaluation. "What changed after this action?" is answered by the feedback diff. No projection needs to be consulted, because no projection has information the engine does not have.

### 5.2 Projections Are Interchangeable

Because all projections consume the same semantic content and differ only in representational form, participants can switch between projections without losing information. An operator can switch from a compact banner to a detailed flowchart. A developer can switch from a visual renderer to raw JSON. A collaborator can switch from observation mode to interactive mode. Each switch changes the representational form; none changes the semantic content.

This interchangeability also means that projections can be composed. A screen can display a compact topology banner (one projection) alongside a detailed card view of the current step (another projection) alongside a raw JSON inspector (a third projection). All three consume the same engine output. All three are lossless. All three are non-additive. They coexist because they occupy the same semantic space rendered through different regions of the representational space.

### 5.3 New Capabilities Are Engine-Level Changes

When the application needs a new semantic capability — a new field type, a new control-flow primitive, a new condition operator — the change is made in the engine. Every projection then has access to the new capability automatically, because it appears in the engine's output. The projection may need a new representational strategy for the new element (e.g., a visual treatment for a previously unseen node type), but the semantic content is already available.

This inverts the common pattern where new capabilities are added at the UI layer first ("add a button that does X") and then propagated downward to the backend. In this architecture, capabilities propagate upward: the engine gains a new semantic element, and projections independently develop representational strategies for it. The engine change is sufficient to make the capability available; the projection changes determine how it is presented.

### 5.4 Bugs Have Clear Jurisdiction

When a semantic error occurs — the wrong affordances are offered, a gate evaluates incorrectly, a side effect fires when it shouldn't — the bug is in the engine. Always. No projection can cause a semantic error because no projection has semantic authority. Diagnosis begins and ends at the engine layer.

When a representational error occurs — an element is displayed in the wrong position, a color is incorrect, an interactive control doesn't respond — the bug is in the projection. The engine's output can be inspected (via the raw JSON projection) to confirm that the semantic content is correct, isolating the defect to the representational layer.

This jurisdictional clarity is a direct consequence of the semantic-representational boundary. In architectures where the UI layer makes semantic decisions (validation, state management, business logic), a bug's jurisdiction is ambiguous — it could be in the frontend, the backend, or in the interaction between them. In this architecture, the boundary eliminates the interaction: semantic content flows one way, from engine to projection, and representational choices flow the other way, from the projection's design to its rendering. The two do not interact, so they cannot produce interaction bugs.

---

## 6. Relationship to Existing Concepts

The principle draws from several established ideas while combining them in a way that, taken together, constitutes a distinct architectural constraint:

**Model-View separation** (MVC, MVVM, etc.) separates data from presentation, but does not prohibit the view from adding semantic content. View models, computed properties, and presentation logic routinely introduce state that does not exist in the model. The non-additive constraint is stronger than standard model-view separation.

**Single source of truth** (Redux, event sourcing) centralizes state management, but does not address what projections may do with the state they receive. A Redux application can have a single store and still render a tooltip that contains invented information. The principle extends single-source-of-truth to include the prohibition on invention and the obligation of completeness.

**HATEOAS** (Hypermedia as the Engine of Application State) requires that the server's response include all available actions, which is aligned with the lossless constraint. But HATEOAS does not prohibit the client from adding its own actions, and it does not require that all clients receive the same response. The principle is stricter on both counts.

**Content-agnostic rendering** (game engines, browser rendering engines) separates content from rendering infrastructure, allowing the same renderer to handle arbitrary content. This is aligned with representational freedom but does not impose the lossless or non-additive constraints on the content pipeline.

The principle's novelty, to the extent it has one, is in the *combination* and the *strictness*: the obligation of completeness (lossless), the prohibition on invention (non-additive), and the explicit permission to vary (representationally free), applied simultaneously and without exception to the relationship between a semantic engine and its projections.

---

## 7. Summary

| Constraint | What it requires | What it prohibits | What it tests |
|---|---|---|---|
| **Lossless** | Every semantic element in the engine's output must appear in every projection | Omission, suppression, silent filtering of engine output | For each engine element, does a corresponding projection element exist? |
| **Non-additive** | Every semantic element in a projection must trace to the engine's output | Invented fields, fabricated constraints, UI-only validation, untraceable state | For each projection element, does a corresponding engine element exist? |
| **Representationally free** | Projections may use any form to represent semantic elements | Mandating a single canonical rendering; engine output dictating visual form | Can multiple projections coexist, each using different forms, all satisfying lossless and non-additive? |

The three constraints together define an architecture where the engine holds exclusive semantic authority, projections hold exclusive representational authority, and the boundary between them is the system's central invariant. Functionality enters the system through the engine. Presentation enters the system through projections. Neither may encroach on the other's domain.

The practical test is simple. For any element in any projection, ask two questions:

1. **Can I find this in the engine's output?** If no, the projection is additive. Remove the element or add it to the engine.
2. **Is every engine element findable in this projection?** If no, the projection is lossy. Add the missing representation.

If both answers are yes, and the projection achieves them through its own representational choices rather than by copying a mandated form, the projection conforms. The architecture holds.
