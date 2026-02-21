---
title: Interactive Compilation Defects
revision_summary: Initial draft
---

# CR-094: Interactive Compilation Defects

## 1. Purpose

Fix four defects in the interaction system's compilation engine discovered during CR-092-VR-001 authoring. The compiled markdown has duplicate frontmatter, broken table rows, overly broad guidance extraction, and no visual distinction between author content and template structure.

---

## 2. Scope

### 2.1 Context

CR-092-VR-001 was the first VR authored through the interaction system. Its compiled output revealed defects in the compilation engine and template parser that undermine readability and auditability.

- **Parent Document:** None (independent defect fix)

### 2.2 Changes Summary

Four defect fixes in the compilation engine, parser, and VR template:
1. Strip template preamble (frontmatter + notice) from compiled output
2. Context-aware attribution rendering (omit from tables, separate from bold/code)
3. Explicit guidance boundaries via `@end-prompt` tag
4. Visual distinction for author responses (blockquote wrapping)

### 2.3 Files Affected

- `qms-cli/interact_compiler.py` - Preamble stripping, context-aware rendering, blockquote wrapping
- `qms-cli/interact_parser.py` - `@end-prompt` tag recognition, bounded guidance extraction
- `qms-cli/seed/templates/TEMPLATE-VR.md` - Add `@end-prompt` tags, improve prompt guidance
- `qms-cli/tests/test_interact_compiler.py` - New and updated compilation tests
- `qms-cli/tests/test_interact_parser.py` - New `@end-prompt` and guidance boundary tests

---

## 3. Current State

The compilation engine (`interact_compiler.py`) produces output with four defects:
- D1: Template's own frontmatter and notice comment leak into compiled output (no preamble stripping)
- D2: Attribution `\n*-- author, ts*` injected into table cells breaks markdown table rows and bold markers in loops
- D3: Guidance extraction grabs everything between tags including document scaffold (headings, table headers, rules)
- D4: Author responses are visually indistinguishable from template structure

---

## 4. Proposed State

- D1: `compile_document()` strips template preamble before processing. Only the document's own frontmatter appears in output.
- D2: Table contexts receive value-only substitution (no attribution). Loop expansions place attribution outside bold markers and code fences.
- D3: `@end-prompt` tag explicitly marks where guidance ends. Parser respects this boundary. Backward-compatible fallback when absent.
- D4: Block-context responses (standalone `{{placeholder}}` lines) wrapped in blockquote (`> `). Label-context (`**Label:** {{placeholder}}`) rendered inline.

---

## 5. Change Description

### 5.1 Preamble Stripping (D1)

Add `_strip_template_preamble()` called at top of `compile_document()`:
- Find frontmatter blocks (pairs of `---` lines)
- If first block has no `{{` placeholders, it's the template's own frontmatter -- strip it along with any content before the second frontmatter block
- If only one frontmatter block exists, keep it as-is

### 5.2 Context-Aware Attribution (D2)

Refactor `_render_response()` into two functions:
- `_render_value_only(entries)` -- active value with amendment trail, NO attribution
- `_render_attribution(entries)` -- attribution line(s) only

Update `_substitute_line()`:
- Detect table rows (line starts with `|`)
- Table context: substitute value only, omit attribution
- Non-table context: value + attribution on separate line

Update `_expand_loops()`:
- `step_instructions`: `**{value}**` then attribution on next line
- `step_expected`: `**Expected:** {value}` then attribution on next line
- `step_actual`: value inside code fence, attribution AFTER closing fence
- `step_outcome`: `**Outcome:** {value}` then attribution on next line

### 5.3 Guidance Boundaries (D3)

Add `@end-prompt` tag to parser vocabulary. In guidance extraction, use `@end-prompt` position as boundary when present. Fallback to next-tag boundary when absent. Add `@end-prompt` after each prompt's guidance in TEMPLATE-VR.md.

### 5.4 Visual Distinction (D4)

For non-loop substitution (`_substitute_line()`):
- Block context (line is just `{{placeholder}}`): wrap response in blockquote (`> ` prefix)
- Label context (`**Label:** {{placeholder}}`): value inline after label, attribution below
- Table context: value only (from D2 fix)

---

## 6. Justification

- CR-092-VR-001 is the first production VR. Its compiled output is the primary auditable record.
- Broken table rows make the document structurally invalid markdown.
- Duplicate frontmatter confuses document parsers.
- Guidance leaking into compiled output exposes template internals to readers.
- Without visual distinction, reviewers cannot easily identify author-provided content.

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `interact_compiler.py` | Modify | Preamble stripping, context-aware rendering, blockquotes |
| `interact_parser.py` | Modify | `@end-prompt` tag recognition, bounded guidance |
| `seed/templates/TEMPLATE-VR.md` | Modify | Add `@end-prompt` tags, improve guidance |
| `tests/test_interact_compiler.py` | Modify | New and updated tests |
| `tests/test_interact_parser.py` | Modify | New `@end-prompt` tests |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| SDLC-QMS-RS | Modify | Add `@end-prompt` to REQ-INT-001 tag vocabulary |
| SDLC-QMS-RTM | Modify | New test entries, update qualified baseline |
| TEMPLATE-VR | Modify | Add `@end-prompt` tags (via code change in seed/) |

### 7.3 Other Impacts

None. Changes are internal to the compilation pipeline. No external interfaces affected.

### 7.4 Development Controls

This CR implements changes to qms-cli, a controlled submodule. Development follows established controls:

1. **Branch isolation:** All development on branch `cr-094`
2. **Qualification required:** All new/modified requirements must have passing tests before merge
3. **Merge gate:** RS and RTM must be EFFECTIVE before merge to main

### 7.5 Qualified State Continuity

| Phase | main branch | RS/RTM Status | Qualified Release |
|-------|-------------|---------------|-------------------|
| Before CR | c83dda0 | EFFECTIVE v16.0/v20.0 | CLI-11.0 |
| During execution | Unchanged | DRAFT (checked out) | CLI-11.0 (unchanged) |
| Post-approval | Merged from cr-094 | EFFECTIVE v17.0/v21.0 | CLI-12.0 |

---

## 8. Testing Summary

<!--
NOTE: Do NOT delete this comment. It provides guidance during document authoring.

For code CRs, address both categories per SOP-002 Section 6.8:
1. Automated verification: unit tests, qualification tests, CI
2. Integration verification: what will be exercised through user-facing levers
   in a running system to demonstrate the change is effective

For document-only CRs, a description of procedural verification is sufficient.
Delete the subsections below and use a simple list.
-->

### Automated Verification

- Frontmatter: template FM removed, document FM kept, single FM preserved, notice stripped
- Tables: rows are valid single-line markdown, no attribution in cells
- Loops: bold not broken by attribution, attribution outside code fences
- `@end-prompt`: guidance stops at closing tag, fallback without closing tag, tag stripped from output
- Blockquotes: block-context responses wrapped, label-context not wrapped
- Integration: CR-092-VR-001 source data compiles cleanly against updated template

### Integration Verification

- Recompile CR-092-VR-001 via `qms interact --compile` and verify:
  - Exactly one frontmatter block
  - Valid table rows with no attribution in cells
  - Free-text responses in blockquotes
  - Step attributions on separate lines, bold markers intact
  - Attribution outside code fences
- Run `qms interact` display to verify guidance boundaries are clean

---

## 9. Implementation Plan

### 9.1 Phase 1: Pre-Execution Baseline

1. Commit and push pipe-dream to capture baseline state
2. Record commit hash

### 9.2 Phase 2: Branch Setup

1. Create branch `cr-094` in qms-cli from main

### 9.3 Phase 3: Implementation

1. Strip template preamble (D1) in `interact_compiler.py`
2. Context-aware attribution rendering (D2) in `interact_compiler.py`
3. `@end-prompt` tag support (D3) in `interact_parser.py` and `TEMPLATE-VR.md`
4. Blockquote wrapping (D4) in `interact_compiler.py`

### 9.4 Phase 4: Qualification

1. Write new tests for all four defect fixes
2. Update existing tests whose assertions break
3. Run full test suite -- all must pass
4. Record qualified commit hash

### 9.5 Phase 5: Integration Verification

1. Recompile CR-092-VR-001 against updated template
2. Verify all six acceptance criteria from Section 8

### 9.6 Phase 6: RS/RTM Update and Approval

1. Update SDLC-QMS-RS: add `@end-prompt` to REQ-INT-001 tag vocabulary
2. Update SDLC-QMS-RTM: new test entries, update qualified baseline commit hash
3. Route RS and RTM through review/approval to EFFECTIVE

### 9.7 Phase 7: Merge and Submodule Update

1. Verify RS and RTM are EFFECTIVE
2. Merge cr-094 to main via `git merge --no-ff`
3. Verify qualified commit reachable from main
4. Update pipe-dream submodule pointer
5. Commit pipe-dream

### 9.8 Phase 8: Post-Execution

1. Commit and push pipe-dream with all execution evidence
2. Record commit hash

---

## 10. Execution

| EI | Task Description | VR | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|----|-------------------|--------------|---------------------|
| EI-1 | Pre-execution baseline commit | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | Create execution branch cr-094 in qms-cli | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Strip template preamble (D1) | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-4 | Context-aware attribution rendering (D2) | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-5 | Explicit guidance boundaries via @end-prompt (D3) | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-6 | Visual distinction for author responses (D4) | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-7 | Write tests | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-8 | Run full test suite, record qualified commit | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-9 | Update RS and RTM, route to EFFECTIVE | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-10 | Merge cr-094 to qms-cli main | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-11 | Update pipe-dream submodule pointer | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-12 | Recompile CR-092-VR-001 | Yes | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-13 | Post-execution commit | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Add rows as needed. When adding rows, fill columns 3-5 during execution.
-->

---

### Execution Comments

| Comment | Performed By - Date |
|---------|---------------------|

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Record observations, decisions, or issues encountered during execution.
Add rows as needed.

This section is the appropriate place to attach VARs that do not apply
to any individual execution item, but apply to the CR as a whole.
-->

---

## 11. Execution Summary

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Complete this section after all EIs are executed.
Summarize the overall outcome and any deviations from the plan.
-->

[EXECUTION_SUMMARY]

---

## 12. References

- **SOP-001:** Document Control
- **SOP-002:** Change Control
- **SOP-004:** Document Execution
- **SOP-005:** Software Development Lifecycle
- **SOP-006:** Specification Management
- **CR-091:** Interaction System Engine (introduced the compilation engine)
- **CR-092:** Corrective action for CR-091 code propagation
- **CR-092-VR-001:** VR that revealed these defects

---

**END OF DOCUMENT**
