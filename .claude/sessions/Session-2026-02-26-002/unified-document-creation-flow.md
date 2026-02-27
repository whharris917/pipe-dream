# Unified Document Lifecycle

## Context

This document traces the complete artifact state across the unified source system (CR-107 redesign). It covers two scenarios: creating a new document from a template, and checking out a pre-existing document under the unified system. Both scenarios follow the same principles — the unified model has no special cases.

---

## The Template as Living Schema Authority

The `TEMPLATE-{TYPE}.md` file in `QMS/TEMPLATE/` is the single source of truth for a document type's user property schema. The template's frontmatter declares which user properties exist for that type.

**Schema is applied at every checkout**, not just at creation. This means:

- When a template evolves (fields added or removed), every document of that type picks up the new schema the next time it is checked out.
- All documents of a given type always have the same active schema, matching the current template.
- There is no schema drift between old and new documents of the same type.

**When the template adds a field:** The new key appears in the document's `user_properties` with a null value. The source file's frontmatter gains the new field (null/empty). Checkin is blocked until the author provides a concrete value — this is the nature of keeping up with the times. The template evolution forces schema compliance.

**When the template removes a field:** The value is not discarded. It moves from `user_properties` to `archived_properties` in metadata, with provenance:

```json
{
  "user_properties": {
    "title": "...",
    "revision_summary": "...",
    "security_impact": null
  },
  "archived_properties": {
    "old_field_name": {
      "value": "the original value",
      "archived_at": "2026-02-26",
      "template_version": "10.0"
    }
  }
}
```

The archived value is still in the metadata, still auditable, but not part of the active schema. Never silently discarded.

**The checkout schema sync flow:**

1. Read current `QMS/TEMPLATE/TEMPLATE-{TYPE}.md`, parse frontmatter for property keys
2. Compare template schema against document's current `user_properties`
3. New keys in template: add to `user_properties` with null values
4. Keys removed from template: move to `archived_properties` with provenance
5. Existing keys: values preserved as-is
6. Copy source to workspace (source frontmatter now reflects updated schema)

---

## Scenario 1: New Document from Template

### At Creation

`qms create RTM --title "..." --namespace SDLC-SYS`

| Artifact | Location | Content |
|----------|----------|---------|
| **Source** | `QMS/.source/SDLC-SYS/SDLC-SYS-RTM/SDLC-SYS-RTM-source.md` | Template content with `{%user:...%}` variables intact, `{{...}}` placeholders intact, frontmatter has property declarations from template |
| **Workspace** | `.claude/users/{user}/workspace/SDLC-SYS-RTM.md` | Copy of source (author edits here) |
| **Draft** | `QMS/SDLC-SYS/SDLC-SYS-RTM/SDLC-SYS-RTM-draft.md` | Stub: "This document has not been checked in since creation. No rendition is available." |
| **Metadata** | `QMS/.meta/.../SDLC-SYS-RTM.json` | Workflow state + `user_properties` with keys from template, null values |
| **Audit** | `QMS/.audit/.../SDLC-SYS-RTM.jsonl` | CREATE event |

The source is the primary artifact from birth. The draft is always derived — and since there's nothing to derive from yet (no values set, body still has `{{...}}` scaffolding), the draft is a stub. This makes the draft's secondary nature explicit from the very first moment the document exists.

**Auto-checkout:** The current system already auto-checks out upon creation, so the author can start editing the workspace copy immediately. The creation flow is: create → edit workspace → checkin.

**Initial schema:** At creation, the template's frontmatter keys become the document's initial `user_properties` schema. This is the same schema sync that happens at every checkout — creation is just the first checkout.

### At First Checkin

1. Parse workspace frontmatter — validate all `{{...}}` replaced with concrete values, all user property keys present with non-null values
2. Write workspace content back to `.source/` (preserving `{%user:...%}` variables in body)
3. Populate `user_properties` from frontmatter values
4. Resolve all `{%user:...%}` and `{%sys:...%}` references → render to draft
5. Draft now has real content for the first time

**After first checkin:**

| Artifact | Content |
|----------|---------|
| **Source** | Markdown with concrete frontmatter values + `{%user:...%}` variables in body |
| **Draft** | Fully rendered markdown — concrete values everywhere |
| **Metadata** | `user_properties` populated from frontmatter |

### Subsequent Checkout/Checkin Cycles

On subsequent checkouts, the system performs the template schema sync (see above), then copies from `.source/` to workspace. The author sees the source with `{%user:...%}` variables visible in the body and concrete values in the frontmatter. If the template has evolved since the last checkout, new fields appear in the frontmatter (with null values that must be filled before checkin). They can update frontmatter values (e.g., change `qualified_commit`), edit body content, and checkin triggers resolution again.

**The source is always the checkout source; the draft is never the checkout source.**

---

## Scenario 2: Pre-Existing Document (Migration)

This traces the lifecycle of SOP-005 v2.0 — a document created before the unified source system, with no source file and no `user_properties` in metadata.

### Starting State

| Artifact | Location | Content |
|----------|----------|---------|
| **Effective** | `QMS/SOP/SOP-005/SOP-005.md` | Effective v2.0 with full frontmatter (author + system fields) |
| **Metadata** | `QMS/.meta/SOP/SOP-005.json` | status: EFFECTIVE, version: 2.0, no `user_properties` |
| **Source** | — | Does not exist |

### Checkout #1 (Migration Trigger)

1. Archive effective: `SOP-005-v2.0.md` → `.archive/`
2. Version bump to 2.1, status to DRAFT in metadata
3. **Migration moment:** System checks `.source/SOP/SOP-005/SOP-005-source.md` — not found
4. Reads effective content. Strips system frontmatter.
5. **Template schema sync:** Reads current `QMS/TEMPLATE/TEMPLATE-SOP.md`, parses frontmatter for property keys. The template defines the schema — not the document's existing frontmatter. If TEMPLATE-SOP currently declares `title` and `revision_summary`, those become the user properties. If the template has evolved to include additional fields, those appear too (with null values).
6. Stamps `user_properties` into metadata from template schema. Values for keys that existed in the effective document's frontmatter (e.g., `title`, `revision_summary`) are populated from those values. New keys from template evolution get null values.
7. Creates `QMS/.source/SOP/SOP-005/SOP-005-source.md` from effective body + user-property-only frontmatter (reflecting the synced schema).
8. Copies source to workspace: `.claude/users/{user}/workspace/SOP-005.md`
9. Renders draft: source body + system frontmatter injected from metadata. Since no `{%...%}` variables exist in the body, the render is an identity transform for the body.

**After checkout #1:**

| Artifact | Content |
|----------|---------|
| **Source** | SOP-005 body with user-property frontmatter (from template schema) |
| **Workspace** | Copy of source |
| **Draft** | Same body + full frontmatter (user properties + system properties) |
| **Metadata** | `user_properties` populated from template schema + existing values |

The author edits the workspace copy — changes prose, updates `revision_summary` in frontmatter. If the template introduced new fields, the author must fill those in before checkin.

### Checkin #1

1. Read workspace content
2. Validate: all user property keys present with concrete values (no nulls, no `{{...}}`) — **checkin blocked if any template-required fields are unfilled**
3. Save workspace content to `.source/` (source updated with edits)
4. Populate `user_properties` from frontmatter values
5. Resolve `{%...%}` in body → none found → identity transform
6. Render to draft: source body + system frontmatter injection

Source and draft body are identical. The only difference between the two files is that the draft has system frontmatter fields (`version`, `status`, `responsible_user`, etc.) and the source has only user property frontmatter fields.

Route for review. Reviewer reads the draft (rendered). Requests edits.

### Checkout #2 (After Review with Edits Requested)

1. Status reverts to DRAFT
2. System checks `.source/` — **source file exists** (created during checkout #1)
3. **Template schema sync:** Reads current TEMPLATE-SOP. Compares against `user_properties`. If template hasn't changed, no schema update. If it has, new fields added (null), removed fields archived.
4. Copies source to workspace (frontmatter reflects current schema).
5. Draft unchanged (still shows last rendered version from checkin #1)
6. Metadata: `checked_out: true`

### Checkin #2

1. Read workspace content
2. Validate: all user property keys present with concrete values
3. Save to `.source/`
4. Populate `user_properties` from frontmatter
5. Resolve → identity transform
6. Render to draft

Route for approval.

### Approval

1. Draft (rendered) → copy to effective: `SOP-005.md`
2. Version bump: 2.1 → 3.0
3. Status: EFFECTIVE
4. Source file remains in `.source/` — canonical representation of the current effective content

Standard approval flow. The source persists as the primary artifact.

---

## Key Architectural Properties

- **The draft is always derived, never primary.** From the stub at creation to the rendered content after checkin, the draft is always a product of resolution — never an input to any operation.
- **The source is primary from birth.** For new documents, the source is created from the template at creation. For pre-existing documents, the source is created from the effective/draft content at first checkout (migration).
- **Frontmatter is the only input channel for user properties.** There is no `qms set` command. Authors set metadata by editing frontmatter values in the source file. Checkin reads frontmatter and populates `user_properties` in metadata.
- **All frontmatter fields in the source are user properties.** There is no distinction between "author-maintained" and "system-managed" frontmatter. The source file's frontmatter contains user properties; the rendered draft's frontmatter contains user properties + system properties. `filter_author_frontmatter()` and the stripping/restoring dance in `write_document_minimal()` are eliminated.
- **The template is the living schema authority.** `TEMPLATE-{TYPE}.md` defines the user property schema for all documents of that type. The schema is applied at every checkout — not frozen at creation. Template evolution propagates to all documents of that type. All documents of a type always share the same active schema.
- **Schema evolution is non-destructive.** New template fields appear as null-valued properties that must be filled before checkin. Removed template fields are archived with provenance — values are never silently discarded.
- **Checkin enforces schema compliance.** All user property keys must have concrete values at checkin. Null values, `{{...}}` placeholders, and missing keys all produce validation errors. This is the enforcement mechanism for template evolution — checking out an old document under a new template forces the author to provide the now-required fields.
- **Validation at checkin catches incomplete metadata.** Any `{{...}}` placeholders remaining in frontmatter — fields the author never filled in — produce a validation error. Any declared property missing entirely from frontmatter (author deleted the line) produces a validation error with specific guidance on what to restore.
- **Checkout is the migration trigger.** Pre-existing documents acquire source files and user property schemas the first time they are checked out under the unified system. Documents that are never checked out again simply never migrate — and that's fine.
- **This flow is universal.** Documents with zero `{%...%}` variables follow the same path — the resolution step is an identity transform for the body. There is no opt-in, no detection, no special cases.
