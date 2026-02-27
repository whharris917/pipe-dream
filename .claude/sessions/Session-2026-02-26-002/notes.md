# Session-2026-02-26-002

## Current State (last updated: post CR-106 alignment)
- **Active documents:** CR-107 (DRAFT v0.1, content v1.0 — grand unification design), CR-106 (DRAFT v0.1, content v0.4 — aligned with CR-107 redesign)
- **Both CRs up to date.** CR-107 reflects grand unification. CR-106 aligned: all `qms set` → frontmatter editing, `{%user:...%}` → Jinja2, CR-107 title/description updated.
- **Design artifacts:** `unified-document-creation-flow.md`, `grand-unification-U-prime-B.md`, `genotype-phenotype-analysis.md`, `TEMPLATE-RTM.md`, `TEMPLATE-RTM-v2.md` (all in session folder)
- **Next:** Route CRs for review, or Lead direction

## Progress Log

### Session Start
- Previous session: Session-2026-02-26-001 — Extensive CR-106 design refinement (22 decisions), draft checked in

### Design Refinement: Template/Source System Separation
Lead identified that:
1. `{%variable%}` values should be settable any time via `qms set`, not just at checkin via flags
2. Checkin resolving `{%var%}` → bare value is destructive — next checkout loses the variable
3. This implies a source file system (`QMS/.source/`) for non-destructive round-tripping
4. The template/source system is general infrastructure, not system-governance-specific → separate CR

### CR-106 Updated (v0.1)
- Removed all template variable content, checkin flags, delegated to CR-107
- Core system governance design unchanged

### CR-107 Created and Drafted (v0.1)
- Title: "Document Source System: source preservation, metadata properties, and template variable rendering"

### Lead Refinements (second round)
Lead directed four refinements:
1. **`qms set` scoped to user-input only** — Writes exclusively to `metadata.user_properties`, not freeform metadata. Structurally scoped (no blocklist needed).
2. **`qms read` shows last checked-in file** — `qms read --preview` for live rendering from source + current metadata.
3. **`{%user:...%}` / `{%sys:...%}` syntax** — Explicit, self-documenting prefixes. User-input resolved from `user_properties`, system-computed from metadata fields.
4. **VR source consolidation** — Move `.source.json` from `.meta/` to `.source/` (storage only, don't touch `.interact` engine).

### CR-107 Updated (v0.2 content)
All four refinements applied. 12 EIs including VR source consolidation and migration.

### CR-106 Updated (v0.2 content)
Aligned with CR-107 v0.2:
- Template variable syntax → `{%user:...%}`
- RTM qualification fields stored in `user_properties`
- `qms_meta.py` scope reduced to `target_systems` only
- Post-approval hook reads from RTM `user_properties`

### Project State Updated
- Section 1: Updated to reflect two-CR design (CR-107 prerequisite, CR-106 consumer)
- Section 2 (Arc): Updated final paragraph to cover both CRs
- Section 4 (Open Documents): Added CR-107, updated CR-106 description
- Section 5 (Forward Plan): Added "Next Up" section with CR-107 → CR-106 sequencing

### Logic & Backward Compatibility Review (post-compaction)
Lead requested full review of both CRs. Explored codebase with 3 agents:
- Checkin/checkout/read flow analysis
- Existing document conflict search (`{%` pattern across all QMS/seed/manual/Python)
- Workflow, metadata, permissions infrastructure

**Verdict: No backward compatibility issues.** Zero `{%` matches in existing effective documents, seed templates, or Python code. Template syntax is completely distinct from existing `{{...}}` patterns.

**3 issues found and fixed:**
1. **Code-block false positives (CR-107)** — Detection regex would match `{%user:...%}` inside code blocks/inline code (e.g., in CR design docs). Added code-block awareness requirement to Section 5.2 and 5.4.
2. **CR-106 Qualified State Table** — Both CRs showed identical baselines. Updated CR-106 Section 7.5 to reflect post-CR-107 state (CLI-19 baseline → CLI-20 post-approval).
3. **`qms read --preview` cross-user workspace** — Clarified Section 5.6: preview always renders from `.source/` file, not from any user's workspace.

Both CRs updated to v0.3 content and checked in.

### Document System Genotype-Phenotype Analysis

Lead requested a systematic analysis of the document system along two axes: now vs. proposed, and genotype (representation) vs. phenotype (rendering). Full analysis saved to `.claude/sessions/Session-2026-02-26-002/genotype-phenotype-analysis.md`.

**Central insight: The QMS has three document architectures:**

1. **Architecture A (Direct)** — CR, SOP, INV, etc. No genotype-phenotype separation. Draft = document. Template is a one-time mold at creation (`{{TITLE}}` substituted once, then template plays no further role). `write_document_minimal()` strips system frontmatter for workspace; body passes through untouched.

2. **Architecture B (Interactive)** — VR only. Full separation. Structured JSON source (`.source.json`) → compiled markdown via `compile_document()`. Template (`TEMPLATE-VR.md` with `@prompt`/`@gate`/`@loop` annotations) is a persistent compiler input that participates in every checkout/read/checkin. Compilation is deterministic, stateless, and lossy (cannot reconstruct source from output).

3. **Architecture C (Template-Variable, CR-107)** — Any document, opt-in via `{%user:...%}` / `{%sys:...%}` in content. Partial separation: markdown with variables (genotype) → markdown with concrete values (phenotype). Lightweight string substitution, no separate template artifact. Strict superset of Architecture A — documents without variables are completely unaffected.

**Key architectural contributions of CR-107:**
- `QMS/.source/` directory unifies genotype storage (Architecture B's `.source.json` relocated from `.meta/`, Architecture C's `-source.md` created here)
- Clean separation: `.meta/` = workflow state, `.source/` = what the author wrote
- `user_properties` in metadata sidecar bridges metadata layer to Architecture C genotype
- Templates have radically different roles: A = one-time mold, B = persistent compiler, C = none (variables are inline)

### CR-107 Scope Expansion: Unified Document Lifecycle

Lead directed a fundamental redesign of CR-107. Rather than adding a third document architecture (C) alongside the existing two (A, B), CR-107 should unify A and C into a single system where A is a limiting case. Key design decisions evolved through iterative discussion:

**Decision 1: Universal source files.** ALL documents get a `-source.md` in `QMS/.source/`, not just documents with `{%...%}` variables. The rendered draft is always a derived artifact. For documents with no variables, the resolution step is an identity transform. No opt-in, no detection.

**Decision 2: Closed variable set.** Authors cannot define new `{%...%}` variables. They can only reference keys that exist in the document's metadata (`{%sys:...%}` for system fields, `{%user:...%}` for user properties). Variables are metadata projections, not author-defined macros.

**Decision 3: Frontmatter is the only input channel.** The `qms set` command is eliminated. Frontmatter in the source file IS the mechanism for setting user property values. Editing `qualified_commit: abc123` in frontmatter is equivalent to the now-removed `qms set DOC qualified_commit abc123`. One input path, no precedence questions.

**Decision 4: Frontmatter defines schema.** The template's example frontmatter declares the user property keys for that document type. `{{...}}` placeholders in frontmatter are one-time scaffolding; authors replace them with concrete values. Unresolved `{{...}}` placeholders at checkin produce a validation error.

**Decision 5: Draft is always derived.** At creation, before first checkin, the draft is a stub ("No rendition available"). The source is the primary artifact from birth. The draft is never an input to any operation.

**Decision 6: Template as living schema authority.** Schema is NOT frozen at creation. At every checkout, the system reads the current `TEMPLATE-{TYPE}.md` and syncs the document's schema. New template fields appear as null-valued properties (checkin blocked until filled). Removed template fields are archived with provenance (value, timestamp, template version) — never silently discarded.

**Decision 7: Checkout-triggered migration.** Pre-existing documents (created before the unified system) acquire source files and user property schemas at first checkout. The template determines the schema, not the document's existing frontmatter. Existing frontmatter values populate matching keys; new template keys get null values. Documents never checked out again simply never migrate.

**Decision 8: All frontmatter fields are user properties.** `title` and `revision_summary` are not special — they're user properties like `qualified_commit`. The distinction between "author-maintained" and "system-managed" frontmatter dissolves. Source frontmatter = user properties. Rendered draft frontmatter = user properties + system properties. `filter_author_frontmatter()` and `write_document_minimal()` stripping/restoring are eliminated.

### Grand Unification: U' + B → U (Jinja2)

After establishing the U' design (A-C unification), Lead posed the question: how does B (interactive/VR) become a limiting case of U rather than a separate architecture?

**Initial attempt:** Proposed a two-layer source model (markdown source + JSON source) with a merge-based render function. This had B as a mode rather than a limiting case.

**Lead's insight: Jinja2 is the answer.** Our custom `{%user:foo%}` syntax is already essentially Jinja2 (`{{ user.foo }}`). The VR compilation operations (loops, conditionals, value substitution, amendment rendering) are all Jinja2 primitives or custom filters. One render engine handles everything.

**Key realization: data always comes from `.meta/`.** This was already settled in the U' design (frontmatter populates `.meta/` at checkin). For interactive documents, the interact engine is simply another input channel to the same `.meta/` data store. The render engine doesn't care where the data came from — it builds a context dict from `.meta/` and calls `jinja2.render(source, context)`.

**Decision 9: Jinja2 as unified render engine.** Replace both `resolve_variables()` and `compile_document()` with `jinja2.render(source, context)`. Custom filters for blockquoting, amendment trails, code fencing. Source files are Jinja2 templates ranging from trivial (no expressions) to complex (loops, conditionals).

**Decision 10: Two input channels, one data store.** Frontmatter editing and `qms interact` are both input channels to `.meta/`. A document can use one or both. The render engine is agnostic to input mechanism.

**Decision 11: Spectrum, not modes.** Documents range from zero Jinja2 complexity (SOP with no expressions — identity transform) through variable expressions (RTM with `{{ user.qualified_commit }}`) through hybrid (some direct body + some compiled sections) to fully compiled (VR — entire body is Jinja2 loops/conditionals). No binary dispatch, no mode switch.

**Connection to interactive engine redesign:** The grand unification and the interactive engine redesign (Session-2026-02-22-004) are the same design viewed from different angles. Workflow specs = authoring layer. Jinja2 source = rendering layer. `.meta/` response data = data layer.

**Design documents produced:**
- `unified-document-creation-flow.md` — Full lifecycle traces for new documents and pre-existing migration
- `grand-unification-U-prime-B.md` — Grand unification design: Jinja2 render, unified data store, spectrum model
- `genotype-phenotype-analysis.md` — Three-architecture analysis (superseded by unification, retained for historical context)
- `TEMPLATE-RTM.md` / `TEMPLATE-RTM-v2.md` — Working template examples showing variable system

### CR-107 Rewrite (post-compaction)

Completely rewrote CR-107 draft to reflect the grand unification design. Key changes from v0.3:
- **Title:** "Document Source System" → "Unified Document Lifecycle: Jinja2 render engine, universal source files, and living schema authority"
- **`qms set` eliminated:** Frontmatter is the sole input channel (Decision 3)
- **Variable syntax:** `{%user:...%}` → Jinja2 `{{ user.foo }}` (Decision 9)
- **Universal source files:** ALL documents get source files, not just those with variables (Decision 1)
- **Draft always derived:** Stub at creation, rendered after checkin (Decision 5)
- **Living schema:** Template synced at every checkout, archived_properties for removed fields (Decisions 6, 10)
- **All frontmatter = user properties:** title/revision_summary not special, filter_author_frontmatter eliminated (Decision 8)
- **VR unification:** compile_document() replaced by Jinja2, same render path for all types (Decision 9)
- **14 EIs** (up from 12): added Jinja2 dependency, VR unification, template updates as separate phases
- **New files:** qms_render.py (Jinja2 engine), qms_schema.py (schema sync/archival), test_migration.py
- Checked in as v0.1 (content v1.0)

### CR-106 Alignment (post-compaction)

Updated CR-106 to align with CR-107 grand unification redesign. Changes:
- **`qms set` eliminated:** All 12+ references to `qms set` replaced with frontmatter editing workflow
- **Variable syntax:** `{%user:...%}` / `{%sys:...%}` → Jinja2 `{{ user.foo }}` / `{{ sys.bar }}`
- **CR-107 prerequisite:** Updated title from "Document Source System" to "Unified Document Lifecycle", updated dependency description
- **Section 5.5 (RTM Metadata):** Rewrote to describe frontmatter-based qualification workflow instead of `qms set`-based
- **Section 7.1/7.3/9.4:** `qms_meta.py` → `commands/create.py` for `target_systems` (CR-107 eliminates `qms_meta.py` frontmatter functions)
- **Testing/Integration/Execution:** All `qms set` steps → "edit source frontmatter"
- **References:** CR-107 title updated
- Checked in as v0.1 (content v0.4)
