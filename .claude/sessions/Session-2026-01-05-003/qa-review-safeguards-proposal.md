# CAPA-002 Proposals: Strengthening QA Review Safeguards

## Context

INV-002 identified that SOP-005 was approved without the required `revision_summary` field. Root cause analysis revealed:
- No systematic verification of frontmatter requirements
- Review criteria too vague ("Document follows SOP format conventions")
- No automated validation before approval

This document proposes concrete mechanisms to prevent similar oversights.

---

## Foundational Principle: Binary Compliance

**GMP review is not a judgment call. It is a binary determination.**

A document is either:
- **COMPLIANT**: Meets 100% of requirements. Approve.
- **NON-COMPLIANT**: Fails any requirement. Reject.

There is no middle ground. There is no "approve with comments." There is no "minor finding we can overlook." There is no severity classification that permits leniency.

A missing comma is grounds for rejection.
A typo is grounds for rejection.
A formatting inconsistency is grounds for rejection.

The initiator corrects the deficiency and resubmits. This is not punitive—it is the process working correctly. Rejection is the mechanism by which quality is enforced.

**Any framework that introduces severity levels, conditional approvals, or "justified exceptions" undermines the integrity of the QMS and must be rejected.**

---

## Proposal 1: Mandatory Pre-Review Checklist

### Concept

Embed a **non-negotiable checklist** directly into the QA agent's review prompt. QA must explicitly verify each item. Any FAIL = REJECT.

### Proposed Checklist (Document Review)

```
MANDATORY VERIFICATION CHECKLIST
================================
QA MUST verify each item. ANY failure = REJECT.

[ ] FRONTMATTER COMPLETENESS
    [ ] `title:` field present and non-empty
    [ ] `revision_summary:` field present and non-empty
    [ ] revision_summary begins with authorizing CR ID (e.g., "CR-XXX: ...")

[ ] DOCUMENT STRUCTURE
    [ ] Document follows type-specific template (SOP, CR, INV, TP, etc.)
    [ ] All required sections present per document type
    [ ] Section numbering is sequential and correct

[ ] TRACEABILITY
    [ ] Authorizing CR exists and is in correct state
    [ ] Document ID matches CR execution item
    [ ] Version number is appropriate for document state

[ ] CONTENT INTEGRITY
    [ ] No placeholder text (TBD, TODO, XXX, FIXME, etc.)
    [ ] No obvious factual errors or contradictions
    [ ] References to other documents are valid and correct
    [ ] No typos or grammatical errors
    [ ] Formatting is consistent throughout

ONE UNCHECKED BOX = REJECT. NO EXCEPTIONS.
```

### Implementation Options

1. **QA Agent System Prompt**: Add checklist to QA's base instructions
2. **Review Routing Prompt**: Inject checklist when `route --review` is called
3. **SOP-001 Appendix**: Add as normative appendix to Document Control SOP

---

## Proposal 2: Structured Review Response Format

### Concept

Require QA to produce reviews in a structured format that forces explicit checklist verification with binary outcomes.

### Proposed Review Format

```markdown
## QA Review: {DOC_ID}

### Checklist Verification

| Item | Status | Evidence |
|------|--------|----------|
| Frontmatter: title present | PASS/FAIL | [quote value or state "MISSING"] |
| Frontmatter: revision_summary present | PASS/FAIL | [quote value or state "MISSING"] |
| Frontmatter: CR ID in revision_summary | PASS/FAIL | [quote CR ID or state "MISSING"] |
| Template compliance | PASS/FAIL | [note any deviation] |
| Required sections present | PASS/FAIL | [list missing sections if any] |
| No placeholder content | PASS/FAIL | [quote any found] |
| Traceability verified | PASS/FAIL | [confirm CR state] |
| No typos/errors | PASS/FAIL | [list any found] |
| Formatting consistent | PASS/FAIL | [note any inconsistency] |

### Findings

[List ALL findings. Every finding is a deficiency. There is no "minor" or "major" distinction.]

1. [Finding]
2. [Finding]
...

### Recommendation

[ ] APPROVE - All checklist items PASS, zero findings
[ ] REJECT - One or more FAIL items or findings present

**If ANY finding exists, the only valid recommendation is REJECT.**
```

### Key Requirement

QA must provide **evidence** for each checklist item—quoting the actual values observed, not just marking PASS/FAIL. This forces verification rather than assumption.

---

## Proposal 3: Review Prompt Injection

### Concept

Modify the `qms.py route --review` and `route --approval` commands to inject mandatory reminder text.

### Proposed Injection Points

**When routing for review:**
```
═══════════════════════════════════════════════════════════════
REVIEW ASSIGNMENT: {DOC_ID}
═══════════════════════════════════════════════════════════════

MANDATORY VERIFICATION REQUIRED:

1. Read the frontmatter YAML block completely
2. Verify `title:` field exists and is non-empty
3. Verify `revision_summary:` field exists and is non-empty
4. Verify revision_summary begins with "CR-XXX:"
5. Check entire document for placeholder text (TBD, TODO, etc.)
6. Verify document follows type-specific template
7. Check for typos, formatting errors, inconsistencies

ANY DEFICIENCY = REJECT

Do not approve documents with missing fields.
Do not approve documents with placeholder content.
Do not approve documents with typos.
Do not approve documents with formatting errors.

There is no "approve with comments."
There is no "minor issue we can overlook."
REJECT and let the initiator correct.

═══════════════════════════════════════════════════════════════
```

**When routing for approval:**
```
═══════════════════════════════════════════════════════════════
APPROVAL ASSIGNMENT: {DOC_ID}
═══════════════════════════════════════════════════════════════

FINAL VERIFICATION - YOU ARE THE LAST LINE OF DEFENSE

Before approving, confirm:
- [ ] Frontmatter complete (title, revision_summary with CR ID)
- [ ] All review findings from previous cycle addressed
- [ ] No new deficiencies introduced

IF ANY DOUBT EXISTS: REJECT

An incorrectly approved document creates nonconformance.
A rejected document creates a correction cycle.
Rejection is always the safer choice.

═══════════════════════════════════════════════════════════════
```

### Implementation

Update `qms.py` to include these reminders in:
- Inbox display for pending reviews/approvals
- Status output when checking review-pending documents
- CLI output when review/approval is assigned

---

## Proposal 4: QA Agent Behavioral Directives

### Concept

Add explicit behavioral directives to QA agent's system prompt that establish the correct mental model.

### Proposed Additions to QA Instructions

```
QA BEHAVIORAL DIRECTIVES
========================

1. COMPLIANCE IS BINARY
   - A document is compliant or non-compliant
   - There is no "mostly compliant" or "compliant enough"
   - 99% compliance = non-compliant
   - One deficiency = rejection

2. ZERO TOLERANCE
   - Missing frontmatter field = REJECT
   - Typo in document = REJECT
   - Formatting inconsistency = REJECT
   - Placeholder content = REJECT
   - ANY deficiency = REJECT

3. VERIFY WITH EVIDENCE
   - Read the actual frontmatter YAML block
   - Quote the revision_summary value you observed
   - Do not assume compliance—prove it
   - "Frontmatter OK" is not acceptable—state what you verified

4. REJECTION IS CORRECT BEHAVIOR
   - Rejection is not punishment
   - Rejection is the mechanism that ensures quality
   - The initiator benefits from catching errors before release
   - You are protecting the integrity of the QMS

5. THERE ARE NO EXCEPTIONS
   - "It's just a typo" = REJECT
   - "The content is good otherwise" = REJECT
   - "We can fix it later" = REJECT
   - "It's not a big deal" = REJECT
   - No exception is minor enough to overlook

6. WHEN IN DOUBT
   - REJECT
   - Always REJECT
   - The cost of false rejection: one correction cycle
   - The cost of false approval: nonconformance, investigation, CAPA
   - REJECT
```

---

## Proposal 5: Automated Pre-Validation (CAPA-003 Related)

### Concept

Add validation logic to `qms.py` that runs before routing for review/approval. Validation failures block the operation.

### Proposed Validations

```python
def validate_for_review(doc_id):
    """Run before route --review. Returns True only if ALL validations pass."""
    failures = []

    # Check frontmatter
    frontmatter = parse_frontmatter(doc_path)

    if 'title' not in frontmatter or not frontmatter['title'].strip():
        failures.append("Missing or empty 'title' in frontmatter")

    if 'revision_summary' not in frontmatter or not frontmatter['revision_summary'].strip():
        failures.append("Missing or empty 'revision_summary' in frontmatter")
    elif not re.match(r'^CR-\d+:', frontmatter['revision_summary']):
        failures.append("revision_summary must begin with CR ID (e.g., 'CR-001: ...')")

    # Check for placeholders
    content = read_document(doc_path)
    placeholders = re.findall(r'\b(TBD|TODO|FIXME|XXX)\b', content, re.IGNORECASE)
    if placeholders:
        failures.append(f"Document contains placeholder text: {', '.join(set(placeholders))}")

    # Report results
    if failures:
        print("VALIDATION FAILED - Cannot route for review:")
        for f in failures:
            print(f"  - {f}")
        print("\nCorrect these issues before routing.")
        return False

    return True
```

### Behavior

- **Blocking**: Document cannot be routed if any validation fails
- **No override**: There is no `--force` flag. Fix the document.
- **Audit logged**: All validation attempts (pass and fail) are recorded

### Rationale

Automated validation catches obvious deficiencies before human review. This is not a replacement for QA review—it is an additional layer that prevents wasting QA's time on documents that are trivially non-compliant.

---

## Recommended Implementation Priority

| Priority | Proposal | Effort | Impact |
|----------|----------|--------|--------|
| 1 | Proposal 4: QA Behavioral Directives | Low | High |
| 2 | Proposal 1: Mandatory Pre-Review Checklist | Low | High |
| 3 | Proposal 2: Structured Review Format | Low | High |
| 4 | Proposal 3: Review Prompt Injection | Medium | High |
| 5 | Proposal 5: Automated Pre-Validation | High | High |

### Rationale

- Proposals 1, 2, and 4 can be implemented immediately by updating QA agent instructions
- Proposal 3 requires `qms.py` modification but is straightforward
- Proposal 5 is the most robust automated safeguard but requires development effort

---

## Questions for Discussion

1. Should the mandatory checklist be embedded in QA's system prompt, or codified in a controlled document (SOP appendix)?

2. For Proposal 5 (automated validation): Should we validate only machine-verifiable items (frontmatter fields, placeholders), or attempt to validate structure/template compliance as well?

3. Should we require QA to quote the actual frontmatter values in every review, or only when recommending rejection?

4. Do we want document-type-specific checklists (SOP checklist, CR checklist, INV checklist), or one universal checklist?

---

## Next Steps

1. Review proposals with Lead
2. Select proposals for implementation
3. If Proposals 1/2/4: Update QA agent instructions (immediate)
4. If Proposal 3/5: Create CR for qms.py changes
5. Update INV-002 EI-5 with implementation evidence

