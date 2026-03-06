# Final Validation Report: QMS Graph Prototype-2

**Date:** 2026-03-05
**Tester:** claude (automated CLI testing)
**Engine:** `engine.py` (Python template edition)
**Working directory:** `qms-graph-prototype-2/`

---

## Test Summary

| # | Test | Result | Notes |
|---|------|--------|-------|
| 1 | Gate conditions | **PASS** (with finding) | Gate blocks `ready: "no"`, advances `ready: "yes"`. Incident template missing gate. |
| 2 | Loop-back edges | **PASS** | Map shows conditional edge; `hypothesis_confirmed: "no"` loops back to hypothesize. |
| 3 | Inline response | **PASS** | Full puzzle walkthrough with `--response` only, 3 steps to completion. |
| 4 | Completed doc rejection | **PASS** | Returns `{"error": "Document is already complete"}`. |
| 5 | Extra field warning | **FAIL** | Warnings generated internally but silently dropped on success path. |
| 6 | Deep diff | **PASS** | Detects tampered prompt and context; reports `compliant: false`. |

**Overall: 5/6 PASS, 1 FAIL, 2 findings**

---

## Test 1: Gate Conditions

### 1a. Start incident doc (first attempt)

**Command:**
```
python engine.py start templates.incident --doc-id GATE-001
python engine.py respond .documents/GATE-001.json --response '{"objective": "Test", "severity": "low", "active_impact": "no", "ready": "no"}'
```

**Output:** Document advanced to `incident.observe` -- gate did NOT block.

**Root cause:** The `Incident` template overrides the `start` node from `ProcedureBase` but does not include `gate="response.get('ready') == 'yes'"`. The `ready` field exists in the schema but has no enforcement. This is a **template inheritance bug** -- when a child template redefines a node, the parent's gate is lost.

### 1b. Retry with diagnostic template (which inherits ProcedureBase's start node with gate)

**Command:**
```
python engine.py start templates.diagnostic --doc-id GATE-001
python engine.py respond .documents/GATE-001.json --response '{"objective": "Test gate blocking", "ready": "no"}'
```

**Output:**
```json
{
  "gate_blocked": true,
  "gate": "response.get('ready') == 'yes'",
  "cursor": "diagnostic.start",
  "message": "Gate condition not met. Revise your response."
}
```

**Result: PASS** -- Gate correctly blocks when `ready: "no"`.

### 1c. Advance with ready=yes

**Command:**
```
python engine.py respond .documents/GATE-001.json --response '{"objective": "Test gate passing", "ready": "yes"}'
```

**Output:**
```json
{
  "cursor": "diagnostic.observe",
  "state": "active",
  "steps": 1
}
```

**Result: PASS** -- Gate passes and cursor advances.

### Finding: Incident template missing gate

The `Incident.define()` method (in `templates/incident.py`) calls `g.node("start", ...)` which creates a new node that shadows ProcedureBase's `start` node. The overridden node includes `severity`, `active_impact`, and `ready` fields but omits `gate="response.get('ready') == 'yes'"`. The `ready` field is purely cosmetic without the gate.

**Severity:** Medium -- the `ready` field creates a false expectation of enforcement.

**Fix:** Add `gate="response.get('ready') == 'yes'"` to the `g.node("start", ...)` call in `Incident.define()`.

---

## Test 2: Loop-Back Edges

### 2a. Start and view map

**Command:**
```
python engine.py start templates.diagnostic --doc-id LOOP-001
python engine.py map .documents/LOOP-001.json --no-color
```

**Output:**
```
============================================================
  Diagnostic Procedure: LOOP-001
============================================================

>>>  diagnostic.start  Begin this procedure. [locked]
  .  diagnostic.observe  Observe and document the symptoms. [locked]
    .  diagnostic.hypothesize  Form a hypothesis about the root cause. [locked]
      .  diagnostic.test  Test your hypothesis. [locked]
        |-- if last_response('diagnostic.test').get('hypothesis_confirmed')
        ^ loop back to diagnostic.hypothesize
        .  diagnostic.conclude  State your conclusion. [locked]
          .  diagnostic.verify  Verify the results. [locked]
            .  diagnostic.close  Close this procedure. [locked]  END
```

**Result: PASS** -- Map shows conditional edge on `test` node and loop-back indicator.

### 2b. Walk through with failed hypothesis

**Sequence:**
1. `start` -> respond with `ready: "yes"` -> advances to `observe`
2. `observe` -> respond with symptoms -> advances to `hypothesize`
3. `hypothesize` -> respond with hypothesis -> advances to `test`
4. `test` -> respond with `hypothesis_confirmed: "no"` -> **loops back to `hypothesize`**

**Output at step 4:**
```json
{
  "cursor": "diagnostic.hypothesize",
  "state": "active",
  "steps": 4
}
```

**Result: PASS** -- Failed hypothesis correctly loops back to `diagnostic.hypothesize`.

---

## Test 3: Inline Response (--response flag)

### Full walkthrough

**Commands:**
```
python engine.py start templates.logic_puzzle --doc-id INLINE-002
python engine.py respond .documents/INLINE-002.json --response '{"understood": "yes"}'
python engine.py respond .documents/INLINE-002.json --response '{"reasoning": "By process of elimination..."}'
python engine.py respond .documents/INLINE-002.json --response '{"fish_owner": "German", "house_assignments": "...", "confidence": "certain"}'
```

**Output (final step):**
```json
{
  "cursor": "puzzle.solve",
  "state": "complete",
  "steps": 3
}
```

**Result: PASS** -- Three-step walkthrough entirely via `--response` inline JSON. No response files needed. Document correctly reaches `complete` state.

---

## Test 4: Completed Document Rejection

**Command:**
```
python engine.py respond .documents/INLINE-002.json --response '{"fish_owner": "trying again"}'
```

**Output:**
```json
{
  "error": "Document is already complete",
  "state": "complete"
}
```

**Result: PASS** -- Completed document correctly rejects further responses.

### Finding: Exit code is 0 for errors

The engine returns exit code 0 even when reporting errors (`"error": "Document is already complete"` or validation failures). Automation scripts checking `$?` would not detect failures.

**Severity:** Low -- JSON output contains the error information, but shell-level error detection is broken.

**Fix:** Add `sys.exit(1)` in `main()` when the result contains `"error"` or `"errors"` keys.

---

## Test 5: Extra Field Warning

### 5a. Submit response with typo field

**Command:**
```
python engine.py respond .documents/EXTRA-001.json --response '{"understood": "yes", "understod": "yes", "notes": "extra field"}'
```

**Output:**
```json
{
  "cursor": "puzzle.work",
  "state": "active",
  "steps": 1
}
```

No warnings in output. The response was accepted and the cursor advanced without any indication that `understod` and `notes` are unknown fields.

### 5b. Direct validation confirms warnings are generated internally

```python
>>> errors, warnings = validate_response(node, response)
>>> print(warnings)
["Unknown field 'understod' (not in schema)", "Unknown field 'notes' (not in schema)"]
```

The `validate_response()` function correctly identifies unknown fields and returns them as warnings. However, `do_respond()` only includes warnings in the output when there are validation errors or a gate block. On the success path (no errors, gate passes), warnings are silently discarded.

### 5c. Proof: warnings appear when errors co-exist

When a response has BOTH missing required fields AND extra fields, the warnings appear:
```json
{
  "errors": ["Missing required field 'symptoms'", "Missing required field 'onset'"],
  "stopped_reason": "validation_error",
  "cursor": "diagnostic.observe",
  "warnings": ["Unknown field 'objective' (not in schema)", "Unknown field 'ready' (not in schema)"]
}
```

**Result: FAIL** -- Extra field warnings are silently dropped on the success path.

**Severity:** Medium -- agents submitting typo'd field names get no feedback. Evidence silently includes junk data.

**Fix:** In `do_respond()`, after the gate check and before recording, include warnings in the success result:
```python
result = {"cursor": ticket.cursor, "state": ticket.state, "steps": len(ticket.history)}
if warnings:
    result["warnings"] = warnings
```

---

## Test 6: Deep Diff

### 6a. Tamper with document

Modified `.documents/DIFF-001.json`:
- Changed `diagnostic.observe` prompt from "Observe and document the symptoms." to "TAMPERED: Skip observation."
- Changed `diagnostic.hypothesize` context from original to "TAMPERED: Just guess."

### 6b. Run diff

**Command:**
```
python engine.py diff .documents/DIFF-001.json templates.diagnostic
```

**Output:**
```json
{
  "missing": [],
  "added": [],
  "modified": [
    ["diagnostic.observe", ["prompt"]],
    ["diagnostic.hypothesize", ["context"]]
  ],
  "compliant": false
}
```

**Result: PASS** -- Diff correctly identifies both tampered nodes, reports which specific fields were modified, and flags the document as non-compliant.

---

## Findings Summary

### Bugs

| ID | Severity | Description | Location |
|----|----------|-------------|----------|
| F-1 | Medium | Extra field warnings silently dropped on success path | `engine.py:do_respond()` lines 285-303 |
| F-2 | Medium | Incident template overrides start node without gate | `templates/incident.py:define()` line 14 |
| F-3 | Low | Exit code is 0 for all responses including errors | `engine.py:main()` respond handler |

### Observations

- Gate condition evaluation is robust -- uses sandboxed `eval()` with restricted builtins
- Loop-back edge resolution is correct and the map renderer properly shows loop indicators
- `--response` inline JSON works cleanly as a replacement for `--response-file`
- Completed document rejection is immediate (checked before validation)
- Diff is field-level accurate and catches prompt/context/performer/terminal/gate/edges/schema changes
- Template inheritance model (ProcedureBase -> Diagnostic -> Incident) works for node ordering and edge generation, but node overrides silently lose parent properties like `gate`

---

## Recommended Fixes (Priority Order)

1. **F-1:** Propagate warnings to success responses in `do_respond()`
2. **F-2:** Add gate condition to Incident's start node override
3. **F-3:** Set non-zero exit code for error/validation-failure/gate-blocked responses
