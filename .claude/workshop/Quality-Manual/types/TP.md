# TP -- Test Protocol

## Document Type Summary

| Property | Value |
|----------|-------|
| **Type code** | `TP` |
| **Executable** | Yes |
| **Parent required** | Yes -- must be a [`CR`](CR.md) |
| **Children** | [`TC`](TC.md) (fragment, embedded), [`ER`](ER.md) (standalone executable) |
| **Folder-per-doc** | No -- lives inside parent CR folder |
| **Template** | `QMS/TEMPLATE/TEMPLATE-TP.md` |

---

## 1. Naming Convention

| Pattern | Example |
|---------|---------|
| `{CR_ID}-TP-{NNN}` | `CR-001-TP-001` |

The sequential number `NNN` is zero-padded to 3 digits. Numbering is scoped to the parent CR: the CLI scans the parent CR folder for existing `{parent_id}-TP-NNN` files and increments from the highest found.

**File paths:**

| Variant | Path |
|---------|------|
| Draft | `QMS/CR/{CR_ID}/{CR_ID}-TP-{NNN}-draft.md` |
| Effective | `QMS/CR/{CR_ID}/{CR_ID}-TP-{NNN}.md` |
| Archive | `QMS/.archive/CR/{CR_ID}/{CR_ID}-TP-{NNN}-v{version}.md` |

---

## 2. Template Structure

### Frontmatter

```yaml
---
title: '{{TITLE}}'
revision_summary: 'Initial draft'
---
```

Only two author-maintained fields. All other metadata (version, status, responsible_user, dates) is managed in sidecar `.meta/TP/{doc_id}.json` files by the CLI.

### Sections

| # | Heading | Content | Static/Editable |
|---|---------|---------|-----------------|
| 1 | **Purpose** | What the test protocol verifies; the system/feature under test. | **Locked** after pre-approval |
| 2 | **Scope** | Table: System, Version, Commit hash identifying the build under test. | **Locked** after pre-approval |
| 3 | **Test Cases** | Container for TC subsections (TC-001, TC-002, ...). Each TC follows `TEMPLATE-TC` structure. | **Editable** during execution |
| 4 | **Protocol Summary** | 4.1 Overall Result (Pass/Fail/Pass with Exceptions) and 4.2 Execution Summary (narrative). | **Editable** during execution |
| 5 | **References** | Links to TC-TEMPLATE and additional references. | Locked after pre-approval |

### Placeholder Convention

| Syntax | Phase | Meaning |
|--------|-------|---------|
| `{{DOUBLE_CURLY}}` | Authoring (design time) | Replace before routing for review. None should remain after authoring. |
| `[SQUARE_BRACKETS]` | Execution (run time) | Replace during protocol execution. All should remain until execution begins. |

### ID Hierarchy (within a TP)

```
TP-NNN                              # Protocol
  TC-NNN                            # Test Case (embedded fragment)
    TC-NNN-NNN                      # Step within TC
    TC-NNN-ER-NNN                   # Exception Report for TC
      TC-NNN-ER-NNN-ER-NNN          # Nested ER
```

Full qualified IDs prefix with the TP ID:

```
CR-001-TP-001
  CR-001-TP-001-TC-001
    CR-001-TP-001-TC-001-001        # Step
    CR-001-TP-001-TC-001-ER-001     # Exception Report
```

---

## 3. Scope Table (Section 2)

The Scope section pins the test to a specific software version:

```markdown
| System | Version | Commit |
|--------|---------|--------|
| My App | 1.0.0 | a1b2c3d |
```

This is filled during authoring and locked after pre-approval. It establishes the qualified baseline for the test.

---

## 4. CLI Operations

For command syntax and detailed CLI behavior, see the [CLI Reference](../../qms-cli/docs/cli-reference.md).

**Key points:**
- TPs require a `--parent` flag pointing to a CR document
- Parent type must be CR (enforced at creation)
- No restriction on the parent CR's status at creation time
- Created in DRAFT status, automatically checked out to the creating user

---

---

## 6. Lifecycle

TP follows the full **executable document workflow** with pre-approval (design) and post-approval (execution) phases.

```
DRAFT
  |-- route --review --> IN_PRE_REVIEW
                           |-- review --> PRE_REVIEWED
                                           |-- route --approval --> IN_PRE_APPROVAL
                                                                      |-- approve --> PRE_APPROVED
                                                                      |-- reject --> PRE_REVIEWED
                                           |-- checkout --> DRAFT (revision)
                           |-- withdraw --> DRAFT

PRE_APPROVED
  |-- release --> IN_EXECUTION
  |-- checkout --> DRAFT (scope revision, clears workflow)

IN_EXECUTION
  |-- checkout (minor version bump) --> IN_EXECUTION
  |-- route --review --> IN_POST_REVIEW
                           |-- review --> POST_REVIEWED
                                           |-- route --approval --> IN_POST_APPROVAL
                                                                      |-- approve --> POST_APPROVED
                                                                      |-- reject --> POST_REVIEWED
                                           |-- checkout --> IN_EXECUTION
                                           |-- revert --> IN_EXECUTION (deprecated)
                           |-- withdraw --> IN_EXECUTION

POST_APPROVED
  |-- close --> CLOSED (terminal)
```

### Status Reference

| Status | Phase | Description |
|--------|-------|-------------|
| DRAFT | Pre-release | Being authored or revised |
| IN_PRE_REVIEW | Pre-release | Design review in progress |
| PRE_REVIEWED | Pre-release | Review complete, awaiting approval routing |
| IN_PRE_APPROVAL | Pre-release | Approval decision pending |
| PRE_APPROVED | Pre-release | Approved; ready for release to execution |
| IN_EXECUTION | Post-release | Test protocol is being executed |
| IN_POST_REVIEW | Post-release | Execution results under review |
| POST_REVIEWED | Post-release | Post-review complete, awaiting approval routing |
| IN_POST_APPROVAL | Post-release | Final approval decision pending |
| POST_APPROVED | Post-release | Approved; ready for closure |
| CLOSED | Terminal | Permanently closed |

---

## 7. Parent/Child Relationships

| Relationship | Details |
|-------------|---------|
| **Parent** | [CR](CR.md) (required). TP cannot exist without a parent CR. |
| **Children** | [ER](ER.md) -- Exception Reports are created with `--parent {TP_ID}`. ERs must have a TP parent. |
| **Embedded fragments** | [TC](TC.md) (Test Cases) are not standalone QMS documents. They are sections within the TP body following `TEMPLATE-TC` structure. |

### Filesystem hierarchy example

```
QMS/CR/CR-001/
  CR-001-draft.md                    # Parent CR
  CR-001-TP-001-draft.md             # Test Protocol
  CR-001-TP-001-ER-001-draft.md      # Exception Report (child of TP)
```

---

---

## See Also

- [Change Control](../04-Change-Control.md) -- Test Protocols as CR children
- [Child Documents](../07-Child-Documents.md) -- Decision guide for ER vs VAR vs ADD
- [Execution](../06-Execution.md) -- Executable block structure and evidence requirements
- [ER Reference](ER.md) -- Exception Reports for test failures
- [TC Reference](TC.md) -- Test Case fragment structure
