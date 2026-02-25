# Document Type: SOP (Standard Operating Procedure)

## Overview

SOPs are **non-executable** documents. They define procedures but do not authorize implementation activities. SOPs become EFFECTIVE after approval and remain in force until superseded by a new revision or retired. See [Document Control](../02-Document-Control.md) for the document category definitions and [Workflows](../03-Workflows.md) for the non-executable lifecycle.

---

## Template Structure

Source: `QMS/TEMPLATE/TEMPLATE-SOP.md`

### Frontmatter

```yaml
---
title: '{{TITLE}}'
revision_summary: 'Initial creation'
---
```

| Field | Description | Managed By |
|-------|-------------|------------|
| `title` | Document title | Author (in frontmatter) |
| `revision_summary` | Description of changes in this revision | Author (in frontmatter) |

All other metadata (version, status, responsible_user, dates) lives in `.meta/SOP/{SOP-NNN}.json` sidecar files, managed exclusively by the CLI.

### Sections

| # | Heading | Content |
|---|---------|---------|
| 1 | **Purpose** | Why this procedure exists; what problem it solves |
| 2 | **Scope** | What it covers, who is governed. Includes bullet list and explicit **Out of Scope** sub-list |
| 3 | **Definitions** | Table: Term / Definition |
| 4+ | **(Content sections)** | The actual procedure. Section titles and count are author-defined. Numbered sequentially from 4 |
| N | **References** | Table: Document / Relationship. Last section, numbered to match |

### Placeholder Convention

SOPs use only one placeholder type:

| Syntax | Meaning | When to Replace |
|--------|---------|-----------------|
| `{{DOUBLE_CURLY}}` | Author-time placeholder | Before routing for review |

After drafting, no `{{...}}` placeholders should remain.

### Static vs Editable

SOPs are non-executable -- **all sections are static** once approved. There is no execution phase. To modify an effective SOP, check it out (creating a new draft revision) and go through the full review/approval cycle again.

---

## CLI Operations

For command syntax and detailed CLI behavior, see the [CLI Reference](../../qms-cli/docs/cli-reference.md).

**Key points:**
- SOPs are top-level documents (no `--parent` flag)
- Created in DRAFT status, automatically checked out to the creating user
- SOPs follow the non-executable workflow (no execution phase)

---

SOPs follow the standard non-executable document workflow. See [Workflows](../03-Workflows.md) for the full state machine and [CLI Reference](../../qms-cli/docs/cli-reference.md) for per-command enforcement details.

---

## Lifecycle

### Status Progression (Happy Path)

```
DRAFT -> IN_REVIEW -> REVIEWED -> IN_APPROVAL -> APPROVED -> EFFECTIVE
```

### Full State Diagram

```
                    +-----------+
                    |   DRAFT   |<-----------+
                    +-----------+            |
                         |                   |
                   route --review            | checkout (auto-withdraw)
                         |                   | checkin from REVIEWED
                         v                   |
                   +-----------+             |
                   | IN_REVIEW |-------------+
                   +-----------+        withdraw
                         |
                   review (all complete)
                         |
                         v
                   +-----------+
                   | REVIEWED  |<-------+
                   +-----------+        |
                         |              | reject
                   route --approval     |
                         |              |
                         v              |
                   +-------------+      |
                   | IN_APPROVAL |------+
                   +-------------+      |
                         |              | withdraw -> REVIEWED
                         |
                   approve (all complete)
                         |
                         v
                   +-----------+
                   |  APPROVED |
                   +-----------+
                         |
                   (automatic transition)
                         |
                         v
                   +-----------+
                   | EFFECTIVE |
                   +-----------+
                         |
                   checkout (creates {major}.1 draft)
                         |
                         v
                     DRAFT (new revision cycle)
```

### Terminal States

| State | How Reached | Recoverable? |
|-------|-------------|--------------|
| EFFECTIVE | Automatic after APPROVED | Yes -- checkout creates new revision |
| RETIRED | `--retire` flag on approval routing | No -- cannot be checked out |

### Withdraw Transitions

| From | To |
|------|----|
| IN_REVIEW | DRAFT |
| IN_APPROVAL | REVIEWED |

### Version Numbering

| Event | Version Change | Example |
|-------|---------------|---------|
| Create | `0.1` | Initial draft |
| Checkin (while DRAFT) | No change | Stays `0.1` |
| Checkout from EFFECTIVE | `{major}.1` | `1.0` -> `1.1` |
| Approval | `{major+1}.0` | `0.1` -> `1.0`, `1.1` -> `2.0` |

---

## Parent/Child Relationships

SOPs have **no parent/child relationships**. They are top-level standalone documents.

TEMPLATE documents can be parents of SOPs in a conceptual sense (SOPs are created from `TEMPLATE-SOP`), but there is no formal QMS linkage enforced by the CLI.

---

## Naming Convention

| Component | Format | Example |
|-----------|--------|---------|
| Prefix | `SOP` | -- |
| Number | 3-digit zero-padded | `001`, `006` |
| Full ID | `SOP-NNN` | `SOP-001`, `SOP-006` |
| Draft filename | `SOP-NNN-draft.md` | `SOP-001-draft.md` |
| Effective filename | `SOP-NNN.md` | `SOP-001.md` |
| Storage path | `QMS/SOP/` | Flat -- no folder-per-doc |
| Meta path | `QMS/.meta/SOP/SOP-NNN.json` | |
| Audit path | `QMS/.audit/SOP/SOP-NNN.jsonl` | |
| Archive path | `QMS/.archive/SOP/SOP-NNN-v{version}.md` | `QMS/.archive/SOP/SOP-001-v0.1.md` |

---

---

## See Also

- [Workflows](../03-Workflows.md) -- Non-executable document lifecycle state machine
- [Agent Orchestration](../11-Agent-Orchestration.md) -- Who can create and approve SOPs
- [CLI Reference](../../qms-cli/docs/cli-reference.md) -- Full command reference and permission matrix
- [TEMPLATE Reference](TEMPLATE.md) -- How SOP templates are governed
- [QMS Glossary](../QMS-Glossary.md) -- Term definitions
