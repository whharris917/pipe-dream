# Grand Unification: U' + B → U

## Context

Having completed the A-C unification (A-C → U'), we now face the U'-B unification. The question: how can we generalize U' such that B becomes a limiting case of U, the grand unification of all three document architectures?

The answer lies in three observations:
1. Data always comes from `.meta/` — this was already settled in the U' design
2. Frontmatter editing and interactive sessions are just different input channels to the same `.meta/` data store
3. Jinja2 provides a single render engine that handles both simple variable substitution and complex structural compilation

---

## The Unified Architecture

Every document in the QMS follows one pattern:

```
Source file (Jinja2 template)  +  .meta/ (data context)  →  Draft (rendered markdown)
```

- **Source file** (`QMS/.source/`): A Jinja2 template. Ranges from simple (just `{{ user.foo }}` expressions in an author-written body) to complex (`{% for %}` loops, `{% if %}` conditionals, custom filters).
- **`.meta/` data**: The single data store. Contains system metadata, user properties (populated from frontmatter at checkin), and — for interactive documents — structured response data (populated by `qms interact`).
- **Render**: `jinja2.render(source, metadata_context)` → draft markdown. One function. Always.

---

## The Spectrum

The difference between document types is not architectural — it's the complexity of the Jinja2 template and the richness of the data context:

| Level | Source (Jinja2) | Data in `.meta/` | Input channel |
|-------|----------------|-----------------|---------------|
| Simple (SOP, INV) | Author-written body, no expressions | `user_properties` (title, revision_summary) | Frontmatter editing |
| Variable (RTM) | Author-written body with `{{ user.qualified_commit }}` expressions | `user_properties` (title, revision_summary, qualified_commit, rs_version, ...) | Frontmatter editing |
| **Hybrid** | Mix of author-written sections and `{% for %}` compiled sections | `user_properties` + interactive responses | Frontmatter editing + `qms interact` |
| Interactive (VR) | Entirely `{% for %}` loops, `{% if %}` conditionals, `{{ response }}` substitutions | `user_properties` + full interactive response tree (responses, loops, gates) | Frontmatter editing + `qms interact` |

There is no mode switch. The render engine is the same. The data store is the same. Documents sit at different points on the spectrum based on how much Jinja2 logic their source contains and how much data their `.meta/` holds.

B is the limiting case where the source is entirely Jinja2 compilation logic and the author provides no directly-written body text — only frontmatter values and interactive responses.

---

## Two Input Channels, One Data Store

Authors populate `.meta/` through two channels:

1. **Frontmatter editing** — The author writes concrete values in the source file's YAML frontmatter (`qualified_commit: abc123`). At checkin, these values are written to `user_properties` in `.meta/`. Every document uses this channel.

2. **Interactive engine** — The author provides responses via `qms interact`. The engine writes structured response data (responses, loops, gates, amendment trails) to `.meta/`. Only documents whose template defines interactive prompts use this channel.

Both channels write to `.meta/`. A document can use one or both. The render engine doesn't care where the data came from — it builds a context dict from `.meta/` and renders the source Jinja2 template.

---

## Jinja2 as the Unified Render Engine

The current system has two render functions:
- `resolve_variables()` — custom string substitution for `{%user:...%}` / `{%sys:...%}`
- `compile_document()` — custom structural compilation for VR documents

Jinja2 replaces both with a single call. Our `{%user:foo%}` syntax is already essentially Jinja2 (`{{ user.foo }}`). The VR compilation operations — loops, conditionals, value substitution, amendment rendering, context-aware formatting — are all Jinja2 primitives or custom filters.

**Syntax mapping:**

| Current | Jinja2 |
|---------|--------|
| `{%user:qualified_commit%}` | `{{ user.qualified_commit }}` |
| `{%sys:version%}` | `{{ sys.version }}` |
| `@loop` expansion | `{% for step in loops.verification_steps %}` |
| `@gate` conditional | `{% if gates.deficiency_found.value == 'yes' %}` |
| `@prompt` response | `{{ responses.test_result \| blockquote }}` |
| Amendment trail | `{{ responses.test_result \| amendment_trail }}` |

**Custom Jinja2 filters** (registered once):
- `blockquote` — wrap in `>` with attribution
- `code_fence` — wrap in triple backticks
- `amendment_trail` — render superseded entries with strikethrough
- `default_placeholder` — render `{{PLACEHOLDER}}` when value is null

---

## The Template's Two Roles

Templates serve two distinct purposes, both mediated by the same file:

**1. Scaffolding (consumed at creation):** The template provides the initial body structure — section headings, placeholder text, document skeleton. This is copied into the source file at creation and then lives there. The template is "dead" for this content after creation.

**2. Schema authority (alive throughout lifecycle):** The template's frontmatter declares the user property keys. At every checkout, the system syncs the document's schema against the current template. This role persists for the document's lifetime.

For interactive documents, the template has a third role: **3. Authoring flow definition.** The template (or a companion workflow spec) defines the prompt sequence, gates, and loops that the interactive engine uses. This is separate from the Jinja2 rendering — it's an authoring concern, not a rendering concern. The interactive engine redesign (Session-2026-02-22-004) proposed separating these into a workflow spec and a rendering template.

---

## What the Source File Looks Like

**Simple document (SOP):**
```
---
title: Execution and Evidence Procedures
revision_summary: 'CR-107: Updated for unified document lifecycle'
---

## 1. Purpose

This SOP establishes the procedures for...

## 2. Scope
...
```
No Jinja2 expressions. Render is an identity transform for the body. Frontmatter values populate `user_properties` at checkin; system frontmatter is injected at render.

**Variable document (RTM):**
```
---
title: {{ user.system_name }} Requirements Traceability Matrix
revision_summary: Updated traceability for v{{ user.rs_version }}
system_name: QMS CLI
rs_doc_id: SDLC-QMS-RS
rs_version: '22.0'
qualified_commit: abc123
---

# {{ sys.doc_id }}: {{ user.system_name }} Requirements Traceability Matrix

## 6.1 Qualified Baseline

| Attribute | Value |
|-----------|-------|
| Requirements Spec | {{ user.rs_doc_id }} v{{ user.rs_version }} |
| Commit | {{ user.qualified_commit }} |
```
Frontmatter has both concrete values (data input) and Jinja2 expressions (rendered fields). Body has Jinja2 expressions resolved from the metadata context.

**Interactive document (VR):**
```
---
title: {{ user.title }}
revision_summary: Initial verification
title: CR-091 Interaction System Verification
---

# {{ sys.doc_id }}: {{ user.title }}

## Verification Steps

{% for step in loops.verification_steps %}
### Step {{ loop.index }}: {{ step.title.value }}

**Expected:**
{{ step.expected.value | blockquote }}

**Actual:**
{{ step.actual.value | blockquote }}

**Result:** {{ step.result.value }}
{% endfor %}
```
Entirely Jinja2. The body is compiled from interactive response data in `.meta/`. The author wrote none of this body text directly — they provided responses through `qms interact`.

---

## Unified Lifecycle Operations

**Create:**
1. Read `TEMPLATE-{TYPE}.md`
2. Copy template body (scaffolding) to source file in `QMS/.source/`
3. Stamp frontmatter schema into `.meta/` (user_properties with null values)
4. Write stub draft ("No rendition available")
5. Auto-checkout to workspace

**Checkout:**
1. Schema sync from current template (add new keys, archive removed keys)
2. Copy source from `QMS/.source/` to workspace
3. If template defines interactive prompts: initialize/copy interact session

**Checkin:**
1. Parse workspace frontmatter → validate all user property keys present with concrete values
2. Write frontmatter values to `user_properties` in `.meta/`
3. If interactive session exists: validate all prompts answered, write response data to `.meta/`
4. Save workspace content to `QMS/.source/` (source preserved)
5. Build context from `.meta/`: `{ user: user_properties, sys: system_metadata, responses: ..., loops: ..., gates: ... }`
6. Render: `jinja2.render(source_body, context)` → draft body
7. Prepend rendered frontmatter (user + system properties) → save draft

**Read:**
1. Load source from `QMS/.source/`
2. Build context from `.meta/`
3. Render: `jinja2.render(source_body, context)` → display

---

## Connection to Interactive Engine Redesign

The interactive engine redesign (Session-2026-02-22-004) proposed:
- **Workflow specs** (YAML/Python): define the authoring flow (prompt sequence, gates, loops)
- **Jinja2 rendering templates**: define the output format
- **Source data**: the collected responses

This maps directly onto the unified architecture:
- Workflow specs → the authoring layer (how `qms interact` collects responses)
- Jinja2 source file → the rendering layer (how source + data → draft)
- `.meta/` response data → the data layer (what the author provided)

The grand unification and the interactive engine redesign are the same design, viewed from different angles.

---

## Key Properties

- **One render engine.** `jinja2.render(source, context)` for all document types. No `resolve_variables()`, no `compile_document()`.
- **One data store.** `.meta/` holds all data — user properties, system metadata, interactive responses. Different input channels write to the same store.
- **One source location.** `QMS/.source/` for all source files. The source is always a Jinja2 template (ranging from trivial to complex).
- **Spectrum, not modes.** Documents range from zero Jinja2 (identity transform) to full Jinja2 (structural compilation). No binary switch, no dispatch logic.
- **Template as living schema authority.** Schema synced at every checkout from `TEMPLATE-{TYPE}.md`. Unchanged from the U' design.
- **Frontmatter as universal input channel.** Every document sets user properties through frontmatter. Interactive documents additionally populate `.meta/` through the interact engine. Both channels feed the same data store.
