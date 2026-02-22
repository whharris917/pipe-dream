---
title: Attachment Auto-Close + VR Template/Compiler Refinements
revision_summary: Execution complete — all 12 EIs passed, 673 tests, no variances
---

# CR-095: Attachment Auto-Close + VR Template/Compiler Refinements

## 1. Purpose

Implement attachment document lifecycle management (cascade close, checkout guard) and refine VR template/compiler output quality based on Lead review of CR-094-ADD-001-VR-001.

---

## 2. Scope

### 2.1 Context

Lead review of CR-094-ADD-001-VR-001 compiled output identified template and compiler deficiencies. Additionally, VR documents lack lifecycle integration with their parent documents — they retain `-draft` suffixes after parent closure, can be checked out after closure, and don't auto-close when their parent closes.

- **Parent Document:** None (independent improvement)

### 2.2 Changes Summary

Two themes bundled into one CR, both scoped to `qms-cli/`:

**Theme A: Attachment Auto-Close** — Generic attachment document class with cascade close on parent closure, terminal state checkout guard, and relaxed close requirements for attachments.

**Theme B: VR Template & Compiler Refinements** — Remove redundant prompts/sections, strip redundant labels, add step subsection numbering, auto-generate metadata, block-render all non-table responses with attribution below blockquotes.

### 2.3 Files Affected

- `qms-cli/qms_config.py` — Add `attachment: True` to VR document type
- `qms-cli/commands/checkout.py` — Terminal state checkout guard
- `qms-cli/commands/close.py` — Attachment close flexibility, cascade close helper, auto-compile for checked-out interactive attachments
- `qms-cli/seed/templates/TEMPLATE-VR.md` — Remove prompts/sections, rename heading, strip labels, subsection headings, version bump to 5
- `qms-cli/interact_compiler.py` — Auto-metadata injection, block rendering for all non-table responses, attribution placement below blockquotes, step subsection numbering
- `qms-cli/tests/test_interact_compiler.py` — Update existing tests, add new test classes
- `qms-cli/tests/test_attachment_lifecycle.py` — New tests for checkout guard and cascade close

---

## 3. Current State

VR documents have no lifecycle coupling to their parent document. A parent CR can close while its VR children remain IN_EXECUTION with `-draft` suffixes. Closed documents can be checked out again. VR compiled output has redundant prompts (date, performer), unnecessary sections (Signature, References), attribution placed inside blockquotes, no visual distinction between label and block context, and flat step headings.

---

## 4. Proposed State

VR documents are classified as "attachments" — a generic property on document types. When a parent document closes, all non-terminal attachment children are automatically closed. Closed/retired documents cannot be checked out. Attachments can be directly closed from any non-terminal status (no POST_APPROVED requirement). VR compiled output has auto-generated metadata, block-rendered responses with attribution below blockquotes, subsection-numbered steps, and no redundant sections.

---

## 5. Change Description

### 5.1 Attachment Classification (A1)

Add `"attachment": True` to VR entry in `DOCUMENT_TYPES`. This is the extensibility point — future attachment types get cascade close behavior for free.

### 5.2 Terminal State Checkout Guard (A2)

Insert 3-line guard in `checkout.py` after meta status read: if status is CLOSED or RETIRED, reject with error message.

### 5.3 Attachment Close Flexibility (A3)

In `close.py`, check if document type is an attachment. If so, allow closure from any non-terminal status and skip the POST_APPROVED requirement. Non-attachments retain existing behavior.

### 5.4 Cascade Close (A4)

After closing a parent document, iterate all document types with `attachment: True`, scan `.meta/` for children matching the parent ID, and close each non-terminal child. For checked-out interactive attachments, auto-compile from `.interact` session or `.source.json` before closing. Clean up workspace files across all users.

### 5.5 TEMPLATE-VR v5 (B1)

Remove `date` prompt (auto-generated). Remove `performer` and `performed_date` prompts (auto-generated). Remove Section 6 (Signature) and Section 7 (References). Rename "Pre-Conditions" to "Prerequisites". Strip redundant labels (`**Objective:**`, `**Overall Outcome:**`, `**Expected:**`, `**Outcome:**`). Change step headings from `### Step {{_n}}` to `### 4.{{_n}} Step {{_n}}`. Bump version to 5.

### 5.6 Auto-Generated Metadata (B2)

In `compile_document()`, inject `date`, `performer`, `performed_date` into `source["metadata"]` from response timestamps and authors. Only inject if not already present (preserving explicit values).

### 5.7 Block Rendering + Attribution Placement (B3)

In `_substitute_line()`, eliminate "label context" distinction. Any non-table line with a response substitution gets block rendering: value in blockquote via `_render_value_only()`, attribution via `_render_attributions()` on a separate line below the closing blockquote.

### 5.8 Step Subsection Numbering (B4)

In `_expand_loops()`, update regex to match `### 4. Step ` (Phase 2 output of `### 4.{{_n}} Step {{_n}}`). Generate headings as `### 4.N Step N`. Include backward-compatible fallback for unnumbered `### Step`.

### 5.9 Block-Rendered Step Content (B5)

In `_expand_loops()`, render `step_expected` and `step_outcome` as blockquotes with attribution below. `step_actual` remains as code fence. `step_instructions` remains as bold value.

---

## 6. Justification

- VR documents accumulate as orphans when parents close without cascade logic, leaving stale `-draft` files and misleading statuses
- SOP-004 9C.2 states VRs should "close when parent document closes" but the CLI has no implementation
- Lead review of produced VR output identified specific quality issues that reduce readability and add unnecessary author burden
- Both themes affect the same qualified system (`qms-cli`), making a single CR the natural grouping

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `qms-cli/qms_config.py` | Modify | Add `attachment: True` to VR (1 line) |
| `qms-cli/commands/checkout.py` | Modify | Terminal state guard (3 lines) |
| `qms-cli/commands/close.py` | Modify | Attachment close, cascade close helper (~70 lines) |
| `qms-cli/seed/templates/TEMPLATE-VR.md` | Modify | Template v5 restructure |
| `qms-cli/interact_compiler.py` | Modify | Auto-metadata, block rendering, attribution, step numbering (~60 lines) |
| `qms-cli/tests/test_interact_compiler.py` | Modify | Update existing tests, add new test classes |
| `qms-cli/tests/test_attachment_lifecycle.py` | Create | Tests for checkout guard and cascade close |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| SDLC-QMS-RS | Modify | Add REQ-DOC-018, REQ-DOC-019, REQ-DOC-020, REQ-INT-023, REQ-INT-024, REQ-INT-025 |
| SDLC-QMS-RTM | Modify | Add entries for 6 new requirements |
| TEMPLATE-VR | Modify | Version 4 -> 5 (via seed template) |

### 7.3 Other Impacts

None. Changes are internal to qms-cli.

### 7.4 Development Controls

This CR implements changes to qms-cli, a controlled submodule. Development follows established controls:

1. **Test environment isolation:** Development in qms-cli submodule directory
2. **Branch isolation:** All development on branch `cr-095`
3. **Write protection:** `.claude/settings.local.json` blocks direct writes to `qms-cli/`
4. **Qualification required:** All new/modified requirements must have passing tests before merge
5. **CI verification:** Tests must pass on GitHub Actions for dev branch
6. **PR gate:** Changes merge to main only via PR after RS/RTM approval
7. **Submodule update:** Parent repo updates pointer only after PR merge

### 7.5 Qualified State Continuity

| Phase | main branch | RS/RTM Status | Qualified Release |
|-------|-------------|---------------|-------------------|
| Before CR | 2c61af2 | EFFECTIVE v17.0 / v21.0 | CLI-12.0 |
| During execution | Unchanged | DRAFT (checked out) | CLI-12.0 (unchanged) |
| Post-approval | Merged from cr-095 | EFFECTIVE v18.0 / v22.0 | CLI-13.0 |

---

## 8. Testing Summary

### Automated Verification

- New tests: checkout guard (terminal state rejection), attachment classification, cascade close logic, attachment close flexibility
- New tests: auto-metadata generation, block rendering, attribution placement, step subsection numbering, VR template v5 structure
- Updated tests: existing blockquote/attribution tests updated for new rendering behavior
- Full suite: `python -m pytest tests/ -v` — all tests pass

### Integration Verification

- Cascade close with checked-in VR: create CR -> create VR -> fill via interact -> checkin VR -> walk CR to CLOSED. Assert VR auto-closed, effective file contains compiled markdown.
- Cascade close with checked-out VR: create CR -> create VR -> fill via interact (don't checkin) -> walk CR to CLOSED. Assert VR auto-compiled from source, auto-closed.
- Direct VR close: `qms close` on a VR in IN_EXECUTION — should succeed.
- Checkout guard: attempt `qms checkout` on a CLOSED document — should be rejected.
- Template v5 compilation: `qms interact` + `qms checkin` on a test VR — verify subsection headings, no Signature/References, attribution below blockquotes, auto-generated date.

---

## 9. Implementation Plan

### 9.1 Phase 1: Pre-Execution Baseline

1. Commit and push pipe-dream to capture pre-execution state
2. Record commit hash in EI-1

### 9.2 Phase 2: Development

1. Create branch `cr-095` in qms-cli
2. Implement Theme A: attachment property, checkout guard, close flexibility, cascade close
3. Implement Theme B: TEMPLATE-VR v5, auto-metadata, block rendering, attribution placement, step numbering

### 9.3 Phase 3: Qualification

1. Write new tests for all changes
2. Update existing tests for new rendering behavior
3. Run full test suite, fix failures, iterate until all pass
4. Push to cr-095 branch
5. Verify GitHub Actions CI passes
6. Document qualified commit hash

### 9.4 Phase 4: Integration Verification

1. Exercise cascade close, checkout guard, direct VR close, and template compilation through CLI
2. Document observations

### 9.5 Phase 5: RS/RTM Update

1. Checkout SDLC-QMS-RS, add 6 new requirements, route to EFFECTIVE
2. Checkout SDLC-QMS-RTM, add entries for new requirements, route to EFFECTIVE

### 9.6 Phase 6: Merge and Submodule Update

1. Verify RS and RTM are EFFECTIVE
2. Merge cr-095 to main (`--no-ff`)
3. Update pipe-dream submodule pointer
4. Post-execution commit

---

## 10. Execution

| EI | Task Description | VR | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|----|-------------------|--------------|---------------------|
| EI-1 | Pre-execution commit (pipe-dream) | | Commit a56da86 captures pre-execution state | Pass | claude - 2026-02-22 |
| EI-2 | Create execution branch in qms-cli | | Branch cr-095 created from main (2c61af2) | Pass | claude - 2026-02-22 |
| EI-3 | Implement Theme A (attachment property, checkout guard, cascade close) | | `attachment: True` on VR in qms_config.py; 3-line terminal state guard in checkout.py; cascade close helper with auto-compile in close.py (~170 lines); attachment close flexibility (any non-terminal status) | Pass | claude - 2026-02-22 |
| EI-4 | Implement Theme B (TEMPLATE-VR v5, compiler refinements) | | TEMPLATE-VR v5 (removed date/performer/performed_date prompts, Signature/References sections, renamed to Prerequisites, stripped redundant labels, subsection headings); auto-metadata injection in interact_compiler.py; block rendering for all non-table responses; attribution below blockquotes; step subsection numbering (4.1, 4.2, etc.) | Pass | claude - 2026-02-22 |
| EI-5 | Write tests: checkout guard, cascade close, compiler changes; update existing tests | | 16 new tests in test_attachment_lifecycle.py (5 classification, 4 terminal state, 3 cascade logic, 2 close flexibility, 2 auto-compile); 14 new tests in test_interact_compiler.py (5 block rendering, 6 auto-metadata, 3 step subsection); updated 3 existing parser tests for v5 | Pass | claude - 2026-02-22 |
| EI-6 | Run full test suite, fix failures, iterate | Yes | 673/673 tests pass. Fixed: add_response timestamp patching pattern, version assertion 4→5 in parser tests, removed date/performer/performed_date from expected prompts, node count 14→11. See CR-095-VR-001 for integration verification. | Pass | claude - 2026-02-22 |
| EI-7 | Update RS: add REQ-DOC-018 through REQ-DOC-020, REQ-INT-023 through REQ-INT-025 | | Added 6 requirements to SDLC-QMS-RS: REQ-DOC-018 (attachment classification), REQ-DOC-019 (checkout guard), REQ-DOC-020 (cascade close), REQ-INT-023 (auto-metadata), REQ-INT-024 (block rendering), REQ-INT-025 (step subsections). Now EFFECTIVE v18.0. | Pass | claude - 2026-02-22 |
| EI-8 | Update RTM: add entries for 6 new requirements | | Added 6 traceability entries to SDLC-QMS-RTM with 30 test function references. Updated test counts (673 total). Qualified baseline: 31f8306. Now EFFECTIVE v22.0. | Pass | claude - 2026-02-22 |
| EI-9 | Route RS + RTM to EFFECTIVE | | RS reviewed + approved (v18.0 EFFECTIVE). RTM reviewed, corrected TBD baseline to 31f8306, re-reviewed + approved (v22.0 EFFECTIVE). | Pass | claude - 2026-02-22 |
| EI-10 | Merge to qms-cli main (`--no-ff`) | | Merged cr-095 → main with --no-ff. Merge commit: f0cd391. Pushed to remote. | Pass | claude - 2026-02-22 |
| EI-11 | Update pipe-dream submodule pointer | | qms-cli submodule updated: 2c61af2 → f0cd391 | Pass | claude - 2026-02-22 |
| EI-12 | Post-execution commit (pipe-dream) | | Commit 4bf56e4 captures RS v18.0, RTM v22.0, archives, audit trails, and updated submodule pointer | Pass | claude - 2026-02-22 |

---

### Execution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| Execution proceeded without variances. QA RTM review caught TBD baseline placeholder — corrected and re-reviewed before approval. | claude - 2026-02-22 |

---

## 11. Execution Summary

All 12 execution items completed successfully with no variances.

**Theme A (Attachment Lifecycle):** VR document type classified as attachment. Terminal state checkout guard prevents re-checkout of CLOSED/RETIRED documents. Cascade close automatically closes child attachments when parent closes, including auto-compilation of interactive attachments from source data. Attachments can be directly closed from any non-terminal status.

**Theme B (VR Template & Compiler):** TEMPLATE-VR v5 removes redundant prompts (date, performer, performed_date — now auto-generated), unnecessary sections (Signature, References), and redundant labels. Steps use subsection numbering (4.1, 4.2). Compiler auto-generates metadata from response timestamps/authors, block-renders all non-table responses with attribution below blockquotes.

**Qualification:** 673/673 tests pass on cr-095 branch (commit 31f8306). 30 new tests cover all 6 new requirements. SDLC-QMS-RS v18.0 and SDLC-QMS-RTM v22.0 both EFFECTIVE.

**Key commits:**
- Pre-execution: a56da86 (pipe-dream)
- Implementation: 31f8306 (qms-cli cr-095)
- Merge: f0cd391 (qms-cli main)
- Post-execution: 4bf56e4 (pipe-dream)

---

## 12. References

- **SOP-001:** Document Control
- **SOP-002:** Change Control
- **SOP-004:** Document Execution (Section 9C.2 — VR closure)
- **SOP-005:** Configuration Management
- **SOP-006:** SDLC Document Management
- **CR-094:** Interactive Compilation Defects (predecessor — identified VR output issues)

---

**END OF DOCUMENT**
