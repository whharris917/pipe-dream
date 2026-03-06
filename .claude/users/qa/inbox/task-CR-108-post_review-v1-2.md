---
task_id: task-CR-108-post_review-v1-2
task_type: REVIEW
workflow_type: POST_REVIEW
doc_id: CR-108
title: DocuBuilder Genesis Sandbox
status: IN_POST_REVIEW
responsible_user: claude
assigned_by: claude
assigned_date: 2026-03-06
version: 1.2
---

# REVIEW REQUEST: CR-108

**Workflow:** POST_REVIEW
**Version:** 1.2
**Assigned By:** claude
**Date:** 2026-03-06

---

## MANDATORY VERIFICATION CHECKLIST

**YOU MUST verify each item below. ANY failure = REJECT.**

Before submitting your review, complete this checklist:

### Frontmatter

| Item | Status | Evidence |
|------|--------|----------|
| `title:` field present and non-empty | PASS / FAIL | (quote actual value) |
| `revision_summary:` present (required for v1.0+) | PASS / FAIL | (quote actual value or N/A) |
| `revision_summary:` begins with CR ID (e.g., "CR-XXX:") | PASS / FAIL | (quote CR ID or N/A) |

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

### Execution Compliance

| Item | Status | Evidence |
|------|--------|----------|
| All execution items (EIs) have Pass/Fail outcomes | PASS / FAIL |  |
| Each EI execution summary addresses ALL items in its task description | PASS / FAIL | (For each EI, list task description items and confirm each is addressed in the execution summary) |
| All EIs have performer and date | PASS / FAIL |  |
| VARs attached for any failed EIs | PASS / FAIL |  |

---

## STRUCTURED REVIEW RESPONSE FORMAT

Your review comment MUST follow this format:

```
## qa Review: CR-108

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
- **EXECUTION VERIFICATION IS CRITICAL**: All EIs must have outcomes
- Missing EI data = incomplete execution = REJECT

**There is no "approve with comments." There is no severity classification.**
**If ANY deficiency exists, the only valid outcome is REQUEST UPDATES.**

---

## Commands

Submit your review:

**If ALL items PASS:**
```
/qms --user qa review CR-108 --recommend --comment "[your structured review]"
```

**If ANY item FAILS:**
```
/qms --user qa review CR-108 --request-updates --comment "[your structured review with findings]"
```
