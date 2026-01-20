# A2-DOC: Document Management Domain Review

## Summary
- Total REQs reviewed: 12
- Accurate: 3
- Accurate with issues: 6
- Inaccurate: 3

## Requirement Analysis

### REQ-DOC-001
**Assessment**: INACCURATE
**Completeness**: INCOMPLETE
**Rebuildability**: INSUFFICIENT
**Evidence**:
- `qms_config.py` lines 78-96 define DOCUMENT_TYPES with 16 types:
  - Listed in RS: SOP, CR, INV, TP, ER, VAR, RS, RTM, TEMPLATE (9 types)
  - Missing from RS: DS, CS, OQ, CAPA, QMS-RS, QMS-RTM (6 types)

**Issues**:
1. The RS lists 9 document types, but the code supports 16 distinct types
2. Missing document types include:
   - **DS** (Design Specification) - `qms_config.py:87`
   - **CS** (Code Specification) - `qms_config.py:88`
   - **OQ** (Operational Qualification) - `qms_config.py:90`
   - **CAPA** (Corrective and Preventive Action) - `qms_config.py:82`
   - **QMS-RS** (QMS Requirements Specification) - `qms_config.py:92`
   - **QMS-RTM** (QMS Requirements Traceability Matrix) - `qms_config.py:93`
3. RS says "RS, RTM" but code has separate RS and RTM types for different namespaces (SDLC-FLOW-RS, SDLC-QMS-RS, etc.)

**Recommendation**: REVISE - Update RS to list all 16 supported document types with brief descriptions

---

### REQ-DOC-002
**Assessment**: PARTIAL
**Completeness**: INCOMPLETE
**Rebuildability**: INSUFFICIENT
**Evidence**:
- `qms_config.py` lines 82-85 define parent-child relationships:
  ```python
  "CAPA": {"path": "INV", "executable": True, "prefix": "CAPA", "parent_type": "INV"},
  "TP": {"path": "CR", "executable": True, "prefix": "TP", "parent_type": "CR"},
  "ER": {"path": "CR", "executable": True, "prefix": "ER", "parent_type": "TP"},
  ```
- `qms_paths.py` lines 84-98 handle nested path resolution
- `create.py` lines 59-78 enforce parent requirements

**Issues**:
1. RS only mentions TP/ER/VAR parent relationships; CAPA (child of INV) is missing
2. RS states "VAR is a child of CR or INV" - Code confirms this at `qms_paths.py:87-92`
3. RS states "TP is a child of CR" - Code confirms at `create.py:68-70`
4. RS states "ER is a child of TP" - But code only allows ER creation through TP, and TP singular ID means only ONE TP per CR (`create.py:84-85`)
5. RS does not mention that TP has a **singular ID** format (CR-001-TP, not CR-001-TP-001)
6. RS does not mention CAPA being a child of INV - but `qms_config.py:82` defines this
7. Code at `create.py:59` only enforces parent for VAR and TP, not for ER or CAPA

**Recommendation**: REVISE - Add CAPA relationship, document singular TP ID format, clarify ER creation mechanism

---

### REQ-DOC-003
**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT
**Evidence**:
- `qms_paths.py` lines 33-36:
  ```python
  PROJECT_ROOT = find_project_root()
  QMS_ROOT = PROJECT_ROOT / "QMS"
  ARCHIVE_ROOT = QMS_ROOT / ".archive"
  USERS_ROOT = PROJECT_ROOT / ".claude" / "users"
  ```
- Actual folder structure verified via `ls` command:
  - `QMS/` contains: CR/, INV/, SOP/, SDLC-FLOW/, SDLC-QMS/, TEMPLATE/
  - `QMS/.meta/` for metadata
  - `QMS/.audit/` for audit trails
  - `QMS/.archive/` for superseded versions
  - `.claude/users/{user}/workspace/` and `.claude/users/{user}/inbox/` for per-user dirs

**Issues**: None

**Recommendation**: PASS

---

### REQ-DOC-004
**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT
**Evidence**:
- `qms_paths.py` lines 153-173 `get_next_number()`:
  ```python
  pattern = re.compile(rf"^{config['prefix']}-(\d+)")
  max_num = 0
  for item in base_path.iterdir():
      name = item.stem if item.is_file() else item.name
      name = name.replace("-draft", "")
      match = pattern.match(name)
      if match:
          max_num = max(max_num, int(match.group(1)))
  return max_num + 1
  ```
- `create.py` lines 98-100:
  ```python
  next_num = get_next_number(doc_type)
  doc_id = f"{config['prefix']}-{next_num:03d}"
  ```

**Issues**: None

**Recommendation**: PASS

---

### REQ-DOC-005
**Assessment**: PARTIAL
**Completeness**: INCOMPLETE
**Rebuildability**: INSUFFICIENT
**Evidence**:
- `qms_paths.py` lines 176-201 `get_next_nested_number()`:
  ```python
  pattern = re.compile(rf"^{re.escape(parent_id)}-{child_type}-(\d+)")
  ```
- `create.py` lines 86-89:
  ```python
  elif doc_type == "VAR" and parent_id:
      next_num = get_next_nested_number(parent_id, "VAR")
      doc_id = f"{parent_id}-VAR-{next_num:03d}"
  ```
- `create.py` lines 83-85 - TP has SINGULAR ID:
  ```python
  elif doc_type == "TP" and parent_id:
      doc_id = f"{parent_id}-TP"  # NOT CR-001-TP-001!
  ```

**Issues**:
1. The RS implies ALL child documents use `{PARENT}-{TYPE}-NNN` format
2. However, TP documents use **singular ID format**: `CR-001-TP` (not `CR-001-TP-001`)
3. Only VAR documents actually use the NNN sequential format within parent
4. ER documents (child of TP) are not explicitly handled in create.py - would be `CR-001-TP-ER-001` based on `qms_paths.py:57`

**Recommendation**: REVISE - Clarify that TP uses singular format, only VAR/ER use sequential within parent

---

### REQ-DOC-006
**Assessment**: ACCURATE
**Completeness**: COMPLETE
**Rebuildability**: SUFFICIENT
**Evidence**:
- `create.py` lines 124-132 initial version:
  ```python
  meta = create_initial_meta(
      doc_id=doc_id,
      doc_type=doc_type,
      version="0.1",  # Initial version
      ...
  )
  ```
- `checkout.py` lines 82-84 new draft from effective:
  ```python
  current_version = meta.get("version", "1.0")
  major = int(str(current_version).split(".")[0])
  new_version = f"{major}.1"
  ```

**Issues**: None - Format N.X is correctly implemented, initial 0.1, bumps to N.1 on checkout from effective

**Recommendation**: PASS

---

### REQ-DOC-007
**Assessment**: ACCURATE
**Completeness**: INCOMPLETE
**Rebuildability**: INSUFFICIENT
**Evidence**:
- `checkout.py` lines 50-75 (draft exists path):
  - Checks if already checked out via `meta.get("checked_out")`
  - Calls `update_meta_checkout(meta, user)` which sets `checked_out=True`, `responsible_user=user`
  - Copies to workspace via `write_document_minimal(workspace_path, frontmatter, body)`
- `checkout.py` lines 77-110 (effective exists path):
  - Creates archive of effective version
  - Sets new version to `{major}.1`
  - Sets status to DRAFT
  - Creates draft file and workspace copy

**Issues**:
1. RS says "copy the document to the user's workspace" but actual behavior also copies to draft location for effective->draft conversion
2. RS does not mention that checking out an effective version archives the current effective version first (`checkout.py:87-90`)
3. RS does not mention the `checked_out_date` field that is set (`qms_meta.py:130`)

**Recommendation**: REVISE - Add archiving behavior, mention checked_out_date field

---

### REQ-DOC-008
**Assessment**: PARTIAL
**Completeness**: INCOMPLETE
**Rebuildability**: INSUFFICIENT
**Evidence**:
- `checkin.py` lines 64-81:
  ```python
  frontmatter, body = read_document(workspace_path)
  write_document_minimal(draft_path, frontmatter, body)
  meta = update_meta_checkin(meta)
  write_meta(doc_id, doc_type, meta)
  workspace_path.unlink()  # Removes from workspace
  ```

**Issues**:
1. RS says "archive any previous draft version" but code does NOT archive drafts on checkin
2. Code at `checkin.py` shows no call to `get_archive_path()` or archive logic
3. Archiving only happens on checkout of effective document (`checkout.py:87-90`)
4. RS says "copy the document from workspace to QMS working directory" - this is accurate
5. RS says "maintain the user as responsible_user" - this is accurate (`qms_meta.py:140-141`)
6. RS does not mention that workspace copy is deleted after checkin (`checkin.py:81`)

**Recommendation**: REVISE - Remove "archive any previous draft version" claim (inaccurate), add workspace deletion behavior

---

### REQ-DOC-009
**Assessment**: PARTIAL
**Completeness**: INCOMPLETE
**Rebuildability**: INSUFFICIENT
**Evidence**:
- `qms_meta.py` lines 156-163 `update_meta_checkin()`:
  ```python
  current_status = meta.get("status", "DRAFT")
  if current_status in ("REVIEWED", "PRE_REVIEWED", "POST_REVIEWED"):
      meta["status"] = "DRAFT"
      meta["pending_reviewers"] = []
      meta["completed_reviewers"] = []
      meta["review_outcomes"] = {}
  ```

**Issues**:
1. RS says status reverts to "DRAFT (for non-executable) or the appropriate pre-review state (for executable)"
2. Code shows ALL reviewed states revert to DRAFT, regardless of executable flag
3. RS mentions reverting to "appropriate pre-review state" for executable - but code just uses DRAFT
4. Code also clears review-related fields (pending_reviewers, completed_reviewers, review_outcomes) - not mentioned in RS
5. RS does not mention the execution_phase preservation logic (`qms_meta.py:153-154`)

**Recommendation**: REVISE - Clarify that all reviewed states revert to DRAFT (not different behavior for executable), add review field clearing

---

### REQ-DOC-010
**Assessment**: ACCURATE
**Completeness**: INCOMPLETE
**Rebuildability**: INSUFFICIENT
**Evidence**:
- `cancel.py` lines 49-55:
  ```python
  version = meta.get("version", "0.1")
  major = int(version.split(".")[0])
  if major >= 1:
      print(f"Error: Cannot cancel {doc_id} - it was effective (v{version}).")
      return 1
  ```
- `cancel.py` lines 76-106 deletion logic:
  - Deletes document file(s)
  - Deletes .meta file
  - Deletes .audit file
  - Also cleans up workspace copies for all users
  - Also cleans up inbox tasks

**Issues**:
1. RS accurately describes version < 1.0 restriction
2. RS accurately describes deletion of document file, metadata, and audit trail
3. RS does NOT mention cleanup of workspace copies (`cancel.py:108-114`)
4. RS does NOT mention cleanup of inbox tasks (`cancel.py:116-122`)
5. RS does NOT mention the --confirm flag requirement (`cancel.py:65-73`)
6. RS does NOT mention that checked-out documents cannot be cancelled (`cancel.py:58-62`)

**Recommendation**: REVISE - Add --confirm requirement, checked-out restriction, workspace/inbox cleanup

---

### REQ-DOC-011
**Assessment**: PARTIAL
**Completeness**: INCOMPLETE
**Rebuildability**: INSUFFICIENT
**Evidence**:
- `create.py` lines 90-97:
  ```python
  elif doc_type == "TEMPLATE":
      name = getattr(args, 'name', None)
      if name:
          doc_id = f"TEMPLATE-{name.upper()}"
      else:
          next_num = get_next_number(doc_type)
          doc_id = f"{config['prefix']}-{next_num:03d}"
  ```

**Issues**:
1. RS says "name shall be specified at creation time" implying it's required
2. Code shows name is OPTIONAL - if not provided, falls back to sequential numbering (TEMPLATE-001)
3. Name is uppercased in code (`name.upper()`) - not mentioned in RS

**Recommendation**: REVISE - Clarify that --name is optional with fallback to sequential, mention uppercase conversion

---

### REQ-DOC-012
**Assessment**: INACCURATE
**Completeness**: INCOMPLETE
**Rebuildability**: INSUFFICIENT
**Evidence**:
- `qms_config.py` lines 86-93 shows SDLC document configuration:
  ```python
  "RS": {"path": "SDLC-FLOW", "executable": False, "prefix": "SDLC-FLOW-RS", "singleton": True},
  "DS": {"path": "SDLC-FLOW", ...},
  "CS": {"path": "SDLC-FLOW", ...},
  "RTM": {"path": "SDLC-FLOW", ...},
  "OQ": {"path": "SDLC-FLOW", ...},
  "QMS-RS": {"path": "SDLC-QMS", "executable": False, "prefix": "SDLC-QMS-RS", "singleton": True},
  "QMS-RTM": {"path": "SDLC-QMS", ...},
  ```
- `qms_paths.py` lines 43-52 show SDLC namespace detection:
  ```python
  if doc_id.startswith("SDLC-QMS-"):
      suffix = doc_id.replace("SDLC-QMS-", "")
      if suffix in ["RS", "RTM"]:
          return f"QMS-{suffix}"
  if doc_id.startswith("SDLC-FLOW-"):
      suffix = doc_id.replace("SDLC-FLOW-", "")
      if suffix in ["RS", "DS", "CS", "RTM", "OQ"]:
          return suffix
  ```

**Issues**:
1. RS says "RS and RTM documents for configured SDLC namespaces" - but code also supports DS, CS, OQ
2. RS mentions "explicit configuration in DOCUMENT_TYPES" - accurate
3. RS mentions storage in `QMS/SDLC-{NAMESPACE}/` - accurate (SDLC-FLOW, SDLC-QMS)
4. RS does not mention that these are **singleton** documents (only one RS per namespace)
5. RS does not explain the doc_type vs doc_id mapping (e.g., doc_type "RS" creates doc_id "SDLC-FLOW-RS")
6. RS does not mention QMS-RS and QMS-RTM internal type names

**Recommendation**: REVISE - Add DS, CS, OQ types; explain singleton behavior; clarify type-to-ID mapping

---

## Undocumented Functionality

### 1. Document Type Extensions
The following document types exist in code but are not documented in REQ-DOC-001:
- **CAPA** - Corrective and Preventive Action (child of INV)
- **DS** - Design Specification (SDLC-FLOW singleton)
- **CS** - Code Specification (SDLC-FLOW singleton)
- **OQ** - Operational Qualification (SDLC-FLOW singleton)
- **QMS-RS** - QMS Requirements Specification (SDLC-QMS singleton)
- **QMS-RTM** - QMS Requirements Traceability Matrix (SDLC-QMS singleton)

### 2. Singleton Document Types
Several document types are "singleton" (only one document per type/namespace):
- RS, DS, CS, RTM, OQ (SDLC-FLOW namespace)
- QMS-RS, QMS-RTM (SDLC-QMS namespace)

This singleton behavior is not documented in any requirement.

### 3. folder_per_doc Configuration
`qms_config.py` line 80-81 shows:
```python
"CR": {"path": "CR", "executable": True, "prefix": "CR", "folder_per_doc": True},
"INV": {"path": "INV", "executable": True, "prefix": "INV", "folder_per_doc": True},
```
CR and INV documents get their own subdirectory. This structural behavior is implicit but not explicitly required.

### 4. TP Singular ID Format
TP documents use `CR-001-TP` format (not `CR-001-TP-001`) per `create.py:84-85`. This is a deliberate design decision not captured in requirements.

### 5. ER and CAPA Creation
While ER and CAPA are defined in DOCUMENT_TYPES with parent_type relationships:
- `create.py` only enforces --parent for VAR and TP (line 59)
- ER and CAPA creation mechanism is undefined in the code
- No tests exist for ER or CAPA creation

### 6. Checked-Out Document Restrictions
`cancel.py` lines 58-62 prevent cancellation of checked-out documents. This restriction is not documented.

### 7. Archive Behavior on Checkout
`checkout.py` lines 87-90 archive the effective version before creating a draft. This is not documented in REQ-DOC-007.

### 8. Workspace Deletion on Checkin
`checkin.py` line 81 deletes the workspace copy after checkin. Not documented in REQ-DOC-008.

---

## Recommended Actions

### Priority 1: Critical Gaps
1. **ADD_REQ**: Create requirement for CAPA document type and INV parent relationship
2. **REVISE REQ-DOC-001**: Expand to include all 16 document types (DS, CS, OQ, CAPA, QMS-RS, QMS-RTM)
3. **REVISE REQ-DOC-008**: Remove incorrect "archive previous draft" claim - drafts are NOT archived on checkin

### Priority 2: Accuracy Corrections
4. **REVISE REQ-DOC-002**: Add CAPA child relationship, document TP singular ID format
5. **REVISE REQ-DOC-005**: Clarify TP uses singular format, only VAR/ER use sequential
6. **REVISE REQ-DOC-009**: Clarify all reviewed states revert to DRAFT regardless of executable flag
7. **REVISE REQ-DOC-012**: Add DS, CS, OQ types; explain singleton behavior

### Priority 3: Completeness Enhancements
8. **REVISE REQ-DOC-007**: Add archiving behavior for effective->draft conversion
9. **REVISE REQ-DOC-010**: Add --confirm requirement, checked-out restriction
10. **REVISE REQ-DOC-011**: Clarify --name is optional with sequential fallback

### Priority 4: New Requirements
11. **ADD_REQ**: Singleton document type behavior (one per namespace)
12. **ADD_REQ**: folder_per_doc behavior for CR and INV
13. **ADD_REQ**: ER creation mechanism (currently undefined in code)
