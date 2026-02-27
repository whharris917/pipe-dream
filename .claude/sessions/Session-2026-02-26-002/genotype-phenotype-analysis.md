# The QMS Document System: A Genotype-Phenotype Analysis

## Context

This document maps the QMS document system along two axes:

1. **Now vs. Proposed** — The current system vs. what CR-107 (Document Source System) introduces
2. **Genotype vs. Phenotype** — How documents are *represented* (source, internal state) vs. how they are *rendered* (user-facing output)

The central insight is that the QMS currently has **two completely different document architectures** — one for non-interactive documents and one for VR interactive documents — and CR-107 introduces a third that bridges the gap between them.

---

## The Three Architectures

### Architecture A: Direct Documents (Now — CR, SOP, INV, VAR, ADD, RS, RTM)

**No genotype-phenotype separation.** The draft *is* the document.

```
Author writes markdown
        │
        ▼
   ┌─────────┐     checkout     ┌───────────┐
   │  QMS/    │ ──────────────► │ workspace/ │  ◄── author edits here
   │  draft   │ ◄────────────── │   copy     │
   └─────────┘     checkin      └───────────┘
        │
        ▼ (on approval)
   ┌─────────┐
   │  QMS/    │
   │ effective│
   └─────────┘
```

**Genotype artifacts:**
| Artifact | Location | Role |
|----------|----------|------|
| Draft markdown | `QMS/{TYPE}/{DOC_ID}/{DOC_ID}-draft.md` | The document itself |
| Workspace copy | `.claude/users/{user}/workspace/{DOC_ID}.md` | Author's working copy (identical format) |

**Phenotype artifacts:**
| Artifact | Location | Role |
|----------|----------|------|
| Effective markdown | `QMS/{TYPE}/{DOC_ID}/{DOC_ID}.md` | Published document (copy of draft at approval) |
| Archived version | `.archive/{TYPE}/{DOC_ID}/{DOC_ID}-v{X.Y}.md` | Immutable historical snapshot |

**Key characteristic:** Genotype = phenotype. What the author writes is exactly what the reviewer sees, what gets approved, and what becomes effective. There is no transformation, no compilation, no rendering step. The `write_document_minimal()` function strips system-managed frontmatter fields when writing to workspace, and restores them at checkin — but the *body content* passes through untouched.

**Template role:** `TEMPLATE-{TYPE}.md` (e.g., `TEMPLATE-CR.md`) provides initial scaffolding at document creation time via `load_template_for_type()`. Placeholders like `{{TITLE}}` and `CR-XXX` are substituted once at creation, then the template plays no further role. The template is a *mold*, not a *compiler* — it shapes the initial form but doesn't participate in subsequent operations.

---

### Architecture B: Interactive Documents (Now — VR only)

**Full genotype-phenotype separation.** The source is structured JSON; the output is compiled markdown.

```
                              ┌──────────────┐
                              │  TEMPLATE-VR │  (state machine definition)
                              └──────┬───────┘
                                     │ parse
                                     ▼
┌──────────────┐   checkout    ┌───────────┐   interact    ┌───────────┐
│ .meta/VR/    │ ────────────► │ workspace/│ ◄───────────► │ interact  │
│ .source.json │               │ .interact │               │  engine   │
└──────────────┘               └─────┬─────┘               └───────────┘
                                     │ checkin
                              ┌──────┴──────┐
                              │  compile()  │
                              └──────┬──────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                                  ▼
             ┌──────────┐                      ┌──────────────┐
             │  QMS/VR/ │                      │  .meta/VR/   │
             │ draft.md │                      │ .source.json │
             └──────────┘                      └──────────────┘
              (phenotype)                       (genotype saved)
```

**Genotype artifacts:**
| Artifact | Location | Format | Role |
|----------|----------|--------|------|
| Source data | `QMS/.meta/VR/{DOC_ID}.source.json` | Structured JSON | Canonical representation: responses, loops, gates, metadata |
| Session file | `.claude/users/{user}/workspace/{DOC_ID}.interact` | Structured JSON (same schema) | Transient working copy during authoring |
| Template | `seed/templates/TEMPLATE-VR.md` | Annotated markdown with `@prompt`, `@gate`, `@loop` tags | State machine definition + output structure |

**Phenotype artifacts:**
| Artifact | Location | Format | Role |
|----------|----------|--------|------|
| Compiled draft | `QMS/VR/{DOC_ID}/{DOC_ID}-draft.md` | Markdown | Deterministically compiled from source + template |
| Workspace placeholder | `.claude/users/{user}/workspace/{DOC_ID}.md` | Markdown | Stub saying "use `qms interact`" |

**Key characteristic:** The genotype and phenotype are radically different formats. The source is a JSON tree of prompt responses with amendment trails, timestamps, and commit hashes. The phenotype is flowing markdown with blockquoted responses, attribution lines, strikethrough amendments, and numbered loop expansions. The `compile_document()` function is the bridge — it is:
- **Deterministic:** same source + same template = same output, always
- **Stateless:** no side effects, no external dependencies
- **Lossy in reverse:** you cannot reconstruct the source from the compiled output (the template structure, guidance text, and graph topology are stripped)

**The template's role here is fundamentally different from Architecture A.** In Architecture A, the template is a one-time mold. In Architecture B, the template is a **persistent compiler input** — it participates in every compilation, every `qms read`, every checkin. It defines both the authoring flow (prompt sequence, gates, loops) and the output structure (section headings, table layouts, subsection numbering). The source data fills the template's slots; the template defines the slots' shapes.

**The `.source.json` data model:**

```
source
  ├── doc_id, template, template_version     (identity)
  ├── cursor, cursor_context                 (authoring position)
  ├── metadata                               (author-editable: title, date, performer)
  │     └── auto-injected at compile time if missing
  ├── responses                              (append-only per prompt)
  │     └── prompt_id → [ {value, author, timestamp, reason?, commit?}, ... ]
  │     └── loop prompts: prompt_id.N → [ ... ]
  ├── loops                                  (iteration tracking)
  │     └── loop_name → {iterations, closed, reopenings: [...]}
  └── gates                                  (branching decisions)
        └── gate_id → {value, timestamp}
```

**Compilation pipeline:**
1. Strip template preamble (template's own frontmatter)
2. Extract structure, strip `@prompt`/`@gate`/`@loop` tags and guidance text
3. Auto-inject metadata (`date`, `performer`, `performed_date` from response timestamps)
4. Substitute `{{placeholder}}` — context-aware:
   - Table rows: value only, no attribution
   - Block context: blockquoted value with `*-- author, timestamp*` attribution
   - Amendments: superseded entries get strikethrough; active entry is current
5. Expand loops: duplicate loop block N times, substitute iteration-indexed responses
6. Normalize whitespace

---

### Architecture C: Template-Variable Documents (Proposed — CR-107)

**Partial genotype-phenotype separation.** The source is markdown with embedded variables; the output is markdown with concrete values.

```
Author writes markdown with {%user:...%} and {%sys:...%} variables
        │
        │  qms set DOC PROP VALUE
        │  (writes to metadata.user_properties)
        │
        ▼
   ┌───────────┐     checkout     ┌───────────┐
   │ .source/  │  (prefers src) ► │ workspace/ │  ◄── author edits here
   │ -source.md│                  │   copy     │      (variables visible)
   └───────────┘                  └─────┬─────┘
                                        │ checkin
                                 ┌──────┴──────┐
                                 │  resolve()  │
                                 └──────┬──────┘
                                        │
                       ┌────────────────┼────────────────┐
                       ▼                                  ▼
                ┌──────────┐                      ┌──────────────┐
                │  QMS/    │                      │  .source/    │
                │  draft   │                      │  -source.md  │
                └──────────┘                      └──────────────┘
                 (phenotype:                       (genotype saved:
                  concrete values)                  variables intact)
```

**Genotype artifacts:**
| Artifact | Location | Format | Role |
|----------|----------|--------|------|
| Source markdown | `QMS/.source/{TYPE}/{DOC_ID}/{DOC_ID}-source.md` | Markdown with `{%user:...%}` / `{%sys:...%}` | Canonical representation with variables intact |
| User properties | `QMS/.meta/{TYPE}/{DOC_ID}.json` → `user_properties` | JSON within metadata sidecar | Values for `{%user:...%}` variables, set via `qms set` |

**Phenotype artifacts:**
| Artifact | Location | Format | Role |
|----------|----------|--------|------|
| Rendered draft | `QMS/{TYPE}/{DOC_ID}/{DOC_ID}-draft.md` | Markdown with concrete values | What reviewers see |
| Preview | stdout of `qms read --preview` | Markdown (transient) | Live rendering from source + current metadata |

**Key characteristic:** This architecture sits between A and B. Like A, both genotype and phenotype are markdown — the transformation is lightweight (string substitution, not structural compilation). Like B, the genotype preserves information that the phenotype loses (the variable names). The resolution function is:
- **Deterministic:** same source + same metadata = same output
- **Reversible (in principle):** the source is preserved alongside the rendered output; no information is lost
- **Code-block-aware:** variables inside fenced code blocks and inline code are treated as literal text

**The two variable categories:**

| Category | Syntax | Source of values | Set by |
|----------|--------|-----------------|--------|
| User-input | `{%user:property%}` | `metadata.user_properties[property]` | Author, via `qms set` |
| System-computed | `{%sys:property%}` | `metadata[property]` or computed | CLI, automatically |

**Key difference from Architecture B:** There is no separate "template" artifact. The source markdown *is* the template — the variables are embedded inline in the document the author writes. There's no state machine, no prompt graph, no compilation pipeline. Just find-and-replace with metadata lookup.

**Opt-in behavior:** Documents without `{%...%}` variables follow Architecture A exactly. Source detection happens at checkin (regex scan outside code blocks). No source file is created unless variables are found. This means Architecture C is a strict superset of Architecture A — it adds capability without changing existing behavior.

---

## The Metadata Layer (Shared Across All Architectures)

Every document, regardless of architecture, has two system-managed artifacts:

| Artifact | Location | Format | Role |
|----------|----------|--------|------|
| Metadata sidecar | `QMS/.meta/{TYPE}/{DOC_ID}.json` | JSON | Workflow state: version, status, responsible_user, checked_out, execution_phase, pending_assignees, review_outcomes |
| Audit trail | `QMS/.audit/{TYPE}/{DOC_ID}.jsonl` | JSONL (append-only) | Immutable event log: CREATE, CHECKOUT, CHECKIN, ROUTE, REVIEW, APPROVE, EFFECTIVE, etc. |

These are neither genotype nor phenotype — they are **infrastructure**. They track the document's lifecycle but are not part of the document's content. The metadata sidecar is the authoritative source for workflow state (not the frontmatter in the markdown file). The audit trail is the authoritative record of what happened.

CR-107 adds one new field to the metadata sidecar: `user_properties` (a dict written by `qms set`, read by the template variable resolver). This is the bridge between the metadata layer and Architecture C's genotype.

---

## The Template Layer

Templates serve fundamentally different roles in each architecture:

| Architecture | Template artifact | Role | Participates in... |
|-------------|-------------------|------|-------------------|
| A (Direct) | `TEMPLATE-{TYPE}.md` | One-time scaffolding mold | Document creation only |
| B (Interactive) | `TEMPLATE-VR.md` with `@prompt`/`@gate`/`@loop` annotations | Persistent compiler input + state machine definition | Every checkout, every read, every checkin, every interact |
| C (Template-variable) | *(none — variables are inline)* | N/A | N/A |

This is a key asymmetry: Architecture B's template is alive throughout the document's lifecycle. Architecture A's template is dead after creation. Architecture C has no template at all — the "template" concept is dissolved into the source document itself via inline variables.

---

## Cross-Cutting: The Frontmatter System

All documents (all architectures) use YAML frontmatter, but with a strict separation:

**Author-maintained fields** (survive `filter_author_frontmatter()`):
- `title`
- `revision_summary`

**System-managed fields** (stripped from workspace, restored at checkin):
- `version`, `status`, `responsible_user`, `created_date`, `checked_out_by`, `checked_out_date`, etc.

The `write_document_minimal()` function enforces this: when copying to workspace, only author fields are included. When copying back to QMS/ at checkin, the CLI re-injects system fields from the metadata sidecar.

CR-107 note: Template variables (`{%sys:version%}`, `{%user:qualified_commit%}`) can appear in frontmatter. Resolution processes the entire document (frontmatter + body), so a source frontmatter of `title: '{%sys:doc_id%}: Qualification Report'` would render to `title: 'SDLC-QMS-RTM: Qualification Report'`.

---

## Summary Matrix

|  | **Architecture A (Direct)** | **Architecture B (Interactive)** | **Architecture C (Template-Variable)** |
|--|---|---|---|
| **Document types** | CR, SOP, INV, VAR, ADD, RS, RTM, TP, ER | VR only | Any (opt-in via `{%...%}` in content) |
| **Status** | Current | Current | Proposed (CR-107) |
| **Genotype format** | Markdown | Structured JSON | Markdown with `{%...%}` variables |
| **Phenotype format** | Markdown (identical to genotype) | Compiled markdown | Markdown with concrete values |
| **Transformation** | None (copy) | Full compilation (structural) | String substitution (lightweight) |
| **Reversible?** | N/A (no transform) | No (compilation is lossy) | Yes (source preserved alongside) |
| **Template role** | One-time mold at creation | Persistent compiler input | None (variables are inline) |
| **Source storage** | N/A | `QMS/.meta/VR/*.source.json` (moving to `QMS/.source/`) | `QMS/.source/{TYPE}/{DOC_ID}/*-source.md` |
| **Author sets values via** | Direct editing | `qms interact --respond` | `qms set` (writes to `user_properties`) |
| **Who can preview?** | Anyone (`qms read`) | Anyone (`qms read` compiles from source) | Anyone (`qms read --preview` renders from source) |

---

## What CR-107 Unifies

CR-107's most significant architectural contribution is the `QMS/.source/` directory — a single location for all genotype artifacts:

```
QMS/.source/
  ├── RTM/
  │     └── SDLC-QMS-RTM/
  │           └── SDLC-QMS-RTM-source.md          # Architecture C genotype
  └── VR/
        └── CR-091-VR-001/
              └── CR-091-VR-001.source.json        # Architecture B genotype (relocated)
```

Before CR-107, Architecture B's genotype lives in `.meta/` alongside workflow metadata — mixing authoring data with workflow state. After CR-107, all source artifacts (regardless of architecture) live in `.source/`, and `.meta/` is purely workflow metadata + user properties.

This is a clean separation of concerns: `.meta/` = "how is this document progressing through its lifecycle?" `.source/` = "what did the author actually write?"
