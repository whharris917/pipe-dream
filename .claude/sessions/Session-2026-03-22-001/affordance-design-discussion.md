# Affordance Framework Design Discussion

**Session:** 2026-03-22-001
**Context:** Deep-dive into HATEOAS, REST, hypermedia, and affordance theory to inform the design of an intuitive, focused, navigable, discoverable, adaptable, and agent-friendly affordance framework for the workflow engine.

---

## The State of the Art — and Where Our Engine Sits

The workflow engine already implements something close to Siren-style hypermedia. Every response includes:
- **State** (the resource representation)
- **Instructions** (semantic context)
- **Affordances** (action templates with method, URL, body template, typed parameters)

This is meaningfully better than HAL (links only) and on par with Siren/Ion (actions with fields). The evaluation confirmed it: an agent with zero prior knowledge could build a 10-node workflow by reading affordances alone. That's the HATEOAS promise delivered.

**But the evaluation also revealed the failure mode of undifferentiated abundance.** When a focused builder node presents 17 affordances — each with parameter descriptions, options arrays, expression syntax references — the response is technically complete but practically overwhelming. Every affordance is rendered at the same prominence. There's no hierarchy, no visual weight, no sense of "this is probably what you want."

This is the gap between Gibson and Norman. The *real affordances* are all present (the agent *can* do 17 things). But the *signifiers* — the cues that communicate which affordances are relevant *right now* — are absent. It's a door with 17 handles.

---

## The Core Tension: Completeness vs. Navigability

Fielding's HATEOAS constraint says the response must contain the complete set of valid next actions. The agent shouldn't need out-of-band knowledge. This creates a tension:

- **Completeness** demands that every valid action be discoverable from the current state.
- **Navigability** demands that the agent can quickly identify the *relevant* actions without parsing through irrelevant ones.

Most hypermedia formats resolve this by being **flat** — here are your links, here are your actions, good luck. JSON:API's sparse fieldsets and GraphQL's field selection address the *data* side (request only the fields you need) but not the *affordance* side (request only the actions you need).

The "attention" idea addresses this directly. The key insight is that **completeness and navigability are not in conflict if the affordance space is navigable rather than flat.**

---

## The Attention Mechanism: Affordances as a Navigable Space

Think of the current affordance list as a single room with everything on the floor. The attention mechanism restructures it into a space you can move through:

**Level 0 — The Portal.** "Here are the workflow types. Here are your instances. Create new, open existing." This already works well. The affordance count is naturally low.

**Level 1 — The Node.** "You're at node X. Here are the *primary* affordances: the fields you need to fill, the proceed/navigation actions, the branch switches." These are the things the agent almost certainly wants to do. This is the **default view** — what you get from a plain GET.

**Level 2 — The Inspection.** "You asked for more detail about this node's structure. Here are the *structural* affordances: add/edit/remove fields, change the node mode, configure the proceed gate, set flags." These are the things an agent wants when it's *constructing or modifying* the node, not when it's *using* it.

**Level 3 — The Parameter Detail.** "You asked for the full specification of a specific affordance. Here are the parameter types, validation rules, expression syntax, available options." This is the reference material that currently gets repeated in every affordance.

The metaphor isn't progressive disclosure (hiding things until you're ready). It's **zoom** — the information exists at every level, and the agent controls its depth of field. This is closer to Shneiderman's visual information seeking mantra: *overview first, zoom and filter, then details-on-demand.*

---

## What Makes This Different from GraphQL Field Selection

GraphQL lets the client declare "I want these fields." That's attention on *data*. What we're describing is attention on *affordances* — "I want to know what I can do, at this level of detail."

The crucial difference: GraphQL's selection requires the client to know the schema in advance. The agent must already know what fields exist to request them. This mechanism is the opposite — **the agent doesn't need to know what structural affordances exist in order to discover that they exist.** It just sees "there are structural affordances available" and can choose to inspect them.

This is genuinely HATEOAS-compliant. The response at Level 1 says "here are your primary affordances, and here is a link to the structural affordances." The agent follows that link (or sends that query parameter) to zoom in. No out-of-band knowledge required.

---

## The Ecological Affordance Lens

Gibson's insight is that affordances are *relational* — they exist in the fit between the agent and the environment. A chair affords sitting to a human but not to a fish.

Applied to our engine: the same node affords different things depending on **what the agent is doing**:

- An agent **executing** a workflow wants to see: fields to fill, proceed, branch switch. It doesn't care about structural affordances (add field, set mode) because those don't exist in runtime.
- An agent **building** a workflow and currently adding fields wants to see: add field (with full parameter spec), edit field, remove field, and maybe the proceed configuration. It doesn't care about table, list, or action affordances until it decides to use them.
- An agent **inspecting** a built workflow wants to see: the full structural configuration, all fields, all gates — a comprehensive read view.

The current system treats all three cases identically: here are all your affordances, flat list, go. The attention mechanism lets the agent signal *what kind of interaction it's in*, and the server adapts the response accordingly.

---

## Concrete Design: How "Focus" / "Inspect" Could Work

### The Affordance Summary

Every response at the default level includes affordances grouped into **categories**, where each category shows:
- The category name (e.g., "fields", "structure", "navigation", "meta")
- The count of affordances in that category
- The primary/most-likely affordances expanded inline
- A **focus link** — an affordance itself — that expands the full category

```json
{
  "affordances": [
    {"id": 1, "label": "Set title", "method": "POST", "url": ".../title", "body": {"value": "<value>"}, "parameters": {"...": "..."}},
    {"id": 2, "label": "Set severity", "method": "POST", "url": ".../severity", "body": {"value": "<value>"}, "parameters": {"value": {"options": ["..."]}}},
    {"id": 3, "label": "Submit for Review", "method": "POST", "url": ".../proceed", "body": {}},
    {"id": 4, "label": "Switch to Compliance Review", "method": "POST", "url": ".../switch_branch", "body": {"branch": "compliance"}}
  ],
  "affordance_groups": {
    "fields": {"count": 2, "expanded": true},
    "flow": {"count": 2, "expanded": true},
    "structure": {"count": 8, "expanded": false, "inspect": {"method": "GET", "url": ".../abc123?focus=structure"}},
    "meta": {"count": 3, "expanded": false, "inspect": {"method": "GET", "url": ".../abc123?focus=meta"}}
  }
}
```

The agent sees 4 primary affordances (the ones it almost certainly needs) plus a signal that 11 more exist in two collapsed groups. If it needs structural affordances, it follows the inspect link. **Zero information is lost. Zero extra round-trips are needed for the common case.**

### The Focus Parameter

`?focus=structure` expands that category's affordances inline while keeping others collapsed. `?focus=all` returns the current flat list (backward compatible). `?focus=fields,flow` expands multiple categories. This is the zoom control.

### Parameter Detail Separation

At Level 1-2, affordances include their body template and basic parameter info (options for selects, type hints). The expression syntax documentation, complex validation rules, and rich metadata move to a separate `?focus=reference` or are included only when `?detail=full` is specified. This addresses the repetition problem (expression syntax appearing 8+ times per response) without losing discoverability — the short reference "See expression_syntax" already works, and expression_syntax is already factored to the response root.

---

## The "Attention as Innovation" Angle

The framing of this as an "attention mechanism" is worth developing. In transformer architecture, attention is: given a query, compute relevance scores over a set of keys, then retrieve the corresponding values weighted by relevance.

The API analog:
- **Query** = the agent's current intent (fill fields? modify structure? navigate?)
- **Keys** = affordance categories
- **Values** = the full affordance specifications
- **Attention** = the focus parameter, which weights certain categories for expansion

The difference from transformer attention is that here the agent *explicitly declares* its attention rather than having it computed implicitly. But the principle is the same: not all information is equally relevant at every moment, and the system should support selective retrieval.

This is genuinely novel in the API design space. No existing hypermedia format treats affordances as a navigable, focusable space rather than a flat list. HAL has no affordances at all. Siren has actions but they're flat. Hydra has operations but they're schema-level, not instance-adaptive. None of them have a mechanism for the client to say "show me more about this category of action."

---

## The Constraint We Must Preserve

The LNARF principle (Lossless, Non-Additive, Representationally Free) requires that the human and agent views are both faithful projections of the same canonical representation. If the API response at Level 1 omits structural affordances, the human renderer must also omit them (or group them identically).

This actually works in our favor. The human UI can render collapsed affordance groups as expandable sections — "Structure (8 actions)" with a disclosure triangle. The agent gets the same signal as a JSON group with a focus link. Both views are faithful to the same canonical representation. The canonical representation just gained a new dimension: **affordance grouping with expansion state.**

---

## Open Design Decisions

1. **How to categorize affordances** — by primitive type (fields/lists/tables/navigation/flow/actions/meta) or by intent (use/build/inspect)?
2. **What's "primary" at the default level** — fields + flow control always expanded? Or context-dependent?
3. **Whether focus is a query parameter or a separate affordance** — `?focus=structure` vs. a POST action that changes the expansion state?

---

## Background Research: Hypermedia Format Landscape

### Hypermedia Formats Compared

| Format | Links | Actions/Methods | Field Types | Write Templates | Complexity |
|--------|-------|----------------|-------------|-----------------|------------|
| HAL | Yes | No | No | No | Low |
| JSON:API | Yes | Partial | No | Sparse fieldsets | Medium |
| Collection+JSON | Yes | CRUD implied | Yes (in template) | Yes | Medium |
| Siren | Yes | Yes (explicit) | Yes (in actions) | Yes | Medium-High |
| Ion | Yes | Yes (via forms) | Yes (form fields) | Yes | Medium |
| JSON Hyper-Schema | Yes | Yes | Yes (via JSON Schema) | Yes (submissionSchema) | High |
| Hydra | Yes | Yes (operations) | Yes (supportedProperty) | Yes | Very High |

Our engine's affordance format is closest to **Siren** — actions with explicit HTTP methods, body templates, and typed parameter descriptions. We go beyond Siren in parameter richness (options, labels, descriptions, dynamic options, expression syntax) but share the flat-list limitation.

### Key Concepts from HATEOAS / REST

**Fielding (2008):** "A REST API should be entered with no prior knowledge beyond the initial URI... The rest of the interaction is driven by hypertext." Our portal → workflow → instance → node chain achieves this.

**Carson Gross (htmx):** Hypermedia controls *are* the API contract. There is no separate API documentation to go out of sync. The response itself tells the client what resources exist, what actions are available, what parameters those actions accept, and where to submit them.

**The versioning advantage:** Hypermedia naturally solves versioning because clients don't hardcode URLs — they follow links. New capabilities appear as new hypermedia controls. Old clients ignore controls they don't understand.

### Affordance Theory

**Gibson (1979):** Affordances are relational — they exist in the fit between the agent and the environment. A horizontal surface affords support; water affords swimming for some animals and drowning for others.

**Norman (1988, revised 2013):** Distinguished between *affordances* (real action possibilities) and *signifiers* (information that communicates where/how to act). "Signifiers signal things, in particular what actions are possible and how they should be done."

**The gap our engine has:** The real affordances are all present (the agent *can* do 17 things). But the signifiers — the cues that communicate which affordances are relevant *right now* — are absent.

### Agent-Friendly API Design

**Token overhead:** MCP tool descriptions are loaded up-front into model context. Complex schemas consume tokens and crowd out conversation history. Every tool call introduces reasoning overhead, schema parsing, and a full round-trip.

**Key principle:** "Unlike human developers who can infer missing details, AI agents rely entirely on what you document." But documenting everything at maximum detail at all times creates the opposite problem — signal buried in noise.

**The attention mechanism resolves this:** Document everything, but let the agent control the zoom level. Full detail is always available; it's just not always foregrounded.

### Progressive Disclosure in API Design

**Shneiderman:** "Overview first, zoom and filter, then details-on-demand."

**Existing mechanisms:** GraphQL field selection (attention on data), OData $expand/$select (hierarchical attention), JSON:API sparse fieldsets (property filtering), Prefer header (return=minimal vs return=representation).

**What's missing:** None of these address attention on *affordances*. They all filter the *data* side of the response. The ability to say "show me more about what I can *do*" rather than "show me more about what *exists*" is an open design space.
