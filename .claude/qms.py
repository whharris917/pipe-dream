#!/usr/bin/env python3
"""
QMS - Quality Management System CLI

Document control system for the Flow State project.
See SOP-001 for complete documentation.

Usage:
    python .claude/qms.py <command> [options]

Commands:
    create, read, checkout, checkin, route, review, approve, reject,
    release, revert, close, status, inbox, workspace
"""

import argparse
import os
import sys
import shutil
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum
import yaml


# =============================================================================
# Configuration
# =============================================================================

# Find project root (directory containing QMS/)
def find_project_root() -> Path:
    """Find the project root by looking for QMS/ directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / "QMS").is_dir():
            return current
        current = current.parent
    # Fallback: assume we're in project root or .claude/
    if Path("QMS").is_dir():
        return Path.cwd()
    elif Path("../QMS").is_dir():
        return Path.cwd().parent
    raise FileNotFoundError("Cannot find QMS/ directory. Are you in the project?")


PROJECT_ROOT = find_project_root()
QMS_ROOT = PROJECT_ROOT / "QMS"
ARCHIVE_ROOT = QMS_ROOT / ".archive"
USERS_ROOT = PROJECT_ROOT / ".claude" / "users"

# Document type configurations
DOCUMENT_TYPES = {
    "SOP": {"path": "SOP", "executable": False, "prefix": "SOP"},
    "CR": {"path": "CR", "executable": True, "prefix": "CR", "folder_per_doc": True},
    "INV": {"path": "INV", "executable": True, "prefix": "INV", "folder_per_doc": True},
    "CAPA": {"path": "INV", "executable": True, "prefix": "CAPA", "parent_type": "INV"},
    "TP": {"path": "CR", "executable": True, "prefix": "TP", "parent_type": "CR"},
    "ER": {"path": "CR", "executable": True, "prefix": "ER", "parent_type": "TP"},
    "RS": {"path": "SDLC-FLOW", "executable": False, "prefix": "SDLC-FLOW-RS", "singleton": True},
    "DS": {"path": "SDLC-FLOW", "executable": False, "prefix": "SDLC-FLOW-DS", "singleton": True},
    "CS": {"path": "SDLC-FLOW", "executable": False, "prefix": "SDLC-FLOW-CS", "singleton": True},
    "RTM": {"path": "SDLC-FLOW", "executable": False, "prefix": "SDLC-FLOW-RTM", "singleton": True},
    "OQ": {"path": "SDLC-FLOW", "executable": False, "prefix": "SDLC-FLOW-OQ", "singleton": True},
}


# =============================================================================
# Status Enums
# =============================================================================

class Status(Enum):
    # Common
    DRAFT = "DRAFT"

    # Non-executable workflow
    IN_REVIEW = "IN_REVIEW"
    REVIEWED = "REVIEWED"
    IN_APPROVAL = "IN_APPROVAL"
    APPROVED = "APPROVED"
    EFFECTIVE = "EFFECTIVE"

    # Executable workflow
    IN_PRE_REVIEW = "IN_PRE_REVIEW"
    PRE_REVIEWED = "PRE_REVIEWED"
    IN_PRE_APPROVAL = "IN_PRE_APPROVAL"
    PRE_APPROVED = "PRE_APPROVED"
    IN_EXECUTION = "IN_EXECUTION"
    IN_POST_REVIEW = "IN_POST_REVIEW"
    POST_REVIEWED = "POST_REVIEWED"
    IN_POST_APPROVAL = "IN_POST_APPROVAL"
    POST_APPROVED = "POST_APPROVED"
    CLOSED = "CLOSED"

    # Superseded
    SUPERSEDED = "SUPERSEDED"


# Valid transitions
TRANSITIONS = {
    # Non-executable
    Status.DRAFT: [Status.IN_REVIEW, Status.IN_PRE_REVIEW],
    Status.IN_REVIEW: [Status.REVIEWED],
    Status.REVIEWED: [Status.IN_REVIEW, Status.IN_APPROVAL],
    Status.IN_APPROVAL: [Status.APPROVED, Status.REVIEWED],  # REVIEWED on rejection
    Status.APPROVED: [Status.EFFECTIVE],
    Status.EFFECTIVE: [Status.SUPERSEDED],

    # Executable
    Status.IN_PRE_REVIEW: [Status.PRE_REVIEWED],
    Status.PRE_REVIEWED: [Status.IN_PRE_REVIEW, Status.IN_PRE_APPROVAL],
    Status.IN_PRE_APPROVAL: [Status.PRE_APPROVED, Status.PRE_REVIEWED],  # PRE_REVIEWED on rejection
    Status.PRE_APPROVED: [Status.IN_EXECUTION],
    Status.IN_EXECUTION: [Status.IN_POST_REVIEW],
    Status.IN_POST_REVIEW: [Status.POST_REVIEWED],
    Status.POST_REVIEWED: [Status.IN_POST_REVIEW, Status.IN_POST_APPROVAL, Status.IN_EXECUTION],
    Status.IN_POST_APPROVAL: [Status.POST_APPROVED, Status.POST_REVIEWED],  # POST_REVIEWED on rejection
    Status.POST_APPROVED: [Status.CLOSED],
    Status.CLOSED: [],
    Status.SUPERSEDED: [],
}


# =============================================================================
# Utilities
# =============================================================================

def get_current_user() -> str:
    """Get the current QMS user. Must be explicitly set via QMS_USER environment variable."""
    user = os.environ.get("QMS_USER")
    if not user:
        print("Error: QMS_USER environment variable not set.")
        print("Set your identity with: export QMS_USER=<username>")
        print("Valid users: lead, claude, qa, bu, tu_input, tu_ui, tu_scene, tu_sketch, tu_sim")
        sys.exit(1)
    return user


# Valid QMS users
VALID_USERS = {"lead", "claude", "qa", "bu", "tu_input", "tu_ui", "tu_scene", "tu_sketch", "tu_sim"}


def verify_user_identity(user: str) -> bool:
    """Verify that the user is a valid QMS user."""
    if user not in VALID_USERS:
        print(f"Error: '{user}' is not a valid QMS user.")
        print(f"Valid users: {', '.join(sorted(VALID_USERS))}")
        return False
    return True


def verify_folder_access(user: str, target_user: str, operation: str) -> bool:
    """Verify that user has access to target_user's folder."""
    if user != target_user:
        print(f"Error: Access denied. User '{user}' cannot {operation} for user '{target_user}'.")
        print(f"You can only access your own inbox and workspace.")
        return False
    return True


def parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    try:
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2].lstrip("\n")
        return frontmatter or {}, body
    except yaml.YAMLError:
        return {}, content


def serialize_frontmatter(frontmatter: Dict[str, Any], body: str) -> str:
    """Serialize frontmatter and body back to markdown."""
    yaml_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True)
    return f"---\n{yaml_str}---\n\n{body}"


def read_document(path: Path) -> tuple[Dict[str, Any], str]:
    """Read a document and parse its frontmatter."""
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")
    content = path.read_text(encoding="utf-8")
    return parse_frontmatter(content)


def write_document(path: Path, frontmatter: Dict[str, Any], body: str):
    """Write a document with frontmatter."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = serialize_frontmatter(frontmatter, body)
    path.write_text(content, encoding="utf-8")


def get_doc_type(doc_id: str) -> str:
    """Determine document type from doc_id."""
    if doc_id.startswith("SDLC-FLOW-"):
        suffix = doc_id.replace("SDLC-FLOW-", "")
        if suffix in ["RS", "DS", "CS", "RTM", "OQ"]:
            return suffix
    if doc_id.startswith("SOP-"):
        return "SOP"
    if "-TP-ER-" in doc_id:
        return "ER"
    if "-TP" in doc_id:
        return "TP"
    if "-CAPA-" in doc_id:
        return "CAPA"
    if doc_id.startswith("CR-"):
        return "CR"
    if doc_id.startswith("INV-"):
        return "INV"
    raise ValueError(f"Unknown document type for: {doc_id}")


def get_doc_path(doc_id: str, draft: bool = False) -> Path:
    """Get the path to a document."""
    doc_type = get_doc_type(doc_id)
    config = DOCUMENT_TYPES[doc_type]

    base_path = QMS_ROOT / config["path"]

    # Handle folder-per-doc types (CR, INV)
    if config.get("folder_per_doc"):
        # Extract the parent folder (e.g., CR-001 from CR-001-TP)
        if doc_type in ["TP", "ER"]:
            # CR-001-TP -> CR-001, CR-001-TP-ER-001 -> CR-001
            match = re.match(r"(CR-\d+)", doc_id)
            if match:
                base_path = base_path / match.group(1)
        elif doc_type == "CAPA":
            # INV-001-CAPA-001 -> INV-001
            match = re.match(r"(INV-\d+)", doc_id)
            if match:
                base_path = base_path / match.group(1)
        else:
            base_path = base_path / doc_id

    filename = f"{doc_id}-draft.md" if draft else f"{doc_id}.md"
    return base_path / filename


def get_archive_path(doc_id: str, version: str) -> Path:
    """Get the archive path for a specific version."""
    doc_type = get_doc_type(doc_id)
    config = DOCUMENT_TYPES[doc_type]

    base_path = ARCHIVE_ROOT / config["path"]

    if config.get("folder_per_doc"):
        if doc_type in ["TP", "ER"]:
            match = re.match(r"(CR-\d+)", doc_id)
            if match:
                base_path = base_path / match.group(1)
        elif doc_type == "CAPA":
            match = re.match(r"(INV-\d+)", doc_id)
            if match:
                base_path = base_path / match.group(1)
        else:
            base_path = base_path / doc_id

    return base_path / f"{doc_id}-v{version}.md"


def get_workspace_path(user: str, doc_id: str) -> Path:
    """Get the workspace path for a user's checked-out document."""
    return USERS_ROOT / user / "workspace" / f"{doc_id}.md"


def get_inbox_path(user: str) -> Path:
    """Get the inbox directory for a user."""
    return USERS_ROOT / user / "inbox"


def get_next_number(doc_type: str) -> int:
    """Get the next available number for a document type."""
    config = DOCUMENT_TYPES[doc_type]
    base_path = QMS_ROOT / config["path"]

    if not base_path.exists():
        return 1

    pattern = re.compile(rf"^{config['prefix']}-(\d+)")
    max_num = 0

    # Check both files and directories
    for item in base_path.iterdir():
        name = item.stem if item.is_file() else item.name
        # Remove -draft suffix if present
        name = name.replace("-draft", "")
        match = pattern.match(name)
        if match:
            max_num = max(max_num, int(match.group(1)))

    return max_num + 1


def today() -> str:
    """Get today's date as YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")


# =============================================================================
# Commands
# =============================================================================

def cmd_create(args):
    """Create a new document."""
    user = get_current_user()

    if not verify_user_identity(user):
        return 1

    doc_type = args.type.upper()

    if doc_type not in DOCUMENT_TYPES:
        print(f"Error: Unknown document type '{doc_type}'")
        print(f"Valid types: {', '.join(DOCUMENT_TYPES.keys())}")
        return 1

    config = DOCUMENT_TYPES[doc_type]

    # Generate doc_id
    if config.get("singleton"):
        doc_id = config["prefix"]
    else:
        next_num = get_next_number(doc_type)
        doc_id = f"{config['prefix']}-{next_num:03d}"

    # Check if already exists
    effective_path = get_doc_path(doc_id, draft=False)
    draft_path = get_doc_path(doc_id, draft=True)

    if effective_path.exists() or draft_path.exists():
        print(f"Error: {doc_id} already exists")
        return 1

    # Create directory structure if needed
    if config.get("folder_per_doc"):
        folder_path = QMS_ROOT / config["path"] / doc_id
        folder_path.mkdir(parents=True, exist_ok=True)

    # Create frontmatter
    frontmatter = {
        "doc_id": doc_id,
        "title": args.title or f"{doc_type} - [Title]",
        "version": "0.1",
        "status": "DRAFT",
        "document_type": doc_type,
        "executable": config["executable"],
        "responsible_user": user,
        "checked_out": True,
        "checked_out_date": today(),
        "effective_version": None,
        "supersedes": None,
        "review_history": [],
        "approval_history": [],
    }

    # Create body template
    body = f"""# {doc_id}: {args.title or '[Title]'}

**Version:** 0.1 (DRAFT)
**Effective Date:** TBD
**Responsible User:** {user}

---

## 1. Purpose

[Describe the purpose of this document]

---

## 2. Scope

[Define what this document covers]

---

## 3. Content

[Main content here]

---

## Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 0.1 | {today()} | {user} | Initial draft |

---

**END OF DOCUMENT**
"""

    # Write to draft path
    write_document(draft_path, frontmatter, body)

    # Copy to user's workspace
    workspace_path = get_workspace_path(user, doc_id)
    workspace_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(draft_path, workspace_path)

    print(f"Created: {doc_id} (v0.1, DRAFT)")
    print(f"Location: {draft_path.relative_to(PROJECT_ROOT)}")
    print(f"Workspace: {workspace_path.relative_to(PROJECT_ROOT)}")
    print(f"Responsible User: {user}")

    return 0


def cmd_read(args):
    """Read a document."""
    doc_id = args.doc_id

    try:
        if args.version:
            # Read specific archived version
            path = get_archive_path(doc_id, args.version)
        elif args.draft:
            path = get_doc_path(doc_id, draft=True)
        else:
            # Read effective version, fall back to draft
            path = get_doc_path(doc_id, draft=False)
            if not path.exists():
                path = get_doc_path(doc_id, draft=True)

        if not path.exists():
            print(f"Error: Document not found: {doc_id}")
            return 1

        content = path.read_text(encoding="utf-8")
        print(content)
        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_checkout(args):
    """Check out a document for editing."""
    doc_id = args.doc_id
    user = get_current_user()

    if not verify_user_identity(user):
        return 1

    # Find the document (effective or draft)
    effective_path = get_doc_path(doc_id, draft=False)
    draft_path = get_doc_path(doc_id, draft=True)

    if draft_path.exists():
        # Already a draft - check if already checked out
        frontmatter, body = read_document(draft_path)
        if frontmatter.get("checked_out"):
            current_owner = frontmatter.get("responsible_user", "unknown")
            if current_owner == user:
                print(f"You already have {doc_id} checked out")
            else:
                print(f"Error: {doc_id} is checked out by {current_owner}")
            return 1

        # Check out existing draft
        frontmatter["checked_out"] = True
        frontmatter["checked_out_date"] = today()
        frontmatter["responsible_user"] = user
        write_document(draft_path, frontmatter, body)
        source_path = draft_path

    elif effective_path.exists():
        # Create new draft from effective
        frontmatter, body = read_document(effective_path)
        current_version = str(frontmatter.get("version", "1.0"))
        major = int(current_version.split(".")[0])
        new_version = f"{major}.1"

        frontmatter["version"] = new_version
        frontmatter["status"] = "DRAFT"
        frontmatter["checked_out"] = True
        frontmatter["checked_out_date"] = today()
        frontmatter["responsible_user"] = user
        frontmatter["effective_version"] = current_version

        write_document(draft_path, frontmatter, body)
        source_path = draft_path

        # Mark effective as having a draft
        eff_fm, eff_body = read_document(effective_path)
        eff_fm["has_draft"] = True
        write_document(effective_path, eff_fm, eff_body)

        print(f"Created draft v{new_version} from effective v{current_version}")
    else:
        print(f"Error: Document not found: {doc_id}")
        return 1

    # Copy to workspace
    workspace_path = get_workspace_path(user, doc_id)
    workspace_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(source_path, workspace_path)

    print(f"Checked out: {doc_id}")
    print(f"Workspace: {workspace_path.relative_to(PROJECT_ROOT)}")

    return 0


def cmd_checkin(args):
    """Check in a document from workspace."""
    doc_id = args.doc_id
    user = get_current_user()

    if not verify_user_identity(user):
        return 1

    workspace_path = get_workspace_path(user, doc_id)
    if not workspace_path.exists():
        print(f"Error: {doc_id} not in your workspace")
        return 1

    draft_path = get_doc_path(doc_id, draft=True)

    # Verify user has it checked out
    if draft_path.exists():
        frontmatter, _ = read_document(draft_path)
        if frontmatter.get("responsible_user") != user:
            print(f"Error: {doc_id} is not checked out by you")
            return 1

    # Read workspace version
    frontmatter, body = read_document(workspace_path)

    # Archive previous draft if exists and version differs
    if draft_path.exists():
        old_fm, old_body = read_document(draft_path)
        old_version = str(old_fm.get("version", "0.1"))
        new_version = str(frontmatter.get("version", "0.1"))
        if old_version != new_version:
            archive_path = get_archive_path(doc_id, old_version)
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(draft_path, archive_path)
            print(f"Archived: v{old_version}")

    # Copy workspace to QMS
    shutil.copy(workspace_path, draft_path)

    print(f"Checked in: {doc_id} (v{frontmatter.get('version', '?')})")

    return 0


def cmd_route(args):
    """Route a document for review or approval."""
    doc_id = args.doc_id
    user = get_current_user()

    if not verify_user_identity(user):
        return 1

    assignees = args.assign

    if not assignees:
        print("Error: Must specify --assign with at least one user")
        return 1

    draft_path = get_doc_path(doc_id, draft=True)
    if not draft_path.exists():
        print(f"Error: No draft found for {doc_id}")
        return 1

    frontmatter, body = read_document(draft_path)

    # Verify ownership
    if frontmatter.get("responsible_user") != user:
        print(f"Error: You are not the responsible user for {doc_id}")
        return 1

    current_status = Status(frontmatter.get("status", "DRAFT"))
    is_executable = frontmatter.get("executable", False)

    # Determine target status based on flags
    if args.review:
        if is_executable:
            print("Error: Use --pre-review or --post-review for executable documents")
            return 1
        target_status = Status.IN_REVIEW
        workflow_type = "REVIEW"
    elif args.pre_review:
        if not is_executable:
            print("Error: --pre-review is only for executable documents")
            return 1
        target_status = Status.IN_PRE_REVIEW
        workflow_type = "PRE_REVIEW"
    elif args.post_review:
        if not is_executable:
            print("Error: --post-review is only for executable documents")
            return 1
        target_status = Status.IN_POST_REVIEW
        workflow_type = "POST_REVIEW"
    elif args.approval:
        if is_executable:
            print("Error: Use --pre-approval or --post-approval for executable documents")
            return 1
        if current_status != Status.REVIEWED:
            print(f"Error: Must be REVIEWED before approval (currently {current_status.value})")
            return 1
        target_status = Status.IN_APPROVAL
        workflow_type = "APPROVAL"
    elif args.pre_approval:
        if not is_executable:
            print("Error: --pre-approval is only for executable documents")
            return 1
        if current_status != Status.PRE_REVIEWED:
            print(f"Error: Must be PRE_REVIEWED before pre-approval (currently {current_status.value})")
            return 1
        target_status = Status.IN_PRE_APPROVAL
        workflow_type = "PRE_APPROVAL"
    elif args.post_approval:
        if not is_executable:
            print("Error: --post-approval is only for executable documents")
            return 1
        if current_status != Status.POST_REVIEWED:
            print(f"Error: Must be POST_REVIEWED before post-approval (currently {current_status.value})")
            return 1
        target_status = Status.IN_POST_APPROVAL
        workflow_type = "POST_APPROVAL"
    else:
        print("Error: Must specify workflow type (--review, --approval, etc.)")
        return 1

    # Validate transition
    if target_status not in TRANSITIONS.get(current_status, []):
        print(f"Error: Cannot transition from {current_status.value} to {target_status.value}")
        return 1

    # Update frontmatter
    frontmatter["status"] = target_status.value

    # Add to review/approval history
    history_key = "review_history" if "REVIEW" in workflow_type else "approval_history"
    history = frontmatter.get(history_key, [])

    round_num = len([h for h in history if h.get("type") == workflow_type]) + 1

    history_entry = {
        "round": round_num,
        "type": workflow_type,
        "date_initiated": today(),
        "assignees": [{"user": u, "status": "PENDING", "date": None, "comments": None} for u in assignees]
    }
    history.append(history_entry)
    frontmatter[history_key] = history

    # Write updated document
    write_document(draft_path, frontmatter, body)

    # Create tasks in assignee inboxes
    for assignee in assignees:
        inbox_path = get_inbox_path(assignee)
        inbox_path.mkdir(parents=True, exist_ok=True)

        task_type = "REVIEW" if "REVIEW" in workflow_type else "APPROVAL"
        task_id = f"task-{doc_id}-{workflow_type.lower()}-r{round_num}"
        task_path = inbox_path / f"{task_id}.md"

        task_content = f"""---
task_id: {task_id}
task_type: {task_type}
workflow_type: {workflow_type}
doc_id: {doc_id}
assigned_by: {user}
assigned_date: {today()}
round: {round_num}
---

# {task_type} Request: {doc_id}

**Workflow:** {workflow_type}
**Round:** {round_num}
**Assigned By:** {user}
**Date:** {today()}

Please {'review' if task_type == 'REVIEW' else 'approve or reject'} {doc_id}.

## Commands

{'```' + f'qms review {doc_id} --comment "Your review comments"' + '```' if task_type == 'REVIEW' else '```' + f'qms approve {doc_id}' + '```' + ' or ' + '```' + f'qms reject {doc_id} --comment "Rejection reason"' + '```'}
"""
        task_path.write_text(task_content, encoding="utf-8")

    print(f"Routed: {doc_id} for {workflow_type}")
    print(f"Status: {current_status.value} -> {target_status.value}")
    print(f"Assigned to: {', '.join(assignees)}")

    return 0


def cmd_review(args):
    """Submit a review for a document."""
    doc_id = args.doc_id
    user = get_current_user()

    if not verify_user_identity(user):
        return 1

    comment = args.comment

    if not comment:
        print("Error: Must provide --comment with review")
        return 1

    draft_path = get_doc_path(doc_id, draft=True)
    if not draft_path.exists():
        print(f"Error: No draft found for {doc_id}")
        return 1

    frontmatter, body = read_document(draft_path)
    current_status = Status(frontmatter.get("status", "DRAFT"))

    # Verify document is in a review state
    review_statuses = [Status.IN_REVIEW, Status.IN_PRE_REVIEW, Status.IN_POST_REVIEW]
    if current_status not in review_statuses:
        print(f"Error: {doc_id} is not in review (status: {current_status.value})")
        return 1

    # Find current review round and update user's entry
    review_history = frontmatter.get("review_history", [])
    current_round = None
    for entry in reversed(review_history):
        if entry.get("type") in ["REVIEW", "PRE_REVIEW", "POST_REVIEW"]:
            for assignee in entry.get("assignees", []):
                if assignee.get("user") == user and assignee.get("status") == "PENDING":
                    assignee["status"] = "COMPLETE"
                    assignee["date"] = today()
                    assignee["comments"] = comment
                    current_round = entry
                    break
            if current_round:
                break

    if not current_round:
        print(f"Error: You are not assigned to review {doc_id}")
        return 1

    # Check if all reviews complete
    all_complete = all(a.get("status") == "COMPLETE" for a in current_round.get("assignees", []))

    if all_complete:
        # Transition to REVIEWED state
        status_map = {
            Status.IN_REVIEW: Status.REVIEWED,
            Status.IN_PRE_REVIEW: Status.PRE_REVIEWED,
            Status.IN_POST_REVIEW: Status.POST_REVIEWED,
        }
        new_status = status_map.get(current_status)
        if new_status:
            frontmatter["status"] = new_status.value
            print(f"All reviews complete. Status: {current_status.value} -> {new_status.value}")

    write_document(draft_path, frontmatter, body)

    # Remove task from inbox
    inbox_path = get_inbox_path(user)
    for task_file in inbox_path.glob(f"task-{doc_id}-*.md"):
        task_file.unlink()

    print(f"Review submitted for {doc_id}")

    return 0


def cmd_approve(args):
    """Approve a document."""
    doc_id = args.doc_id
    user = get_current_user()

    if not verify_user_identity(user):
        return 1

    draft_path = get_doc_path(doc_id, draft=True)
    if not draft_path.exists():
        print(f"Error: No draft found for {doc_id}")
        return 1

    frontmatter, body = read_document(draft_path)
    current_status = Status(frontmatter.get("status", "DRAFT"))
    is_executable = frontmatter.get("executable", False)

    # Verify document is in an approval state
    approval_statuses = [Status.IN_APPROVAL, Status.IN_PRE_APPROVAL, Status.IN_POST_APPROVAL]
    if current_status not in approval_statuses:
        print(f"Error: {doc_id} is not in approval (status: {current_status.value})")
        return 1

    # Find current approval round and update user's entry
    approval_history = frontmatter.get("approval_history", [])
    current_round = None
    for entry in reversed(approval_history):
        for assignee in entry.get("assignees", []):
            if assignee.get("user") == user and assignee.get("status") == "PENDING":
                assignee["status"] = "APPROVED"
                assignee["date"] = today()
                current_round = entry
                break
        if current_round:
            break

    if not current_round:
        print(f"Error: You are not assigned to approve {doc_id}")
        return 1

    # Check if all approvals complete
    all_approved = all(a.get("status") == "APPROVED" for a in current_round.get("assignees", []))

    if all_approved:
        # Transition to APPROVED state and bump version
        status_map = {
            Status.IN_APPROVAL: Status.APPROVED,
            Status.IN_PRE_APPROVAL: Status.PRE_APPROVED,
            Status.IN_POST_APPROVAL: Status.POST_APPROVED,
        }
        new_status = status_map.get(current_status)

        if new_status:
            frontmatter["status"] = new_status.value

            # Bump to major version
            current_version = str(frontmatter.get("version", "0.1"))
            major = int(current_version.split(".")[0])
            new_version = f"{major + 1}.0"
            frontmatter["version"] = new_version

            # Archive current draft
            archive_path = get_archive_path(doc_id, current_version)
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(draft_path, archive_path)

            print(f"All approvals complete. Status: {current_status.value} -> {new_status.value}")
            print(f"Version: {current_version} -> {new_version}")

            # For non-executable, transition to EFFECTIVE
            if new_status == Status.APPROVED:
                frontmatter["status"] = Status.EFFECTIVE.value
                effective_path = get_doc_path(doc_id, draft=False)
                write_document(effective_path, frontmatter, body)
                draft_path.unlink()
                print(f"Document is now EFFECTIVE at {effective_path.relative_to(PROJECT_ROOT)}")
            else:
                # Executable document - stays as draft until closed
                write_document(draft_path, frontmatter, body)
    else:
        # Not all approvals complete yet
        write_document(draft_path, frontmatter, body)

    # Remove task from inbox
    inbox_path = get_inbox_path(user)
    for task_file in inbox_path.glob(f"task-{doc_id}-*.md"):
        task_file.unlink()

    print(f"Approval submitted for {doc_id}")

    return 0


def cmd_reject(args):
    """Reject a document."""
    doc_id = args.doc_id
    user = get_current_user()

    if not verify_user_identity(user):
        return 1

    comment = args.comment

    if not comment:
        print("Error: Must provide --comment with rejection")
        return 1

    draft_path = get_doc_path(doc_id, draft=True)
    if not draft_path.exists():
        print(f"Error: No draft found for {doc_id}")
        return 1

    frontmatter, body = read_document(draft_path)
    current_status = Status(frontmatter.get("status", "DRAFT"))

    # Verify document is in an approval state
    approval_statuses = [Status.IN_APPROVAL, Status.IN_PRE_APPROVAL, Status.IN_POST_APPROVAL]
    if current_status not in approval_statuses:
        print(f"Error: {doc_id} is not in approval (status: {current_status.value})")
        return 1

    # Find current approval round and update user's entry
    approval_history = frontmatter.get("approval_history", [])
    current_round = None
    for entry in reversed(approval_history):
        for assignee in entry.get("assignees", []):
            if assignee.get("user") == user and assignee.get("status") == "PENDING":
                assignee["status"] = "REJECTED"
                assignee["date"] = today()
                assignee["comments"] = comment
                current_round = entry
                break
        if current_round:
            break

    if not current_round:
        print(f"Error: You are not assigned to approve {doc_id}")
        return 1

    # Transition back to REVIEWED state
    status_map = {
        Status.IN_APPROVAL: Status.REVIEWED,
        Status.IN_PRE_APPROVAL: Status.PRE_REVIEWED,
        Status.IN_POST_APPROVAL: Status.POST_REVIEWED,
    }
    new_status = status_map.get(current_status)

    if new_status:
        frontmatter["status"] = new_status.value
        print(f"Document rejected. Status: {current_status.value} -> {new_status.value}")

    write_document(draft_path, frontmatter, body)

    # Remove all pending approval tasks for this document
    for user_dir in USERS_ROOT.iterdir():
        if user_dir.is_dir():
            inbox = user_dir / "inbox"
            if inbox.exists():
                for task_file in inbox.glob(f"task-{doc_id}-*approval*.md"):
                    task_file.unlink()

    print(f"Rejected: {doc_id}")
    print(f"Reason: {comment}")

    return 0


def cmd_release(args):
    """Release an executable document for execution."""
    doc_id = args.doc_id
    user = get_current_user()

    if not verify_user_identity(user):
        return 1

    draft_path = get_doc_path(doc_id, draft=True)
    if not draft_path.exists():
        print(f"Error: No draft found for {doc_id}")
        return 1

    frontmatter, body = read_document(draft_path)

    if not frontmatter.get("executable"):
        print(f"Error: {doc_id} is not an executable document")
        return 1

    if frontmatter.get("responsible_user") != user:
        print(f"Error: You are not the responsible user for {doc_id}")
        return 1

    current_status = Status(frontmatter.get("status", "DRAFT"))
    if current_status != Status.PRE_APPROVED:
        print(f"Error: {doc_id} must be PRE_APPROVED to release (currently {current_status.value})")
        return 1

    frontmatter["status"] = Status.IN_EXECUTION.value
    frontmatter["released_date"] = today()
    write_document(draft_path, frontmatter, body)

    print(f"Released: {doc_id}")
    print(f"Status: PRE_APPROVED -> IN_EXECUTION")

    return 0


def cmd_revert(args):
    """Revert an executable document back to execution."""
    doc_id = args.doc_id
    user = get_current_user()

    if not verify_user_identity(user):
        return 1

    reason = args.reason

    if not reason:
        print("Error: Must provide --reason for revert")
        return 1

    draft_path = get_doc_path(doc_id, draft=True)
    if not draft_path.exists():
        print(f"Error: No draft found for {doc_id}")
        return 1

    frontmatter, body = read_document(draft_path)

    if frontmatter.get("responsible_user") != user:
        print(f"Error: You are not the responsible user for {doc_id}")
        return 1

    current_status = Status(frontmatter.get("status", "DRAFT"))
    if current_status != Status.POST_REVIEWED:
        print(f"Error: {doc_id} must be POST_REVIEWED to revert (currently {current_status.value})")
        return 1

    frontmatter["status"] = Status.IN_EXECUTION.value

    # Log revert
    reverts = frontmatter.get("revert_history", [])
    reverts.append({"date": today(), "user": user, "reason": reason})
    frontmatter["revert_history"] = reverts

    write_document(draft_path, frontmatter, body)

    print(f"Reverted: {doc_id}")
    print(f"Status: POST_REVIEWED -> IN_EXECUTION")
    print(f"Reason: {reason}")

    return 0


def cmd_close(args):
    """Close an executable document."""
    doc_id = args.doc_id
    user = get_current_user()

    if not verify_user_identity(user):
        return 1

    draft_path = get_doc_path(doc_id, draft=True)
    if not draft_path.exists():
        print(f"Error: No draft found for {doc_id}")
        return 1

    frontmatter, body = read_document(draft_path)

    if not frontmatter.get("executable"):
        print(f"Error: {doc_id} is not an executable document")
        return 1

    if frontmatter.get("responsible_user") != user:
        print(f"Error: You are not the responsible user for {doc_id}")
        return 1

    current_status = Status(frontmatter.get("status", "DRAFT"))
    if current_status != Status.POST_APPROVED:
        print(f"Error: {doc_id} must be POST_APPROVED to close (currently {current_status.value})")
        return 1

    frontmatter["status"] = Status.CLOSED.value
    frontmatter["closed_date"] = today()
    frontmatter["checked_out"] = False

    # Move to effective location
    effective_path = get_doc_path(doc_id, draft=False)
    write_document(effective_path, frontmatter, body)
    draft_path.unlink()

    # Remove from workspace
    workspace_path = get_workspace_path(user, doc_id)
    if workspace_path.exists():
        workspace_path.unlink()

    print(f"Closed: {doc_id}")
    print(f"Location: {effective_path.relative_to(PROJECT_ROOT)}")

    return 0


def cmd_status(args):
    """Show document status."""
    doc_id = args.doc_id

    # Try draft first, then effective
    draft_path = get_doc_path(doc_id, draft=True)
    effective_path = get_doc_path(doc_id, draft=False)

    if draft_path.exists():
        path = draft_path
        location = "draft"
    elif effective_path.exists():
        path = effective_path
        location = "effective"
    else:
        print(f"Error: Document not found: {doc_id}")
        return 1

    frontmatter, _ = read_document(path)

    print(f"Document: {doc_id}")
    print(f"Title: {frontmatter.get('title', 'N/A')}")
    print(f"Version: {frontmatter.get('version', 'N/A')}")
    print(f"Status: {frontmatter.get('status', 'N/A')}")
    print(f"Location: {location}")
    print(f"Type: {frontmatter.get('document_type', 'N/A')}")
    print(f"Executable: {frontmatter.get('executable', False)}")
    print(f"Responsible User: {frontmatter.get('responsible_user', 'N/A')}")
    print(f"Checked Out: {frontmatter.get('checked_out', False)}")

    if frontmatter.get("effective_version"):
        print(f"Effective Version: {frontmatter.get('effective_version')}")

    # Show current workflow
    review_history = frontmatter.get("review_history", [])
    if review_history:
        latest = review_history[-1]
        print(f"\nLatest Review ({latest.get('type', 'REVIEW')}, Round {latest.get('round', '?')}):")
        for a in latest.get("assignees", []):
            print(f"  - {a.get('user')}: {a.get('status', 'PENDING')}")

    approval_history = frontmatter.get("approval_history", [])
    if approval_history:
        latest = approval_history[-1]
        print(f"\nLatest Approval ({latest.get('type', 'APPROVAL')}, Round {latest.get('round', '?')}):")
        for a in latest.get("assignees", []):
            print(f"  - {a.get('user')}: {a.get('status', 'PENDING')}")

    return 0


def cmd_inbox(args):
    """List tasks in current user's inbox."""
    user = get_current_user()

    if not verify_user_identity(user):
        return 1

    inbox_path = get_inbox_path(user)

    if not inbox_path.exists():
        print(f"Inbox is empty")
        return 0

    tasks = list(inbox_path.glob("*.md"))
    if not tasks:
        print(f"Inbox is empty")
        return 0

    print(f"Inbox for {user}:")
    print("-" * 60)

    for task_path in sorted(tasks):
        frontmatter, _ = read_document(task_path)
        print(f"  [{frontmatter.get('task_type', '?')}] {frontmatter.get('doc_id', '?')}")
        print(f"    Workflow: {frontmatter.get('workflow_type', '?')}")
        print(f"    From: {frontmatter.get('assigned_by', '?')}")
        print(f"    Date: {frontmatter.get('assigned_date', '?')}")
        print()

    return 0


def cmd_workspace(args):
    """List documents in current user's workspace."""
    user = get_current_user()

    if not verify_user_identity(user):
        return 1

    workspace_path = USERS_ROOT / user / "workspace"

    if not workspace_path.exists():
        print(f"Workspace is empty")
        return 0

    docs = list(workspace_path.glob("*.md"))
    if not docs:
        print(f"Workspace is empty")
        return 0

    print(f"Workspace for {user}:")
    print("-" * 60)

    for doc_path in sorted(docs):
        frontmatter, _ = read_document(doc_path)
        print(f"  {frontmatter.get('doc_id', doc_path.stem)}")
        print(f"    Version: {frontmatter.get('version', '?')}")
        print(f"    Status: {frontmatter.get('status', '?')}")
        print()

    return 0


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="QMS - Quality Management System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  qms create SOP --title "New Procedure"
  qms checkout SOP-001
  qms route SOP-001 --review --assign qa tu_ui
  qms review SOP-001 --comment "Looks good"
  qms approve SOP-001
  qms status SOP-001
  qms inbox
  qms workspace

Environment:
  QMS_USER    Current user (default: claude)
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # create
    p_create = subparsers.add_parser("create", help="Create a new document")
    p_create.add_argument("type", help="Document type (SOP, CR, INV, RS, DS, etc.)")
    p_create.add_argument("--title", help="Document title")

    # read
    p_read = subparsers.add_parser("read", help="Read a document")
    p_read.add_argument("doc_id", help="Document ID")
    p_read.add_argument("--draft", action="store_true", help="Read draft version")
    p_read.add_argument("--version", help="Read specific version (e.g., 1.0)")

    # checkout
    p_checkout = subparsers.add_parser("checkout", help="Check out a document")
    p_checkout.add_argument("doc_id", help="Document ID")

    # checkin
    p_checkin = subparsers.add_parser("checkin", help="Check in a document")
    p_checkin.add_argument("doc_id", help="Document ID")

    # route
    p_route = subparsers.add_parser("route", help="Route document for review/approval")
    p_route.add_argument("doc_id", help="Document ID")
    p_route.add_argument("--review", action="store_true", help="Route for review")
    p_route.add_argument("--pre-review", action="store_true", help="Route for pre-review")
    p_route.add_argument("--post-review", action="store_true", help="Route for post-review")
    p_route.add_argument("--approval", action="store_true", help="Route for approval")
    p_route.add_argument("--pre-approval", action="store_true", help="Route for pre-approval")
    p_route.add_argument("--post-approval", action="store_true", help="Route for post-approval")
    p_route.add_argument("--assign", nargs="+", help="Users to assign")

    # review
    p_review = subparsers.add_parser("review", help="Submit a review")
    p_review.add_argument("doc_id", help="Document ID")
    p_review.add_argument("--comment", required=True, help="Review comments")

    # approve
    p_approve = subparsers.add_parser("approve", help="Approve a document")
    p_approve.add_argument("doc_id", help="Document ID")

    # reject
    p_reject = subparsers.add_parser("reject", help="Reject a document")
    p_reject.add_argument("doc_id", help="Document ID")
    p_reject.add_argument("--comment", required=True, help="Rejection reason")

    # release
    p_release = subparsers.add_parser("release", help="Release for execution")
    p_release.add_argument("doc_id", help="Document ID")

    # revert
    p_revert = subparsers.add_parser("revert", help="Revert to execution")
    p_revert.add_argument("doc_id", help="Document ID")
    p_revert.add_argument("--reason", required=True, help="Revert reason")

    # close
    p_close = subparsers.add_parser("close", help="Close a document")
    p_close.add_argument("doc_id", help="Document ID")

    # status
    p_status = subparsers.add_parser("status", help="Show document status")
    p_status.add_argument("doc_id", help="Document ID")

    # inbox
    p_inbox = subparsers.add_parser("inbox", help="List inbox tasks")

    # workspace
    p_workspace = subparsers.add_parser("workspace", help="List workspace documents")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "create": cmd_create,
        "read": cmd_read,
        "checkout": cmd_checkout,
        "checkin": cmd_checkin,
        "route": cmd_route,
        "review": cmd_review,
        "approve": cmd_approve,
        "reject": cmd_reject,
        "release": cmd_release,
        "revert": cmd_revert,
        "close": cmd_close,
        "status": cmd_status,
        "inbox": cmd_inbox,
        "workspace": cmd_workspace,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
