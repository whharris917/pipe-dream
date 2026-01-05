# Document Rendering Concepts

**Date:** 2026-01-04
**Session:** 009
**Status:** Discussion notes (not implemented)

---

## Overview

QMS documents should have automatically injected metadata headers and revision history footers. The document in the QMS is a polished *rendition*, while the checkout version is the clean *source*.

---

## Source vs. Rendition Model

### Source Document (Workspace)

What the author sees during checkout — clean, focused on content:

```markdown
---
title: Deviation Management
revision_summary: "CR-009: Initial release"
parent_cr: CR-009
---

## 1. Purpose

This Standard Operating Procedure establishes procedures for...

---

## 2. Scope

...

---

**END OF DOCUMENT**
```

The author never maintains metadata headers or revision history manually.

### Rendered Document (QMS)

What appears in the QMS after checkin — polished with injected metadata:

```markdown
---
title: Deviation Management
revision_summary: "CR-009: Initial release"
parent_cr: CR-009
---

# SOP-003: Deviation Management

| Document ID | SOP-003 |
|-------------|---------|
| Version | 1.0 |
| Status | EFFECTIVE |
| Effective Date | 2026-01-04 |

---

## 1. Purpose

This Standard Operating Procedure establishes procedures for...

---

## 2. Scope

...

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-04 | claude | CR-009: Initial release |
| 0.1 | 2026-01-04 | claude | Draft |

---

**END OF DOCUMENT**
```

---

## Three-Layer Structure

### Layer 1: YAML Frontmatter

- Machine-readable metadata
- Authoritative source for machine parsing
- May contain fields not shown in visible header
- Preserved in both source and rendered versions

### Layer 2: Visible Header (Injected)

Human-readable summary of key metadata:

| Field | Source |
|-------|--------|
| Document ID | Derived from filename/path |
| Version | `.meta/{doc_id}.json` |
| Status | `.meta/{doc_id}.json` |
| Effective Date | `.meta/{doc_id}.json` |

Injected immediately after frontmatter, before first content section.

### Layer 3: Visible Footer (Injected)

Revision history table built from audit trail:

| Column | Source |
|--------|--------|
| Version | `.audit/{doc_id}.jsonl` events |
| Date | Event timestamp |
| Author | Event user |
| Changes | `revision_summary` from frontmatter at that version |

Injected before `**END OF DOCUMENT**` marker.

---

## Workflow Integration

### Checkin Process

1. Read source document from workspace
2. Read metadata from `.meta/{doc_id}.json`
3. Build revision history from `.audit/{doc_id}.jsonl`
4. Inject visible header after frontmatter
5. Inject revision history footer before END OF DOCUMENT
6. Write rendered version to QMS location
7. Archive rendered version to `.archive/`

### Checkout Process

1. Read rendered version from QMS
2. Strip injected header (between frontmatter and first `## ` section)
3. Strip injected footer (Revision History section)
4. Write clean source to workspace

---

## Benefits

| Benefit | Description |
|---------|-------------|
| **Accuracy** | Metadata always current — pulled from system of record |
| **Simplicity** | Authors focus on content, not bookkeeping |
| **Consistency** | All documents have uniform header/footer format |
| **Auditability** | Revision history automatically built from audit trail |
| **Clean diffs** | Source documents don't have noisy metadata changes |

---

## Implementation Notes

### Header Detection

The injected header can be identified by:
- Appears immediately after frontmatter (`---`)
- Starts with `# {DOC_ID}: {Title}`
- Contains metadata table
- Ends with `---` before first content section

### Footer Detection

The injected footer can be identified by:
- Section header `## Revision History`
- Immediately followed by version/date/author/changes table
- Appears just before `**END OF DOCUMENT**`

### Edge Cases

- Documents without `**END OF DOCUMENT**` marker: Add one during checkin
- Documents with manual revision history: Replace with generated version
- First version (no audit history): Single row with current version

---

## Open Items

- Exact header format (which metadata fields to show)
- Date format in revision history
- Handling of very long revision histories (truncate? collapse?)
- Whether to show draft versions in revision history or only released versions

---

**End of Notes**
