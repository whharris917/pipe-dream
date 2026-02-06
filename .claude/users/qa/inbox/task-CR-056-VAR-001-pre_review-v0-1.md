---
task_id: task-CR-056-VAR-001-pre_review-v0-1
task_type: REVIEW
workflow_type: PRE_REVIEW
doc_id: CR-056-VAR-001
title: MCP Auto-Connect Reliability Blocks Multi-Agent Testing
status: IN_PRE_REVIEW
responsible_user: claude
assigned_by: claude
assigned_date: 2026-02-05
version: 0.1
---

# REVIEW REQUEST: CR-056-VAR-001

**Workflow:** PRE_REVIEW
**Version:** 0.1
**Assigned By:** claude
**Date:** 2026-02-05

---

## MANDATORY VERIFICATION CHECKLIST

**YOU MUST verify each item below. ANY failure = REJECT.**

Before submitting your review, complete this checklist:

### Frontmatter

| Item | Status | Evidence |
|------|--------|----------|
| `title:` field present and non-empty | PASS / FAIL | (quote actual value) |
| `revision_summary:` present and descriptive (required for v1.0+) | PASS / FAIL | (quote actual value or N/A) |

### Document Structure

| Item | Status | Evidence |
|------|--------|----------|
| Document follows type-specific template | PASS / FAIL |  |
| All required sections present | PASS / FAIL |  |
| Section numbering sequential and correct | PASS / FAIL |  |

### Content Integrity

| Item | Status | Evidence |
|------|--------|----------|
| No placeholder text (TBD, TODO, XXX, FIXME) | PASS / FAIL |  |
| No obvious factual errors or contradictions | PASS / FAIL |  |
| References to other documents are valid | PASS / FAIL |  |
| No typos or grammatical errors | PASS / FAIL |  |
| Formatting consistent throughout | PASS / FAIL |  |

---

## STRUCTURED REVIEW RESPONSE FORMAT

Your review comment MUST follow this format:

```
## qa Review: CR-056-VAR-001

### Checklist Verification

[Complete checklist table with PASS/FAIL and evidence]

### Findings

[List ALL findings. Every finding is a deficiency.]

1. [Finding or "No findings"]

### Recommendation

[RECOMMEND / REQUEST UPDATES] - [Brief rationale]
```

---

## CRITICAL REMINDERS

- **Compliance is BINARY**: Document is either compliant or non-compliant
- **ONE FAILED ITEM = REJECT**: No exceptions, no "minor issues"
- **VERIFY WITH EVIDENCE**: Quote actual values, do not assume
- **REJECTION IS CORRECT**: A rejected document prevents nonconformance

**There is no "approve with comments." There is no severity classification.**
**If ANY deficiency exists, the only valid outcome is REQUEST UPDATES.**

---

## Commands

Submit your review:

**If ALL items PASS:**
```
/qms --user qa review CR-056-VAR-001 --recommend --comment "[your structured review]"
```

**If ANY item FAILS:**
```
/qms --user qa review CR-056-VAR-001 --request-updates --comment "[your structured review with findings]"
```
