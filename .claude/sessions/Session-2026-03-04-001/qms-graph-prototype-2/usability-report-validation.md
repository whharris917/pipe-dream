# Usability Report: Validation, Diff, and Template Enforcement

**Tester:** Fresh agent (no prior exposure to the system)
**Date:** 2026-03-05
**System:** QMS Graph Engine Prototype 2
**Scope:** Template enforcement, validation errors, diff/compliance checking, locking mechanism

---

## Executive Summary

The validation and diff system is functional and produces clear, useful output. The diff mechanism correctly detects missing nodes, added nodes, and schema modifications. Validation catches required field omissions, enum constraint violations, and type mismatches. The locking mechanism correctly distinguishes template nodes from fill nodes at instantiation time.

However, there are several enforcement gaps: `locked` is metadata-only with no runtime enforcement, extra response fields are silently accepted, completed documents accept further responses, and the diff `valid` flag ignores added nodes. These are design decisions that may be intentional (audit-over-enforcement philosophy), but they represent real compliance risks if not documented.

---

## Test Results

### 1. Graph.validate() -- Structural Validation

**What it checks:**
- Entry point exists and is a valid node
- All edge targets reference existing nodes
- All nodes are reachable from entry point

**Tests performed:**
| Test | Input | Result | Verdict |
|------|-------|--------|---------|
| Fresh document | Unmodified DIAG-DIFF-001 | 0 errors | PASS |
| Removed node | Deleted `diagnostic.hypothesize` | Detected dangling edge + 5 unreachable nodes | PASS |
| Added dangling edge | Edge to `diagnostic.nonexistent` | "Edge from 'diagnostic.start' to unknown 'diagnostic.nonexistent'" | PASS |
| Template validation | `python engine.py validate templates.diagnostic` | `valid: true, nodes: 7` | PASS |

**Error message quality:** Clear and specific. Each error names the exact node and the nature of the problem. The unreachability check is particularly valuable -- removing one node cascades to show all downstream nodes that become orphaned.

**Gap:** The `validate` CLI command only works on templates (builds from class), not on document files. There is no `validate` subcommand for `.json` documents -- you must load the document in Python and call `graph.validate()` manually. The engine does validate at `start` time (exits with errors if invalid), but there is no way to re-validate a document that has been modified after creation.

---

### 2. Graph.diff() -- Template Compliance Checking

**What it checks:**
- Missing nodes (in template but not in document)
- Added nodes (in document but not in template)
- Modified nodes (schema or edge count differs)

**Tests performed:**
| Test | Input | Result | Verdict |
|------|-------|--------|---------|
| Identical | Fresh doc vs. its template | `missing: [], added: [], modified: []` | PASS |
| Missing node | Removed `hypothesize` | `missing: ["diagnostic.hypothesize"]` | PASS |
| Added node | Injected `diagnostic.extra` | `added: ["diagnostic.extra"]` | PASS |
| Modified schema | Added field to locked node | `modified: [["diagnostic.start", ["evidence_schema"]]]` | PASS |
| Fill nodes | Document with fills vs. base template | `added: ["diagnostic.custom_analysis", "diagnostic.custom_review"]` | PASS |
| Cross-template | Incident doc vs. diagnostic template | All 7 diagnostic nodes missing, all 9 incident nodes added | PASS |

**Diff output quality:** The output is structured JSON, easy to parse programmatically. The three categories (missing/added/modified) are intuitive and immediately actionable.

**Gap 1 -- `valid` flag semantics:** The `valid` flag in the CLI diff output is defined as `len(result["missing"]) == 0`. This means a document with unauthorized added nodes is still reported as `valid: true`. This is surprising -- one would expect that any deviation from the template (missing OR added) would flag non-compliance. At minimum, this should be split into `template_complete: true` and `template_only: false` or similar.

**Gap 2 -- No prompt/context comparison:** The diff compares evidence_schema keys and edge counts, but does not compare node prompts, context text, performer assignments, terminal flags, or gate conditions. A locked node whose prompt was changed from "Begin this procedure" to "Skip everything" would not appear in the `modified` list.

**Gap 3 -- Edge comparison is count-only:** The diff checks `len(dn.edges) != len(tn.edges)` but does not compare edge targets or conditions. An edge redirected from `diagnostic.observe` to `diagnostic.close` would not be detected if the count stays the same.

---

### 3. Response Validation

**What it checks:**
- Required fields present
- Enum values within allowed set
- Integer type enforcement

**Tests performed:**
| Test | Input | Result | Verdict |
|------|-------|--------|---------|
| Empty response | `{}` | "Missing required field 'objective'" + "Missing required field 'ready'" | PASS |
| Bad enum | `ready: "maybe"` | "Field 'ready': 'maybe' not in ['yes', 'no']" | PASS |
| Valid response | `objective: "test", ready: "yes"` | Accepted, cursor advanced | PASS |
| String for integer | `count: "five"` | "Field 'count': expected int, got str" | PASS |
| Extra fields | Valid fields + `bogus: "x"` | Silently accepted | PASS (but see gap) |
| Wrong step fields | Hypothesis fields at start step | Rejected (missing start's required fields) | PASS |

**Error message quality:** Very good. Messages name the exact field, the submitted value, and the expected constraint. The `stopped_reason: "validation_error"` key is clear. The response also re-includes the full node status, which is helpful for the agent to self-correct.

**Gap 1 -- Extra fields accepted silently:** Any field not in the evidence_schema is recorded without warning. This means typos in field names go undetected (e.g., `symtpoms` instead of `symptoms` would be recorded, and the required `symptoms` would still be flagged as missing -- but if the field is optional, the typo would silently create garbage data).

**Gap 2 -- No `text` type validation:** The `text` type accepts any value, including integers, booleans, lists, or nested objects. There is no string type enforcement.

**Gap 3 -- No `bool` type validation:** The `bool` field type is referenced in `auto_run()` defaults but not validated in `validate_response()`. A bool field would accept any value.

---

### 4. Node Locking Mechanism

**What it does:**
- `instantiate()` sets `locked: true` on all template nodes
- Fill nodes (from `fills=` parameter) remain `locked: false`
- `freeze()` sets `locked: true` on ALL nodes (including fills)
- The `[locked]` annotation appears in the `map` output

**Tests performed:**
| Test | Result | Verdict |
|------|--------|---------|
| Fresh instantiation: all template nodes locked | 7/7 locked | PASS |
| Fill nodes unlocked at instantiation | `custom_analysis` and `custom_review` unlocked | PASS |
| freeze() locks everything | All 8 nodes locked after freeze | PASS |
| Map shows lock status | `[locked]` annotation on locked nodes, absent on fills | PASS |

**Critical Gap -- Locking is NOT enforced at runtime.** The `locked` attribute is purely informational. The engine does not check `node.locked` anywhere during `do_respond()`. A locked node can be responded to, its response is recorded, and the cursor advances. There is no code path that prevents mutation of a locked node's content.

This means `locked` serves only two purposes:
1. Visual annotation in the map view
2. Diff baseline (template nodes vs. fill nodes)

If the intent is to prevent structural modification of template nodes, enforcement must be added either at the JSON editing layer or in the engine itself.

---

### 5. Completed Document Handling

**Critical Gap:** The engine allows responding to a completed document. After all 7 steps of DIAG-VAL-001 were completed (state: "complete"), submitting another response was accepted. The history grew from 7 to 8 entries, and the terminal node recorded a duplicate response.

The `do_respond()` function does not check `ticket.state == "complete"` before processing. The only "protection" is that after recording the response on the terminal node, it sets state to "complete" again -- but the response is already recorded.

**Expected behavior:** `do_respond()` should return an error like `{"error": "Document is already complete"}` when `ticket.state != "active"`.

---

### 6. Cross-Template Diffing

The cross-template diff (incident doc vs. diagnostic template) works mechanically but produces output that is not very useful. Because node IDs are prefixed with the template ID (`incident.start` vs `diagnostic.start`), there is zero overlap between them. The diff shows ALL diagnostic nodes as missing and ALL incident nodes as added, even though the incident template inherits from diagnostic and shares the same logical structure (observe, hypothesize, test, conclude).

**Suggestion:** For cross-template comparison to be meaningful, the diff would need a mode that compares node suffixes (ignoring the template prefix) or compares based on structural shape rather than exact IDs.

---

## Summary of Gaps

| # | Gap | Severity | Category |
|---|-----|----------|----------|
| 1 | `locked` is not enforced at runtime | High | Enforcement |
| 2 | Completed documents accept further responses | High | Enforcement |
| 3 | Extra response fields accepted silently | Medium | Validation |
| 4 | Diff `valid` flag ignores added nodes | Medium | Compliance |
| 5 | Diff does not compare prompts, context, performer, terminal, gate | Medium | Compliance |
| 6 | Diff edge comparison is count-only, not target-aware | Medium | Compliance |
| 7 | No `validate` CLI command for document files | Low | Usability |
| 8 | No `bool` type validation | Low | Validation |
| 9 | No `text` type enforcement (accepts any JSON type) | Low | Validation |
| 10 | Cross-template diff is prefix-bound, not structure-aware | Low | Design |

---

## Suggestions for Improvement

### High Priority

1. **Guard completed documents.** Add to `do_respond()`:
   ```python
   if ticket.state != "active":
       return {"error": f"Document is in '{ticket.state}' state, cannot accept responses"}
   ```

2. **Enforce locking (optional).** If locking should prevent structural modification, add a check in the diff that returns errors (not just annotations) for any modifications to locked nodes. Alternatively, if locking is meant to be audit-only, document this clearly in the Template docstring.

### Medium Priority

3. **Warn on extra fields.** Add a "warnings" key to validation output for fields present in the response but not in the schema:
   ```python
   warnings = [f"Unknown field '{k}'" for k in response if k not in schema]
   ```

4. **Expand diff comparison.** Compare full node properties (prompt, context, performer, terminal, gate) and edge targets, not just schema keys and edge counts.

5. **Split diff validity.** Replace single `valid` with `template_complete` (all template nodes present) and `template_strict` (no additions or modifications).

### Low Priority

6. **Add `validate` for documents.** `python engine.py validate .documents/DOC.json` should load and validate the serialized graph.

7. **Add `bool` validation.** Check `isinstance(val, bool)` for bool-typed fields.

8. **Tighten `text` validation.** Require `isinstance(val, str)` for text-typed fields.

---

## Overall Assessment

The system is well-designed for its prototype stage. The validation error messages are clear and actionable -- an AI agent receiving them would immediately know what to fix. The diff output is structured and useful for compliance checking. The locking/fill distinction at instantiation time is clean and intuitive.

The main philosophical question is whether the system should be **audit-oriented** (detect and report violations after the fact) or **enforcement-oriented** (prevent violations at the point of action). Currently it is firmly in the audit camp, which is fine as long as that is intentional and documented. The two high-severity gaps (completed document responses and lack of lock enforcement) should be addressed either by adding enforcement or by explicitly documenting them as design decisions with compensating audit controls.

The map rendering (`--no-color` flag) is useful for quick visual inspection. The `[locked]` annotations and `>>>` cursor marker make document state immediately readable.

**Verdict:** Ready for real use with the two high-priority fixes applied. The diff and validation infrastructure provides a solid foundation for template compliance checking.
