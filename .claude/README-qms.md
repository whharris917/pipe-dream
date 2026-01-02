# QMS CLI - Quality Management System

Document control system for the Flow State project. See **SOP-001** for complete procedural documentation.

## Setup

Set your identity before using any commands:

```bash
export QMS_USER=claude    # or: lead, qa, tu_ui, tu_scene, etc.
```

Alias for convenience:

```bash
alias qms='python .claude/qms.py'
```

## User Groups & Permissions

| Group | Members | Capabilities |
|-------|---------|--------------|
| **Initiators** | lead, claude | Create, checkout, checkin, route, release, close |
| **QA** | qa | Assign reviewers, review, approve, reject, fix |
| **Reviewers** | tu_input, tu_ui, tu_scene, tu_sketch, tu_sim, bu | Review, approve, reject (when assigned) |

## Commands

### Document Creation & Editing

```bash
# Create a new document (auto-generates ID, auto-checkouts)
qms create SOP --title "My Procedure"
qms create CR --title "Feature Implementation"

# Check out existing document for editing
qms checkout SOP-001

# Check in edited document (saves to QMS, clears checkout)
qms checkin SOP-001

# Read documents
qms read SOP-001                    # Effective version
qms read SOP-001 --draft            # Draft version
qms read SOP-001 --version 1.0      # Archived version
```

### Workflow Routing

**Non-executable documents (SOP, RS, DS, CS, RTM, OQ):**

```bash
qms route SOP-001 --review              # Route for review (QA auto-assigned)
qms route SOP-001 --approval            # Route for approval (after REVIEWED)
```

**Executable documents (CR, INV, CAPA, TP, ER):**

```bash
qms route CR-001 --pre-review           # Before execution
qms route CR-001 --pre-approval         # After PRE_REVIEWED
qms release CR-001                      # Start execution
qms route CR-001 --post-review          # After execution
qms route CR-001 --post-approval        # After POST_REVIEWED
qms close CR-001                        # Finalize
```

### Review & Approval

```bash
# Submit review (must specify outcome)
qms review SOP-001 --recommend --comment "Approved. No issues."
qms review SOP-001 --request-updates --comment "Section 3 needs work."

# Approve or reject
qms approve SOP-001
qms reject SOP-001 --comment "Does not meet requirements."

# QA: Assign additional reviewers
qms assign SOP-001 --user tu_ui tu_scene
```

### Status & Tasks

```bash
qms status SOP-001    # Document status and workflow state
qms inbox             # Your pending review/approval tasks
qms workspace         # Your checked-out documents
```

### Administrative

```bash
# Fix metadata on EFFECTIVE documents (QA/lead only)
qms fix SOP-001
```

## Document Types

| Type | Executable | Description |
|------|------------|-------------|
| SOP | No | Standard Operating Procedure |
| CR | Yes | Change Record |
| INV | Yes | Investigation |
| CAPA | Yes | Corrective/Preventive Action (child of INV) |
| TP | Yes | Test Protocol (child of CR) |
| ER | Yes | Exception Report (child of TP) |
| RS, DS, CS, RTM, OQ | No | SDLC documents (singletons) |

## Workflows

### Non-Executable (SOP, SDLC docs)

```
DRAFT → IN_REVIEW → REVIEWED → IN_APPROVAL → APPROVED → EFFECTIVE
                ↑______________|  (rejection)
```

### Executable (CR, INV, etc.)

```
DRAFT → IN_PRE_REVIEW → PRE_REVIEWED → IN_PRE_APPROVAL → PRE_APPROVED
                    ↑_______________|  (rejection)
                                                              ↓
                                                        IN_EXECUTION
                                                              ↓
        IN_POST_REVIEW → POST_REVIEWED → IN_POST_APPROVAL → POST_APPROVED → CLOSED
                     ↑_______________|  (rejection)
                            ↑_______|  (revert)
```

## Review Outcomes

Reviews require an explicit outcome:

| Flag | Meaning |
|------|---------|
| `--recommend` | Document ready for approval |
| `--request-updates` | Changes required before approval |

**Approval Gate:** Documents cannot be routed for approval unless all reviewers submitted `--recommend`.

## Directory Structure

```
QMS/
├── SOP/                    # Effective SOPs
├── CR/                     # Change Records (folder per CR)
│   └── CR-001/
├── INV/                    # Investigations
└── .archive/               # Historical versions
    └── SOP/
        └── SOP-001-v1.0.md

.claude/users/
├── claude/
│   ├── workspace/          # Checked-out documents
│   └── inbox/              # Pending tasks
├── qa/
└── ...
```

## Version Numbering

| Version | Meaning |
|---------|---------|
| v0.1 | Initial draft |
| v0.2+ | Revisions during review |
| v1.0 | First approval |
| v1.1+ | Revisions after reopening v1.0 |
| v2.0 | Second approval |

## Common Workflows

### Create and approve a new SOP

```bash
export QMS_USER=claude
qms create SOP --title "New Procedure"
# Edit the document in workspace...
qms checkin SOP-003
qms route SOP-003 --review

export QMS_USER=qa
qms review SOP-003 --recommend --comment "Looks good."
qms inbox  # empty now

export QMS_USER=claude
qms route SOP-003 --approval

export QMS_USER=qa
qms approve SOP-003
# Document is now EFFECTIVE
```

### Create and execute a Change Record

```bash
export QMS_USER=claude
qms create CR --title "Add feature X"
qms checkin CR-001
qms route CR-001 --pre-review

export QMS_USER=qa
qms assign CR-001 --user tu_ui        # Assign technical reviewer
qms review CR-001 --recommend --comment "Approach is sound."

export QMS_USER=tu_ui
qms review CR-001 --recommend --comment "UI changes approved."

export QMS_USER=claude
qms route CR-001 --pre-approval

export QMS_USER=qa
qms approve CR-001

export QMS_USER=tu_ui
qms approve CR-001

export QMS_USER=claude
qms release CR-001                     # Begin execution
# ... implement the change ...
qms route CR-001 --post-review

# ... post-review and post-approval ...
qms close CR-001
```

## Error Messages

The CLI provides detailed error messages with guidance when permissions are denied or workflow rules are violated. Example:

```
Permission Denied: 'approve' command

Your role: initiators (claude)
Required role(s): qa, reviewers

As an Initiator (lead, claude), you can:
  - Create new documents: qms create SOP --title "Title"
  ...

You cannot:
  - Approve or reject documents
```

## References

- **SOP-001**: Quality Management System - Document Control (complete procedural documentation)
- **SOP-002**: Change Control (CR workflow details)
