# Document Type: TEMPLATE

## Overview

TEMPLATE documents are **non-executable, name-based** controlled documents that define the structure and guidance for other document types. They are themselves governed by document control -- a template is a QMS document that goes through the full [non-executable review/approval lifecycle](../03-Workflows.md). This means modifying a CR template requires a [Change Record](CR.md) that modifies the template.

Templates exist in **two locations** that must stay aligned:
- **`QMS/TEMPLATE/`** -- the active QMS instance copy (governed by document control)
- **`qms-cli/seed/templates/`** -- the seed copy (governed by SDLC, used when bootstrapping new QMS instances)

---

## Identity

| Property | Value |
|----------|-------|
| **Executable** | No |
| **Singleton** | No (but name-based, not numbered) |
| **Has Template** | N/A (templates are templates) |
| **Folder-per-doc** | No |
| **Parent Required** | No |
| **Requires `--name`** | Yes |

---

## Naming Convention

TEMPLATE documents use a name-based ID pattern rather than sequential numbering:

```
TEMPLATE-{NAME}
```

The NAME must be uppercase letters only. | Name | Document ID | Filesystem Path |
|------|-------------|-----------------|
| CR | `TEMPLATE-CR` | `QMS/TEMPLATE/TEMPLATE-CR.md` |
| SOP | `TEMPLATE-SOP` | `QMS/TEMPLATE/TEMPLATE-SOP.md` |
| VR | `TEMPLATE-VR` | `QMS/TEMPLATE/TEMPLATE-VR.md` |
| INV | `TEMPLATE-INV` | `QMS/TEMPLATE/TEMPLATE-INV.md` |

### Existing Templates

At the time of this writing, the following templates exist in both `QMS/TEMPLATE/` and `qms-cli/seed/templates/`:

| Template ID | Purpose |
|-------------|---------|
| `TEMPLATE-CR` | Change Record |
| `TEMPLATE-SOP` | Standard Operating Procedure |
| `TEMPLATE-TP` | Test Protocol |
| `TEMPLATE-ER` | Execution Record |
| `TEMPLATE-INV` | Investigation |
| `TEMPLATE-VAR` | Variance |
| `TEMPLATE-ADD` | Addendum |
| `TEMPLATE-VR` | Verification Record |
| `TEMPLATE-TC` | Test Case |

---

## CLI Operations

For command syntax and detailed CLI behavior, see the [CLI Reference](../../qms-cli/docs/cli-reference.md).

**Key points:**
- TEMPLATE documents require the `--name` flag (e.g., `--name CR` produces `TEMPLATE-CR`)
- The name must be uppercase letters only
- Duplicate names are rejected (both effective and draft paths are checked)
- There is no `TEMPLATE-TEMPLATE` -- new templates fall back to minimal scaffolding

---

## The Dual-Copy System

### QMS Copy (`QMS/TEMPLATE/`)

This is the **active instance copy**. It is a controlled document governed by standard document control:

- Checked out / checked in via the QMS CLI
- Goes through review/approval lifecycle
- Has version history, audit trail, metadata sidecar
- Used by the CLI at runtime when creating new documents of the corresponding type

When a new document is created, the CLI reads from `QMS/TEMPLATE/TEMPLATE-{TYPE}.md` and parses the template content. If no template exists for the type, it falls back to minimal scaffolding.

### Seed Copy (`qms-cli/seed/templates/`)

This is the **bootstrapping copy**. It lives inside the `qms-cli` submodule and is used:

1. When initializing a new QMS instance (the seed templates populate `QMS/TEMPLATE/`)
2. By the interactive authoring engine (`qms interact`) for VR documents
3. By the interactive checkin/checkout system for documents with `.interact` sessions
4. By the `close` command for VR auto-close compilation

The seed copy is governed by SDLC (the `qms-cli` submodule has its own CI and PR workflow), not directly by QMS document control.

### Alignment Requirement

When a CR modifies a template, **both copies must be updated**:

1. **QMS copy**: Checkout via CLI, edit, checkin (standard document control)
2. **Seed copy**: Follow the [code governance workflow](../09-Code-Governance.md) -- develop in `.test-env/`, create execution branch, run CI, merge via PR, then update submodule pointer

CRs that modify templates should include an alignment verification EI to confirm both copies match after changes are applied.

---

## Template Document Structure

Every controlled template in `QMS/TEMPLATE/` has a specific internal structure:

### Structure Overview

```
---                                    # Template's own frontmatter (controlled)
title: Change Record Template
revision_summary: 'CR-100: description'
---

<!-- TEMPLATE DOCUMENT NOTICE -->      # Metadata comment (stripped by CLI)

---                                    # Example frontmatter (copied to new docs)
title: '{{TITLE}}'
revision_summary: 'Initial draft'
---

<!-- TEMPLATE USAGE GUIDE -->          # Author guidance (preserved in new docs)

# CR-XXX: {{TITLE}}                   # Document body with placeholders
...
```

### Two Frontmatter Blocks

Templates have **two** YAML frontmatter blocks separated by `---`:

1. **Template frontmatter** (lines 1-4): The template document's own metadata (`title`, `revision_summary`). This is what the QMS tracks as the template's controlled content.

2. **Example frontmatter** (after the TEMPLATE DOCUMENT NOTICE): The frontmatter that will be copied into new documents created from this template. Contains `{{TITLE}}` placeholder.

### Comment Blocks

**TEMPLATE DOCUMENT NOTICE**: A comment block that explains the template is a controlled document. This block is **stripped** by the CLI when creating a new document from the template.

**TEMPLATE USAGE GUIDE**: A comment block providing authoring guidance for the document type. This block is **intentionally preserved** in new documents so the author can read it and then delete it manually.

### Template Parsing Logic

The CLI splits the template content on `---` delimiters to separate the template's own frontmatter, the TEMPLATE DOCUMENT NOTICE, the example frontmatter, and the document body. After parsing:
- The example frontmatter is extracted as YAML
- The TEMPLATE DOCUMENT NOTICE is stripped
- `{{TITLE}}` is replaced with the actual title
- `{TYPE}-XXX` is replaced with the actual doc_id

---

## Interactive Templates (Tag System)

Some templates (currently only `TEMPLATE-VR`) use the **interactive template tag system** for guided authoring via `qms interact`. See [Interactive Authoring](../08-Interactive-Authoring.md) for the full system documentation. These templates embed HTML comment tags that define a state machine graph.

### Tag Vocabulary

Defined in `interact_parser.py` (REQ-INT-001):

| Tag | Syntax | Purpose |
|-----|--------|---------|
| `@template` | `@template: NAME \| version: N \| start: id` | Template header with metadata |
| `@prompt` | `@prompt: id \| next: id [\| commit: true] [\| default: value]` | Content prompt node |
| `@gate` | `@gate: id \| type: yesno \| yes: id \| no: id` | Flow-control decision node |
| `@loop` | `@loop: name` | Repeating block start |
| `@end-loop` | `@end-loop: name` | Repeating block end |
| `@end-prompt` | `@end-prompt` | Guidance boundary marker |
| `@end` | `@end` | Terminal state |

### Tag Attributes

| Attribute | Used In | Description |
|-----------|---------|-------------|
| `id` | prompt, gate | Node identifier (bare value or explicit) |
| `next` | prompt | Unconditional transition target |
| `type` | gate | Gate type (`yesno`) |
| `yes` / `no` | gate | Conditional transition targets |
| `commit` | prompt | When `true`, engine commits project state on response |
| `default` | prompt | Auto-fill value (author can override) |

### Parsed Structure

Tags are parsed into a graph structure containing:
- A **header** with name, version, and start prompt
- **Prompt nodes** with ID, next target, optional commit flag, default value, guidance text, and loop membership
- **Gate nodes** with ID, gate type, yes/no targets, guidance, and loop membership
- **Loop definitions** tracking iteration state

### Example: VR Template Tags

From `TEMPLATE-VR` (seed copy):

```markdown
<!-- @template: VR | version: 5 | start: related_eis -->

<!-- @prompt: related_eis | next: objective -->
Which execution item(s)...
<!-- @end-prompt -->

<!-- @loop: steps -->
<!-- @prompt: step_instructions | next: step_expected -->
What are you about to do?...
<!-- @prompt: step_actual | next: step_outcome | commit: true -->
What did you observe?...
<!-- @gate: more_steps | type: yesno | yes: step_instructions | no: summary_outcome -->
<!-- @end-loop: steps -->

<!-- @prompt: summary_outcome | next: summary_narrative -->
<!-- @prompt: summary_narrative | next: end -->
<!-- @end -->
```

### Placeholder Substitution

In the compiled output, `{{prompt_id}}` is replaced with the active response value. For loop-iterated prompts, `{{_n}}` is replaced with the iteration counter.

---

## Interactive Session Lifecycle

### VR Creation

When a VR document is created, the CLI initializes an interactive session:

1. Reads the **seed** template (`qms-cli/seed/templates/TEMPLATE-VR.md`)
2. Parses it into a template graph
3. Creates a source data structure (`.interact` session file)
4. Saves the session to the workspace

### Interactive Checkin

When an interactive document is checked in:

1. The `.interact` session is loaded
2. The **seed** template is loaded (not the QMS copy)
3. The session is compiled to markdown via `compile_document(source, template_text)`
4. The compiled markdown is written to the QMS draft path
5. The source data is saved to `.meta/` as `{doc_id}.source.json` (permanent record)
6. The `.interact` file and workspace placeholder are cleaned up

### Interactive Checkout

When an interactive document is checked out:

1. The **seed** template is loaded
2. If `.source.json` exists in `.meta/`, it is loaded to resume the session
3. Otherwise, a new source is created
4. A new `.interact` session file is saved to workspace

---

## Lifecycle (Non-Executable Workflow)

```
DRAFT --> IN_REVIEW --> REVIEWED --> IN_APPROVAL --> APPROVED --> EFFECTIVE
```

Same as all non-executable documents. On approval:
1. Draft archived
2. Draft promoted to effective copy in `QMS/TEMPLATE/`
3. Previous effective version archived
4. Version bumped to major, owner cleared

---

TEMPLATE documents follow the standard non-executable workflow (create, checkout, checkin, route, review, approve). See the [CLI Reference](../../qms-cli/docs/cli-reference.md) for command syntax.

---

## Filesystem Layout

```
QMS/
  TEMPLATE/
    TEMPLATE-CR.md                # Effective (controlled) template
    TEMPLATE-CR-draft.md          # Draft (when checked out for revision)
    TEMPLATE-SOP.md
    TEMPLATE-VR.md
    ...
  .meta/
    TEMPLATE/
      TEMPLATE-CR.json            # Metadata sidecar
      TEMPLATE-SOP.json
      ...
  .audit/
    TEMPLATE/
      TEMPLATE-CR.audit.json      # Audit trail
  .archive/
    TEMPLATE/
      TEMPLATE-CR-v1.0.md         # Archived versions

qms-cli/
  seed/
    templates/
      TEMPLATE-CR.md              # Seed copy (for bootstrapping + interactive)
      TEMPLATE-SOP.md
      TEMPLATE-VR.md              # Interactive template (has @tags)
      ...
```

---

## Key Distinctions: QMS Copy vs Seed Copy

| Aspect | QMS Copy (`QMS/TEMPLATE/`) | Seed Copy (`qms-cli/seed/templates/`) |
|--------|---------------------------|---------------------------------------|
| **Governance** | QMS document control (checkout/checkin) | SDLC (CI, PR, submodule update) |
| **Used for** | Creating new documents at runtime | Bootstrapping new QMS instances; interactive engine compilation |
| **Has metadata sidecar** | Yes (`.meta/TEMPLATE/`) | No |
| **Has audit trail** | Yes (`.audit/TEMPLATE/`) | No (tracked by git) |
| **Versioned by** | QMS version (0.1, 1.0, 2.0) | Git commit history |
| **Modifiable by** | QMS CLI (checkout/edit/checkin) | Direct file edit + PR merge |
| **Template notice stripped** | Yes (on `load_template_for_type`) | No (read raw by interact engine) |

---

## See Also

- [Interactive Authoring](../08-Interactive-Authoring.md) -- Template tags, VR authoring, source data model
- [Document Control](../02-Document-Control.md) -- Document types, naming, and metadata architecture
- [VR Reference](VR.md) -- The primary interactive template consumer
- [Code Governance](../09-Code-Governance.md) -- Seed copy governance via SDLC
- [QMS Glossary](../QMS-Glossary.md) -- Term definitions
