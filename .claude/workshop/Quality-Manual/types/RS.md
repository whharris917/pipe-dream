# Document Type: RS (Requirements Specification)

## Overview

RS documents are **non-executable, singleton** SDLC documents that define requirements for a controlled system. They are namespaced under an SDLC namespace (e.g., `FLOW`, `QMS`) and follow the [non-executable document workflow](../03-Workflows.md). See [SDLC](../10-SDLC.md) for the requirements framework and qualification process.

There is no RS template in `QMS/TEMPLATE/` or `qms-cli/seed/templates/`. RS documents are created with a minimal fallback template.

---

## Identity

| Property | Value |
|----------|-------|
| **Executable** | No |
| **Singleton** | Yes (one per namespace) |
| **Has Template** | No (`TEMPLATE-RS` does not exist; uses minimal fallback) |
| **Folder-per-doc** | No |
| **Parent Required** | No |

---

## Naming Convention

RS documents use the SDLC namespace naming pattern:

```
SDLC-{NAMESPACE}-RS
```

| Namespace | Document ID | Filesystem Path |
|-----------|-------------|-----------------|
| FLOW | `SDLC-FLOW-RS` | `QMS/SDLC-FLOW/SDLC-FLOW-RS.md` |
| QMS | `SDLC-QMS-RS` | `QMS/SDLC-QMS/SDLC-QMS-RS.md` |

---

## CLI Operations

For command syntax and detailed CLI behavior, see the [CLI Reference](../../qms-cli/docs/cli-reference.md).

**Key points:**
- RS types are dynamically generated per SDLC namespace (e.g., `FLOW-RS`, `QMS-RS`)
- RS is a **singleton** type -- exactly one per namespace, no sequential numbering
- No RS template exists; the CLI uses minimal fallback scaffolding
- Created in DRAFT status, automatically checked out to the creating user

---

## SDLC Namespace System

### Built-in Namespaces

| Namespace | Path | Document Types |
|-----------|------|----------------|
| FLOW | `SDLC-FLOW` | `FLOW-RS`, `FLOW-RTM` |
| QMS | `SDLC-QMS` | `QMS-RS`, `QMS-RTM` |

### Custom Namespaces

Additional namespaces can be registered by administrators via the `namespace add` command. This creates the directory structure and makes `{NS}-RS` and `{NS}-RTM` available as document types. Custom namespaces are persisted in `QMS/.meta/sdlc_namespaces.json`.

Only users in the `administrator` group can add namespaces. All users can list namespaces.

For namespace command syntax, see the [CLI Reference](../../qms-cli/docs/cli-reference.md).

---

## Lifecycle (Non-Executable Workflow)

```
DRAFT --> IN_REVIEW --> REVIEWED --> IN_APPROVAL --> APPROVED --> EFFECTIVE
                                                                    |
                                                                    v
                                                                 RETIRED
```

### Key Transitions

| From | Action | To |
|------|--------|-----|
| DRAFT | Route for review | IN_REVIEW |
| IN_REVIEW | All reviewers recommend | REVIEWED |
| REVIEWED | Route for approval | IN_APPROVAL |
| IN_APPROVAL | All approvers approve | APPROVED -> EFFECTIVE |
| EFFECTIVE | Checkout (new revision) | DRAFT (new minor version) |
| EFFECTIVE | Route for retirement | IN_APPROVAL (with retiring flag) |

### Approval Behavior for Non-Executable Documents

When approved, non-executable documents immediately transition through APPROVED to EFFECTIVE:

1. Draft is archived as the pre-approval version
2. Draft is promoted to effective copy (draft file renamed, `-draft` suffix removed)
3. Previous effective version (if any) is archived
4. Meta is updated: status=EFFECTIVE, version bumped to major (N+1.0), owner cleared

### Revision Cycle

When an EFFECTIVE RS is checked out for revision:
1. A new draft is created from the effective copy
2. Version incremented to `N.1` (minor from current major)
3. Effective copy remains in place (preserved per REQ-WF-020)
4. Standard review/approval cycle follows
5. On approval, new version supersedes old effective

---

RS documents follow the standard non-executable workflow (create, checkout, checkin, route, review, approve). See the [CLI Reference](../../qms-cli/docs/cli-reference.md) for command syntax.

---

## Filesystem Layout

```
QMS/
  SDLC-FLOW/
    SDLC-FLOW-RS.md              # Effective version
    SDLC-FLOW-RS-draft.md        # Draft version (when checked out)
  .meta/
    FLOW-RS/
      SDLC-FLOW-RS.json          # Metadata sidecar
  .audit/
    FLOW-RS/
      SDLC-FLOW-RS.audit.json    # Audit trail
  .archive/
    SDLC-FLOW/
      SDLC-FLOW-RS-v1.0.md       # Archived versions
```

---

## See Also

- [SDLC](../10-SDLC.md) -- Requirements framework, verification types, qualification
- [RTM Reference](RTM.md) -- Companion document that proves RS requirements are met
- [Code Governance](../09-Code-Governance.md) -- Merge gate requires EFFECTIVE RS
- [Change Control](../04-Change-Control.md) -- CR closure prerequisites for SDLC-governed systems
- [QMS Glossary](../QMS-Glossary.md) -- Term definitions
