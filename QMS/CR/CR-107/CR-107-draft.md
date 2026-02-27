---
title: 'Unified Document Lifecycle: Jinja2 render engine, universal source files,
  and living schema authority'
revision_summary: v1.0 — Complete redesign. Grand unification of all three document
  architectures (Direct, Interactive, Template-Variable) into a single system with
  Jinja2 render engine, .meta/ as universal data store, and spectrum of template complexity.
  Replaces v0.3 entirely.
---

# CR-107: Unified Document Lifecycle

## 1. Purpose

Unify the QMS document system into a single architecture. The current system has three separate document architectures with different storage models, render pipelines, and lifecycle operations. This CR replaces all three with one universal pattern:

```
Source file (Jinja2 template)  +  .meta/ (data context)  →  Draft (rendered markdown)
```

Every document — from a simple SOP with no expressions to a fully interactive VR with loops and conditionals — follows this pattern. The difference between document types is not architectural; it is the complexity of the Jinja2 template and the richness of the data context. There is no mode switch, no binary dispatch, no separate code paths.

---

## 2. Scope

### 2.1 Context

The QMS currently has three document architectures that evolved independently:

- **Architecture A (Direct):** CR, SOP, INV, VAR, ADD, RS, RTM, TP, ER. No source/rendered separation. The draft IS the document. `write_document_minimal()` strips system frontmatter for workspace; body passes through untouched.

- **Architecture B (Interactive):** VR only. Full source/rendered separation. Structured JSON source (`.source.json` in `.meta/`) compiled to markdown via `compile_document()`. The template (`TEMPLATE-VR.md` with `@prompt`/`@gate`/`@loop` annotations) is a persistent compiler input.

- **Architecture C (Template-Variable):** Proposed in the original CR-107 design but never implemented. Markdown with `{%user:...%}` / `{%sys:...%}` variables resolved via custom string substitution.

This CR unifies all three into a single system where A, B, and C are limiting cases of one architecture. Architecture A is the limiting case with zero Jinja2 complexity (identity transform). Architecture B is the limiting case where the entire body is Jinja2 compilation logic. Architecture C dissolves into the spectrum between them.

- **Parent Document:** None

### 2.2 Changes Summary

1. **Universal source files** — ALL documents get a source file in `QMS/.source/`. The rendered draft is always a derived artifact. No opt-in, no detection.
2. **Jinja2 render engine** — One render function (`jinja2.render(source, context)`) replaces both `resolve_variables()` (which does not yet exist) and `compile_document()`. Custom filters for blockquoting, amendment trails, code fencing.
3. **`.meta/` as universal data store** — User properties, system metadata, and interactive response data all live in `.meta/`. Different input channels write to the same store.
4. **Template as living schema authority** — `TEMPLATE-{TYPE}.md` defines the user property schema. Schema synced at every checkout. Template evolution propagates to all documents of that type.
5. **Frontmatter as sole input channel** — Authors set user properties by editing frontmatter in the source file. No `qms set` command. One input path, no precedence questions.
6. **All frontmatter fields are user properties** — `title` and `revision_summary` are not special. Source frontmatter = user properties. Draft frontmatter = user properties + system properties. `filter_author_frontmatter()` and `write_document_minimal()` stripping/restoring are eliminated.
7. **Draft is always derived** — At creation, the draft is a stub. After checkin, the draft is the Jinja2 render output. The draft is never an input to any operation.
8. **Checkout-triggered migration** — Pre-existing documents acquire source files and user property schemas at first checkout under the unified system.
9. **VR source consolidation** — Move `.source.json` from `.meta/` to `.source/`, unifying all source storage.
10. **Schema evolution with archival** — New template fields appear as null-valued properties (checkin blocked until filled). Removed template fields are archived with provenance.

### 2.3 Files Affected

- `qms-cli/qms_render.py` — New file: Jinja2 render engine, custom filters, context builder
- `qms-cli/qms_source.py` — New file: source path utilities, schema sync, migration logic
- `qms-cli/qms_schema.py` — New file: template schema parsing, schema comparison, archival logic
- `qms-cli/commands/create.py` — Modify: source-first creation, stub draft, schema stamping
- `qms-cli/commands/checkin.py` — Modify: frontmatter validation, user_properties population, Jinja2 rendering, source preservation
- `qms-cli/commands/checkout.py` — Modify: source-aware checkout, schema sync, migration
- `qms-cli/commands/read.py` — Modify: Jinja2-based rendering for all document types
- `qms-cli/commands/interact.py` — Modify: write response data to `.meta/` (unchanged engine, new data path)
- `qms-cli/qms_docs.py` — Modify: eliminate `filter_author_frontmatter()`, `write_document_minimal()` frontmatter stripping/restoring
- `qms-cli/qms_mcp/tools.py` — Modify: update tools for new lifecycle
- `qms-cli/tests/test_render.py` — New file: Jinja2 render engine tests
- `qms-cli/tests/test_schema.py` — New file: schema sync and archival tests
- `qms-cli/tests/test_source.py` — New file: source system tests
- `qms-cli/tests/test_migration.py` — New file: pre-existing document migration tests

---

## 3. Current State

### 3.1 Architecture A (Direct Documents)

The majority of document types (CR, SOP, INV, VAR, ADD, RS, RTM, TP, ER) follow a direct model where the draft IS the document. There is no source/rendered separation:

- **Checkout:** `write_document_minimal()` strips system-managed frontmatter fields (`version`, `status`, `responsible_user`, etc.) from the document, copies the result to the workspace.
- **Checkin:** The CLI reads the workspace document, re-injects system frontmatter from the metadata sidecar, writes the result back to `QMS/`.
- **Template role:** `TEMPLATE-{TYPE}.md` provides one-time scaffolding at creation. `{{TITLE}}` and type-specific placeholders are substituted once, then the template plays no further role.
- **Frontmatter:** Two categories — "author-maintained" (`title`, `revision_summary`) and "system-managed" (everything else). `filter_author_frontmatter()` enforces the split.

This architecture conflates the authoring artifact with the review artifact. Any value that should be system-maintained (commit hashes, version references) must be manually written and updated by the author.

### 3.2 Architecture B (Interactive Documents)

VR documents follow a completely separate architecture with full source/rendered separation:

- **Source:** Structured JSON (`.source.json`) stored in `QMS/.meta/`, containing responses, loops, gates, amendment trails, and timestamps.
- **Render:** `compile_document()` — a custom structural compiler that processes `@prompt`, `@gate`, and `@loop` annotations in the template, substituting response data with context-aware formatting (blockquotes, attribution, strikethrough for amendments).
- **Template role:** `TEMPLATE-VR.md` is a persistent compiler input — it participates in every compilation, every `qms read`, every checkin. It defines both the authoring flow (prompt sequence) and the output structure.
- **Authoring:** `qms interact` drives a state machine that collects responses, manages loops and gates, and writes to the `.source.json` structured data.

Architecture B's source lives in `.meta/` alongside workflow metadata — mixing authoring data with workflow state.

### 3.3 No User Properties

There is no concept of "user properties" in the metadata sidecar. All metadata fields are system-managed. There is no way for the CLI to track author-provided values separately from workflow state. There is no mechanism for template-driven schema evolution.

---

## 4. Proposed State

### 4.1 One Architecture

Every document in the QMS follows one pattern:

```
Source file (Jinja2 template)  +  .meta/ (data context)  →  Draft (rendered markdown)
```

- **Source file** (`QMS/.source/`): A Jinja2 template. Ranges from trivial (an author-written body with no expressions — identity transform) to complex (`{% for %}` loops, `{% if %}` conditionals, custom filters for blockquoting and amendment trails).

- **`.meta/` data**: The single data store. Contains system metadata, user properties (populated from frontmatter at checkin), and — for interactive documents — structured response data (populated by `qms interact`).

- **Render**: `jinja2.render(source, context)` → draft markdown. One function. Always.

### 4.2 The Spectrum

The difference between document types is the complexity of the Jinja2 template and the richness of the data context:

| Level | Source (Jinja2) | Data in `.meta/` | Input channel |
|-------|----------------|-----------------|---------------|
| **Simple** (SOP, INV) | Author-written body, no expressions | `user_properties` (title, revision_summary) | Frontmatter editing |
| **Variable** (RTM) | Author-written body with `{{ user.qualified_commit }}` expressions | `user_properties` (title, revision_summary, qualified_commit, ...) | Frontmatter editing |
| **Hybrid** | Mix of author-written sections and `{% for %}` compiled sections | `user_properties` + interactive responses | Frontmatter editing + `qms interact` |
| **Interactive** (VR) | Entirely `{% for %}` loops, `{% if %}` conditionals, `{{ response }}` substitutions | `user_properties` + full interactive response tree | Frontmatter editing + `qms interact` |

There is no mode switch. The render engine is the same. The data store is the same. Documents sit at different points on the spectrum based on how much Jinja2 logic their source contains and how much data their `.meta/` holds.

### 4.3 Two Input Channels, One Data Store

Authors populate `.meta/` through two channels:

1. **Frontmatter editing** — The author writes concrete values in the source file's YAML frontmatter. At checkin, these values are written to `user_properties` in `.meta/`. Every document uses this channel.

2. **Interactive engine** — The author provides responses via `qms interact`. The engine writes structured response data to `.meta/`. Only documents whose template defines interactive prompts use this channel.

Both channels write to `.meta/`. A document can use one or both. The render engine doesn't care where the data came from — it builds a context dict from `.meta/` and renders the source Jinja2 template.

### 4.4 Example Source Files

**Simple document (SOP) — identity transform:**
```yaml
---
title: Execution and Evidence Procedures
revision_summary: 'CR-107: Updated for unified document lifecycle'
---

## 1. Purpose

This SOP establishes the procedures for...
```
No Jinja2 expressions. Render is an identity transform for the body. Frontmatter values populate `user_properties` at checkin; system frontmatter is injected at render.

**Variable document (RTM) — expression substitution:**
```yaml
---
title: '{{ user.system_name }} Requirements Traceability Matrix'
revision_summary: 'Updated traceability for v{{ user.rs_version }}'
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

**Interactive document (VR) — full compilation:**
```yaml
---
title: '{{ user.title }}'
revision_summary: Initial verification
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
Entirely Jinja2. The body is compiled from interactive response data in `.meta/`.

---

## 5. Change Description

### 5.1 Universal Source Files: `QMS/.source/`

ALL documents get a source file in `QMS/.source/`. The source is the primary artifact from birth — the draft is always derived.

```
QMS/.source/
  SOP/
    SOP-005/
      SOP-005-source.md              # Simple: author-written body, no expressions
  RTM/
    SDLC-QMS-RTM/
      SDLC-QMS-RTM-source.md        # Variable: body with {{ user.foo }} expressions
  VR/
    CR-091-VR-001/
      CR-091-VR-001-source.md        # Interactive: Jinja2 loops/conditionals
      CR-091-VR-001.source.json      # Interactive response data (relocated from .meta/)
```

**At creation:** The template body is copied into the source file. The draft is a stub: "This document has not been checked in since creation. No rendition is available."

**At checkin:** The source is preserved with Jinja2 expressions intact. The draft is rendered from source + `.meta/` context.

**At checkout:** The workspace copy comes from `.source/`, never from the draft. The source is always the checkout source; the draft is never the checkout source.

### 5.2 Jinja2 Render Engine

One render function replaces all existing render paths:

```python
def render_document(source_body: str, context: dict) -> str:
    """Render a Jinja2 source template with metadata context."""
    env = jinja2.Environment(undefined=jinja2.StrictUndefined)
    env.filters['blockquote'] = blockquote_filter
    env.filters['code_fence'] = code_fence_filter
    env.filters['amendment_trail'] = amendment_trail_filter
    template = env.from_string(source_body)
    return template.render(context)
```

**Context construction:**
```python
context = {
    "user": metadata["user_properties"],          # From frontmatter (all documents)
    "sys": {                                       # From metadata sidecar
        "doc_id": metadata["doc_id"],
        "version": metadata["version"],
        "status": metadata["status"],
        "responsible_user": metadata["responsible_user"],
        "created_date": metadata["created_date"],
        # ... other system fields
    },
    "responses": metadata.get("responses", {}),    # From qms interact (interactive only)
    "loops": metadata.get("loops", {}),            # From qms interact (interactive only)
    "gates": metadata.get("gates", {}),            # From qms interact (interactive only)
}
```

**Syntax mapping from current system to Jinja2:**

| Current | Jinja2 |
|---------|--------|
| `{%user:qualified_commit%}` (proposed, never implemented) | `{{ user.qualified_commit }}` |
| `{%sys:version%}` (proposed, never implemented) | `{{ sys.version }}` |
| `@loop` expansion (VR compiler) | `{% for step in loops.verification_steps %}` |
| `@gate` conditional (VR compiler) | `{% if gates.deficiency_found.value == 'yes' %}` |
| `@prompt` response (VR compiler) | `{{ responses.test_result \| blockquote }}` |
| Amendment trail (VR compiler) | `{{ responses.test_result \| amendment_trail }}` |

**Custom Jinja2 filters** (registered once at engine initialization):
- `blockquote` — wrap in `>` with `*-- author, timestamp*` attribution
- `code_fence` — wrap in triple backticks with optional language tag
- `amendment_trail` — render superseded entries with strikethrough, active entry current
- `default_placeholder` — render `{{PLACEHOLDER}}` when value is null (for stub drafts)

**Documents with no Jinja2 expressions:** The render is an identity transform for the body. The engine processes the source, finds no expressions, and returns the body unchanged. This is the simple-document limiting case.

### 5.3 Template as Living Schema Authority

`TEMPLATE-{TYPE}.md` in `QMS/TEMPLATE/` is the single source of truth for a document type's user property schema. The template's frontmatter declares which user properties exist for that type.

**Schema is applied at every checkout**, not just at creation:
- When a template evolves (fields added or removed), every document of that type picks up the new schema the next time it is checked out.
- All documents of a given type always have the same active schema, matching the current template.
- There is no schema drift between old and new documents of the same type.

**The checkout schema sync flow:**

1. Read current `QMS/TEMPLATE/TEMPLATE-{TYPE}.md`, parse frontmatter for property keys
2. Compare template schema against document's current `user_properties`
3. New keys in template → add to `user_properties` with null values
4. Keys removed from template → move to `archived_properties` with provenance (see Section 5.8)
5. Existing keys → values preserved as-is
6. Update source frontmatter to reflect current schema
7. Copy source to workspace

**Template evolution forces schema compliance.** New fields appear in the document's frontmatter with null values. Checkin is blocked until the author provides concrete values — this is the nature of keeping up with the times.

**Template's two roles:**

1. **Scaffolding (consumed at creation):** The template provides the initial body structure — section headings, placeholder text, document skeleton. This is copied into the source file at creation and then lives there. The template is "dead" for this content after creation.

2. **Schema authority (alive throughout lifecycle):** The template's frontmatter declares the user property keys. At every checkout, the system syncs the document's schema against the current template. This role persists for the document's lifetime.

For interactive documents, the template has a third role: **3. Authoring flow definition.** The template (or a companion workflow spec) defines the prompt sequence, gates, and loops that the interactive engine uses. This is an authoring concern separate from rendering.

### 5.4 Frontmatter as Sole Input Channel

There is no `qms set` command. Authors set user properties by editing frontmatter values in the source file. Checkin reads frontmatter and populates `user_properties` in `.meta/`.

**Source frontmatter = user properties.** The source file's frontmatter contains user property fields only. There is no system-managed frontmatter in the source — that's injected at render time into the draft.

**Draft frontmatter = user properties + system properties.** The rendered draft includes both the author's values and system fields (version, status, dates, etc.), providing a complete view for reviewers.

**This eliminates:**
- `filter_author_frontmatter()` — no longer needed (source has only user properties)
- `write_document_minimal()` frontmatter stripping/restoring — no longer needed
- The "author-maintained" vs. "system-managed" frontmatter distinction — dissolved

**Validation at checkin catches incomplete metadata:**
- Any `{{...}}` placeholders remaining in frontmatter (fields the author never filled in from template scaffolding) produce a validation error
- Any declared property missing entirely from frontmatter (author deleted the line) produces a validation error with specific guidance on what key to restore
- Any null-valued property (from template evolution adding new fields) produces a validation error listing the field and its template origin

### 5.5 Unified Lifecycle Operations

**Create:**
1. Read `TEMPLATE-{TYPE}.md`
2. Copy template body (scaffolding) to source file in `QMS/.source/`
3. Parse template frontmatter → stamp `user_properties` schema into `.meta/` (keys from template, null values)
4. Write stub draft: "This document has not been checked in since creation. No rendition is available."
5. Auto-checkout to workspace (copy source to workspace)

**Checkout:**
1. Schema sync from current template (see Section 5.3)
2. If source file exists in `QMS/.source/` → copy to workspace
3. If no source file exists (pre-existing document) → migration (see Section 5.6)
4. If template defines interactive prompts → initialize/copy interact session

**Checkin:**
1. Parse workspace frontmatter → validate all user property keys present with concrete values (no nulls, no `{{...}}` placeholders, no missing keys)
2. Write frontmatter values to `user_properties` in `.meta/`
3. If interactive session exists → validate all prompts answered, write response data to `.meta/`
4. Save workspace content to `QMS/.source/` (source preserved with Jinja2 expressions intact)
5. Build context from `.meta/`: `{ user: user_properties, sys: system_metadata, responses: ..., loops: ..., gates: ... }`
6. Render: `jinja2.render(source_body, context)` → draft body
7. Prepend rendered frontmatter (user properties + system properties) → save draft

**Read (`qms read`):**
1. Load source from `QMS/.source/`
2. Build context from `.meta/`
3. Render: `jinja2.render(source_body, context)` → display

This replaces the current behavior where `qms read` simply shows the file on disk. Under the unified system, `qms read` always renders live from source + metadata, ensuring the displayed content reflects the current metadata state.

For VR documents, this replaces the current `compile_document()` call with the same Jinja2 render path used by all document types.

### 5.6 Checkout-Triggered Migration

Pre-existing documents (created before the unified system) have no source file and no `user_properties` in their metadata. These documents acquire both at first checkout:

1. System checks `QMS/.source/{TYPE}/{DOC_ID}/{DOC_ID}-source.md` — not found
2. Reads effective/draft content. Strips system frontmatter.
3. **Template schema sync:** Reads current `TEMPLATE-{TYPE}.md`, parses frontmatter for property keys. The template defines the schema — not the document's existing frontmatter.
4. Stamps `user_properties` into metadata from template schema. Values for keys that existed in the document's frontmatter (e.g., `title`, `revision_summary`) are populated from those values. New keys from template evolution get null values.
5. Creates source file from effective body + user-property-only frontmatter (reflecting the synced schema)
6. Copies source to workspace

**Documents never checked out again simply never migrate — and that's fine.** They continue to exist as they are. Migration is lazy, triggered by the first checkout under the new system.

### 5.7 VR Source Consolidation

VR structured source files (`.source.json`) are relocated from `QMS/.meta/` to `QMS/.source/`:

**Before:**
```
QMS/.meta/VR/CR-091-VR-001.source.json
```

**After:**
```
QMS/.source/VR/CR-091-VR-001/CR-091-VR-001.source.json
```

VR source files additionally gain a Jinja2 markdown source (`-source.md`) that defines the rendering template — replacing the current `TEMPLATE-VR.md` + `compile_document()` approach with a standard Jinja2 source file.

**What changes:**
- Source path references in all VR-related commands
- VR compilation replaced by Jinja2 rendering (same output, different engine)
- Interactive response data written to `.meta/` (for render context), not embedded in `.source.json` exclusively

**What does NOT change:**
- `qms interact` authoring workflow — unchanged
- `.interact` session files — still written to workspace
- Interactive engine state machine — unchanged (responses, loops, gates, amendments)
- Response data model — unchanged (values, timestamps, authors, amendment trails)

**Migration:** Existing VR source files in `.meta/` are moved to `.source/` during implementation. The checkout path checks both locations during a transition period.

### 5.8 User Properties and Archived Properties

**`user_properties`** in the metadata sidecar stores all frontmatter-sourced values:

```json
{
  "status": "DRAFT",
  "version": "0.1",
  "user_properties": {
    "title": "QMS CLI Requirements Traceability Matrix",
    "revision_summary": "Updated traceability for v23.0",
    "system_name": "QMS CLI",
    "rs_doc_id": "SDLC-QMS-RS",
    "rs_version": "23.0",
    "qualified_commit": "abc123def456"
  }
}
```

**`archived_properties`** stores values from template fields that have been removed. Values are never silently discarded:

```json
{
  "archived_properties": {
    "old_field_name": {
      "value": "the original value",
      "archived_at": "2026-02-26",
      "template_version": "10.0"
    }
  }
}
```

The archived value is still in the metadata, still auditable, but not part of the active schema.

### 5.9 Archive Behavior

When a document transitions to EFFECTIVE, the rendered draft is copied to the effective location. The source file remains in `.source/` as the canonical representation of the current effective content. Archived versions (in `.archive/`) are rendered snapshots.

### 5.10 MCP Tools

- `qms_read` updated to use Jinja2 rendering
- `qms_checkout` updated for schema sync and migration
- `qms_checkin` updated for frontmatter validation and Jinja2 rendering
- `qms_create` updated for source-first creation

---

## 6. Justification

- **One architecture, not three.** The current system has three separate document architectures with different storage models, render pipelines, and lifecycle operations. Maintaining three parallel systems creates compounding complexity. The unified architecture has one render engine, one data store, one source location, and one lifecycle flow.

- **Spectrum, not modes.** Documents range from zero Jinja2 (SOP — identity transform) through variable expressions (RTM) through hybrid to fully compiled (VR). No binary dispatch, no mode switch, no special cases. Adding a new document type doesn't require choosing an architecture — it sits naturally on the spectrum.

- **Draft is always derived.** The source is the primary artifact. The draft is always a product of rendering. This eliminates the conceptual confusion of Architecture A where the draft is simultaneously the source and the output.

- **Living schema authority.** Templates define the user property schema for their document type and enforce it at every checkout. Template evolution propagates automatically. No schema drift between documents of the same type.

- **Non-destructive authoring.** Source files preserve Jinja2 expressions across checkout/checkin cycles. The author always gets back what they wrote. Values that should be system-maintained (commit hashes, version references) are metadata-backed rather than manually maintained.

- **Clean separation of concerns.** `.meta/` = workflow state and data context. `.source/` = what the author wrote. `QMS/{TYPE}/` = derived renditions for review and approval.

- **Foundation for interactive engine redesign.** The grand unification and the interactive engine redesign (Session-2026-02-22-004) are the same design viewed from different angles: workflow specs define the authoring layer, Jinja2 sources define the rendering layer, `.meta/` holds the data layer.

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `qms-cli/qms_render.py` | Create | Jinja2 render engine, custom filters, context builder |
| `qms-cli/qms_source.py` | Create | Source path utilities, source read/write |
| `qms-cli/qms_schema.py` | Create | Template schema parsing, schema sync, archival logic |
| `qms-cli/commands/create.py` | Modify | Source-first creation, stub draft, schema stamping |
| `qms-cli/commands/checkin.py` | Modify | Frontmatter validation, user_properties population, Jinja2 rendering, source preservation |
| `qms-cli/commands/checkout.py` | Modify | Source-aware checkout, schema sync, migration |
| `qms-cli/commands/read.py` | Modify | Jinja2-based rendering for all document types |
| `qms-cli/commands/interact.py` | Modify | Response data written to `.meta/` for render context |
| `qms-cli/qms_docs.py` | Modify | Eliminate `filter_author_frontmatter()`, `write_document_minimal()` frontmatter stripping/restoring |
| `qms-cli/qms_config.py` | Modify | Add Jinja2 dependency |
| `qms-cli/qms.py` | Modify | Import new modules |
| `qms-cli/qms_mcp/tools.py` | Modify | Update MCP tools for new lifecycle |
| `qms-cli/tests/test_render.py` | Create | Jinja2 render engine tests |
| `qms-cli/tests/test_schema.py` | Create | Schema sync and archival tests |
| `qms-cli/tests/test_source.py` | Create | Source system tests |
| `qms-cli/tests/test_migration.py` | Create | Pre-existing document migration tests |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| SDLC-QMS-RS | Modify | Add requirements for Jinja2 render engine, universal source files, schema sync, migration |
| SDLC-QMS-RTM | Modify | Add verification evidence for new requirements |
| All `TEMPLATE-{TYPE}.md` files | Modify | Ensure frontmatter declares user property schema |

### 7.3 Dependencies

- **Jinja2 package:** New Python dependency (`jinja2`). Must be added to requirements.
- **No external service dependencies.**

### 7.4 Other Impacts

**All document types affected.** This is a fundamental change to how documents are created, checked out, checked in, and read. However, the change is backward-compatible in the sense that:
- Pre-existing documents work identically until first checkout (lazy migration)
- Simple documents with no Jinja2 expressions produce identical output (identity transform)
- The interactive authoring workflow (`qms interact`) is unchanged from the author's perspective

**`filter_author_frontmatter()` and `write_document_minimal()` eliminated.** Code that calls these functions must be updated. The frontmatter stripping/restoring dance is replaced by the clean separation: source has user properties only, draft has user + system properties.

**VR compilation replaced.** `compile_document()` is replaced by `jinja2.render()`. The output must be verified to be identical for existing VR documents.

This CR is a prerequisite for CR-106 (System Governance), which defines RTM qualification metadata fields as user properties rendered via Jinja2 expressions.

### 7.5 Development Controls

This CR implements changes to qms-cli, a controlled submodule. Development follows established controls:

1. **Test environment isolation:** Development in `.test-env/` (local) or `/projects/` (containerized agents)
2. **Branch isolation:** All development on branch `cr-107`
3. **Write protection:** `.claude/settings.local.json` blocks direct writes to `qms-cli/`
4. **Qualification required:** All new/modified requirements must have passing tests before merge
5. **CI verification:** Tests must pass on GitHub Actions for dev branch
6. **PR gate:** Changes merge to main only via PR after RS/RTM approval
7. **Submodule update:** Parent repo updates pointer only after PR merge

### 7.6 Qualified State Continuity

| Phase | main branch | RS/RTM Status | Qualified Release |
|-------|-------------|---------------|-------------------|
| Before CR | Current commit (309f217) | EFFECTIVE v22.0 / v27.0 | CLI-18 |
| During execution | Unchanged | DRAFT (checked out) | CLI-18 (unchanged) |
| Post-approval | Merged from cr-107 | EFFECTIVE v23.0 / v28.0 | CLI-19 |

---

## 8. Testing Summary

### Automated Verification

**Jinja2 render engine:**
- Simple source (no expressions) → identity transform for body
- Source with `{{ user.foo }}` expressions → values substituted from user_properties
- Source with `{{ sys.bar }}` expressions → values substituted from system metadata
- Source with `{% for %}` loops → iterations expanded from response data
- Source with `{% if %}` conditionals → branches evaluated from gate data
- Source with custom filters (`blockquote`, `amendment_trail`, `code_fence`) → correct formatting
- Undefined variable in source with `StrictUndefined` → clear error message
- Empty context (no user_properties, no responses) → identity transform

**Universal source files:**
- Create document → source file created in `QMS/.source/`, draft is stub
- Checkin → source preserved with Jinja2 expressions, draft rendered with concrete values
- Checkout → workspace copy comes from source, not draft
- Source body with zero Jinja2 → draft body identical to source body
- Source body with expressions → draft body has concrete values

**Template schema authority:**
- Create document → user_properties schema matches template frontmatter
- Checkout with unchanged template → no schema modification
- Checkout after template adds field → new field in user_properties (null value)
- Checkout after template removes field → value moved to archived_properties with provenance
- Checkin with null-valued property → validation error (blocked)
- Checkin with `{{...}}` placeholder in frontmatter → validation error
- Checkin with missing frontmatter key → validation error with guidance

**Frontmatter as sole input channel:**
- Checkin populates user_properties from source frontmatter values
- Draft frontmatter includes user properties + system properties
- Source frontmatter contains user properties only (no system fields)
- All frontmatter fields treated equally (title, revision_summary not special)

**Checkout-triggered migration:**
- Pre-existing document (no source, no user_properties) → source created, schema stamped
- Existing frontmatter values (title, revision_summary) → populated into user_properties
- Template has fields beyond existing frontmatter → null values, checkin blocked until filled
- Post-migration checkout → source-first flow (normal behavior)

**VR source consolidation:**
- VR checkout loads `.source.json` from `QMS/.source/` (new location)
- VR checkin saves `.source.json` to `QMS/.source/` (new location)
- VR read renders via Jinja2 from source
- Fallback: if `.source.json` not in `.source/`, check `.meta/` (migration compatibility)
- VR output via Jinja2 matches previous `compile_document()` output

**Archived properties:**
- Template removes field → archived with value, timestamp, template version
- Archived property still present in metadata (auditable)
- Archived property not in active schema (not in source frontmatter)
- Multiple archival events → each tracked independently

**Regression:**
- Full existing test suite passes
- Non-interactive documents: unchanged authoring experience
- Interactive documents: full lifecycle unchanged (interact → respond → amend → compile)
- Document approval/effective/archive flow: unchanged

### Integration Verification

- **Full lifecycle (new document):** Create → auto-checkout → edit workspace (fill frontmatter, write body) → checkin → verify source preserved, draft rendered → `qms read` (verify live render) → checkout again → verify workspace has source with expressions → update frontmatter values → checkin → verify new rendered values
- **Full lifecycle (pre-existing document migration):** Checkout pre-existing SOP → verify source created, schema stamped → edit → checkin → verify user_properties populated → route for review → checkout after edits requested → verify source-first checkout → checkin → route for approval → approve → verify effective
- **VR lifecycle under unified system:** Create VR → interact → respond → checkin → verify Jinja2 render matches expected output → checkout → amend response → checkin → verify amendment trail rendered correctly
- **Template evolution:** Create document → checkin → modify template (add field) → checkout → verify new field appears with null value → fill field → checkin → verify new field in rendered output
- **Schema archival:** Create document → checkin with field X → modify template (remove field X) → checkout → verify field X archived with provenance → checkin → verify field X not in rendered output

---

## 9. Implementation Plan

### 9.1 Phase 1: Pre-Execution Baseline

1. Commit and push project repository to capture pre-execution state

### 9.2 Phase 2: Test Environment Setup

1. Clone qms-cli to `.test-env/`
2. Create and checkout branch `cr-107`
3. Add `jinja2` to requirements
4. Verify clean test environment (existing tests pass)

### 9.3 Phase 3: Requirements (RS Update)

1. Checkout SDLC-QMS-RS
2. Add requirements for Jinja2 render engine, universal source files, template schema authority, frontmatter validation, checkout-triggered migration, archived properties
3. Checkin RS, route for review and approval

### 9.4 Phase 4: Implementation — Render Engine and Source System

1. Create `qms_render.py` — Jinja2 render engine with custom filters, context builder
2. Create `qms_source.py` — source path utilities, source read/write
3. Create `qms_schema.py` — template schema parsing, schema comparison, archival logic
4. Create `tests/test_render.py` — render engine unit tests
5. Create `tests/test_schema.py` — schema sync and archival unit tests
6. Create `tests/test_source.py` — source system unit tests

### 9.5 Phase 5: Implementation — Lifecycle Operations

1. Modify `commands/create.py` — source-first creation, stub draft, schema stamping
2. Modify `commands/checkin.py` — frontmatter validation, user_properties population, Jinja2 rendering, source preservation
3. Modify `commands/checkout.py` — source-aware checkout, schema sync, migration
4. Modify `commands/read.py` — Jinja2-based rendering for all document types
5. Modify `qms_docs.py` — eliminate `filter_author_frontmatter()`, `write_document_minimal()` frontmatter stripping/restoring
6. Create `tests/test_migration.py` — pre-existing document migration tests

### 9.6 Phase 6: Implementation — VR Unification

1. Create Jinja2 source templates for VR documents (replacing `@prompt`/`@gate`/`@loop` annotations with Jinja2 syntax)
2. Modify `commands/interact.py` — write response data to `.meta/` for render context
3. Update VR source paths to use `QMS/.source/`
4. Add migration fallback (check `.meta/` if `.source/` not found)
5. Verify Jinja2 VR render output matches `compile_document()` output

### 9.7 Phase 7: Template Updates

1. Update all `TEMPLATE-{TYPE}.md` files to declare user property schema in frontmatter
2. Ensure templates follow the unified format (frontmatter = schema, body = scaffolding)

### 9.8 Phase 8: Qualification

1. Run full test suite, verify all tests pass
2. Push to dev branch
3. Verify GitHub Actions CI passes
4. Document qualified commit hash

### 9.9 Phase 9: Integration Verification

1. Full lifecycle: new document creation through approval
2. Pre-existing document migration lifecycle
3. VR lifecycle under unified system
4. Template evolution and schema archival
5. Regression: existing document types unchanged behavior

### 9.10 Phase 10: RTM Update and Approval

1. Checkout SDLC-QMS-RTM
2. Add verification evidence for new requirements
3. Checkin RTM, route for review and approval

### 9.11 Phase 11: MCP Tools

1. Update MCP tools for unified lifecycle
2. Verify MCP tools work via test invocations

### 9.12 Phase 12: Merge and Submodule Update

**Prerequisite:** RS and RTM must both be EFFECTIVE.

1. Create PR to merge cr-107 to main
2. Merge via merge commit (--no-ff)
3. Verify qualified commit is reachable on main
4. Update submodule pointer in parent repo

### 9.13 Phase 13: Production Migration

1. Move existing VR `.source.json` files from `QMS/.meta/` to `QMS/.source/`
2. Verify all VR documents read correctly from new location
3. Remove migration fallback path (or leave for safety)

### 9.14 Phase 14: Post-Execution Baseline

1. Commit and push project repository to capture post-execution state

---

## 10. Execution

| EI | Task Description | VR | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|----|-------------------|--------------|---------------------|
| EI-1 | Pre-execution baseline: commit and push | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | Set up test environment, create branch cr-107, add Jinja2 dependency | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Update SDLC-QMS-RS with unified lifecycle requirements | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-4 | Implement Jinja2 render engine (`qms_render.py`), source utilities (`qms_source.py`), schema system (`qms_schema.py`) with unit tests | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-5 | Implement unified lifecycle operations: create, checkout, checkin, read modifications; eliminate frontmatter stripping | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-6 | Implement VR unification: Jinja2 VR source templates, response data in `.meta/`, source path migration | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-7 | Update all `TEMPLATE-{TYPE}.md` files for user property schema declarations | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-8 | Run full test suite, push to cr-107, verify CI | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-9 | Integration verification: full lifecycles, migration, VR, template evolution, regression | Yes | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-10 | Update SDLC-QMS-RTM with verification evidence | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-11 | Update MCP tools for unified lifecycle | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-12 | Merge gate: PR, merge (--no-ff), submodule update | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-13 | VR source migration: move existing `.source.json` files from `.meta/` to `.source/` in production | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-14 | Post-execution baseline: commit and push | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

---

### Execution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| [COMMENT] | [PERFORMER] - [DATE] |

---

## 11. Execution Summary

[EXECUTION_SUMMARY]

---

## 12. References

- **Dependent CR:** CR-106 (System Governance) — first consumer of Jinja2 template variables for RTM qualification metadata
- **Interactive engine redesign:** Session-2026-02-22-004 — same design from the authoring-layer perspective
- **Design documents:** Session-2026-02-26-002:
  - `grand-unification-U-prime-B.md` — unified architecture design
  - `unified-document-creation-flow.md` — lifecycle traces for new and pre-existing documents
  - `genotype-phenotype-analysis.md` — three-architecture analysis (superseded by unification)
- **Existing VR source system:** `interact_source.py`, `interact_engine.py`, `interact_compiler.py`

---

**END OF DOCUMENT**
