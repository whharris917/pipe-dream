# Discussion: Verification Records (VR) — A New QMS Document Type

**Session:** 2026-02-16-004
**Participants:** Lead, Claude

---

## Context

CR-088 post-closure revealed a deficiency: integration verification was structural (grep, imports, CLI registration) rather than behavioral (starting services, observing behavior). CR-084 already mandates integration verification, but the mandate had no structure — so weak evidence filled the box. The fix isn't more mandate; it's giving the mandate a form.

---

## Testing Taxonomy

The Lead established a framework for thinking about testing:

**Core four elements of a test:** instruction, expected result, actual result, outcome (pass/fail). Everything else (comments, acceptance criteria, evidence fields) is supplementary.

**Three script types:**

| Type | Characteristics | Use When |
|------|----------------|----------|
| **Scripted** | Precisely defined steps, exact expected outcomes, no wiggle room | Precision is paramount; outcomes are binary |
| **Unscripted** | Well-defined final outcome, flexible path | Goal is clear but steps don't need rigid definition |
| **Exploratory** | Lab notebook style, discovery-oriented | Figuring something out, triage, debugging |

**Automated vs. manual** is an orthogonal axis that cuts across all three types.

**Mapping to current QMS:**
- Scripted automated = committed unit tests (416 in qms-cli)
- Scripted manual = TP execution (never done — too onerous)
- Unscripted manual = CR-084's "integration verification" (practiced but unstructured)
- Exploratory manual = debugging sessions, INV execution (not formalized as testing)

---

## The Problem with Ad Hoc Terminal Testing

Claude often performs verification via inline scripts during CR execution. This has several failure modes:

1. **Unreviewed tests** — the test itself might be wrong or poorly scoped
2. **Muddled evidence trail** — troubleshooting the test obscures what was actually proven
3. **Surgical scope** — tests target exactly what was changed, missing adjacent breakage ("the tree was healthy but the forest was on fire")
4. **Opaque to reviewers** — multi-line inline scripts aren't readable evidence
5. **"PASS" conflation** — "the test passed" and "the feature works" are different claims

---

## Signature Types on Executable Documents

Adapted from GMP pharma conventions for our context. These define the *role* of the person signing an executable document, and what their signature attests to:

| Signature Type | Role | What It Attests |
|----------------|------|-----------------|
| **Performer** | Executes the test steps | "I did this and observed this" |
| **Witness** | Witnesses execution contemporaneously | "I watched the Performer do this and confirm what they observed" |
| **Verifier** | Repeats the step themselves (not necessarily contemporaneously) | "I independently reproduced this result" |
| **Reviewer** | Reviews the executed document without executing anything | "The evidence is complete, consistent, and supports the claimed outcomes" (e.g., timestamps in order, expected results match actual results) |

**Mapping to our current QMS:**
- **Performer**: Claude executing EIs during CR execution, filling in VRs
- **Witness**: Not currently practiced — would require a second agent or human witnessing contemporaneously
- **Verifier**: Not currently practiced — would require independent reproduction of results
- **Reviewer**: QA and TUs during post-review — they review the executed document, not re-execute

**Implication for VRs:** The Performer fills in the VR contemporaneously during testing. The Reviewer (QA) evaluates the filled VR during post-review. The VR form must produce evidence clear enough for a Reviewer to assess without having been present. This is why observational evidence ("started X, observed Y, here's the log") is superior to assertional evidence ("test passed") — the Reviewer can evaluate observational evidence on its own merits.

**The Verifier as a design constraint:** VRs should be executed in such a way that a Verifier — someone without expansive background knowledge of the project — could follow the completed VR's instructions and confirm matching results. This means:

- The *executed* VR becomes a de facto reproducible script, even though it was unscripted going in
- Before execution: unscripted (Performer doesn't pre-define steps)
- After execution: detailed enough for independent reproduction

This mirrors GMP batch records: the blank form says "weigh ingredient X" (high-level); the executed form says "weighed 45.2g of ingredient X on balance #1234 at 14:32" (specific, reproducible).

**Litmus test for a completed VR:** Could a Verifier who knows how to operate a terminal, but doesn't know the project architecture, follow this and get the same results?

**TEMPLATE-VR implication:** The form must prompt the Performer to record:
- Specific commands/actions taken (actual commands, not summaries)
- Specific outputs/behaviors observed (copy-pasted, not paraphrased)
- Environment and preconditions (system state, services running, branch/commit)

**Future possibilities:** Witness and Verifier roles could become relevant as multi-agent integration testing matures. A second agent could independently reproduce results (Verifier) or observe execution in real-time via the GUI/WebSocket infrastructure (Witness).

---

## The VR Concept

**Verification Records (VRs)** are lightweight child documents of CRs that serve as formal evidence containers for unscripted testing.

### Design Principles

- VRs are the **pinnacle of proof** — what you show an auditor who asks "demonstrate that CR-XYZ-EI-N passed"
- They are **forms to fill out**, not planning documents — they come "pre-approved" because the template itself is the approval (batch record analogy)
- Evidence must be **observational** (what was done, what was observed) not **assertional** (an inline script printed PASS)
- Evidence must be **contemporaneous** (recorded at time of testing, per ALCOA+ principles)

### The Batch Record Analogy

| GMP Pharma | QMS VR |
|------------|--------|
| Approved master batch record | TEMPLATE-VR (approved form structure) |
| Pull blank form for a batch | Create VR from template during CR execution |
| Fill in contemporaneously during manufacturing | Fill in during testing — objectives, observations, evidence |
| Reviewed during batch release | Reviewed during CR post-review |

### Two Types of Acceptable Evidence

1. **Observational evidence** (VRs) — "I started the services, performed X, observed Y." Inherently holistic because the system is running. Readable by anyone.
2. **Automated test results** (RTM) — "The committed test suite passes at commit X." Reviewed, committed, CI-verified, reproducible.

Ad hoc terminal scripts are **development aids, not verification evidence**. They are neither committed tests nor behavioral observations.

### Lifecycle

- **Created:** During CR execution, after code changes
- **Filled in:** Contemporaneously with testing
- **Reviewed:** During CR post-review (QA evaluates sufficiency of evidence)
- **Closed:** When parent CR closes

No pre-review, no pre-approval, no release. Lightest document type in the QMS.

### QA's Role

During post-review, QA evaluates VRs for:
- Is the evidence sufficient?
- Does the actual result support the claimed outcome?
- Is the evidence observational, not just assertional?
- Was the scope holistic (forest-level), not just surgical (tree-level)?

QA's role with VRs is the **Reviewer** signature type: they didn't execute anything, but they verify the executed form is complete, consistent, and supports the claimed outcomes.

### Template Design Implication

TEMPLATE-VR must guide the tester toward producing auditor-ready evidence. The form should make it hard to write "verified, works fine" and easy to write "started services with X, performed Y, observed Z, here's the log output."

---

## Isomorphic QMS Problems

The VR addresses a specific instance of a general pattern: **a mandate exists but lacks a structured evidence container, so weak evidence satisfies the requirement without achieving its intent.**

### Where This Pattern Appears

**1. CAPA effectiveness verification (SOP-003)**

CAPAs are "verified complete" by confirming child CRs are closed. "Closed" means the CR went through workflow — not that the corrective action actually eliminated the root cause. We verify the paperwork was done, not that the medicine worked. A VR-like form attached to CAPA execution ("demonstrate the corrective action resolved the deviation") would close this gap.

**2. EI execution summaries generally**

The EI table's Execution Summary column is free text. Some entries are rich ("commit abc123, 416 tests pass, CI run 22077645945"). Others are "Completed as described." There's no structural floor for adequate evidence. The VR extracts the evidence burden out of this free-text field and into a structured form where weak evidence is visibly weak.

**3. Qualitative proofs in the RTM**

The RTM has two verification types: unit tests (structured — file, function, commit, PASS) and qualitative proofs (unstructured — prose argument). Unit test entries have a natural form that makes inadequacy visible. Qualitative proofs don't. Same pattern: mandate (prove the requirement is met), no form (free prose).

### The Mandate Escalation Cycle

The recurring pattern in QMS evolution:

1. A failure happens
2. We create a mandate (SOP update, template language)
3. The mandate is technically satisfiable with minimal effort
4. It fails in practice because minimum compliance ≠ actual rigor
5. We add another mandate → go to step 3

Examples: INV-007 through INV-010 produced mandates. CR-084 produced a mandate. CR-085/086 produced mandates. Each is a procedural checkbox technically satisfiable without achieving its intent.

**The VR breaks this cycle by providing form instead of mandate.** The form makes rigor the path of least resistance. When we notice a mandate failing, the first question should be "does this need a form?" rather than "does this need a stronger mandate?"

---

## EI Table: VR Column

The CR template's EI table should include a **VR column** that flags which execution items require a Verification Record.

**Current EI table columns:** EI | Task Description | Execution Summary | Task Outcome | Performed By — Date

**Proposed EI table columns:** EI | Task Description | VR | Execution Summary | Task Outcome | Performed By — Date

The VR column serves double duty:

| Phase | Column Content | Field Type |
|-------|---------------|------------|
| **Planning (pre-approval)** | "Yes" or blank — flags the requirement | Static |
| **Execution** | VR document ID (e.g., `CR-089-VR-001`) | Editable |

**Pre-review:** QA evaluates whether the right EIs are flagged for VR. Not every EI needs one — "commit and push pre-execution state" doesn't; "implement health check fix" does.

**Post-review:** QA verifies that all flagged EIs have a corresponding completed VR with sufficient evidence.

**This resolves the "mandatory vs. discretionary" question:** VRs are per-EI, determined at planning time, and approved as part of the CR scope. The requirement is precise, not blanket.

---

## Further Design Extensions

### 1. VR as a Third RTM Verification Type

The RTM currently has two verification types. VRs add a third:

| Type | Nature | Evidence | Best For |
|------|--------|----------|----------|
| **Unit Test** | Automated, committed | Test file + commit + PASS | Deterministic, repeatable assertions |
| **Qualitative Proof** | Analytical reasoning | Prose argument + code references | Structural/architectural claims ("no circular imports") |
| **Verification Record** | Behavioral observation | VR ID + observational evidence | System-level behavioral claims ("health check produces no errors") |

Some requirements are awkward to unit test (you'd mock away the thing you're verifying) and aren't purely analytical (you need to run the system). "The health check shall not generate error log entries" is a behavioral claim best verified by observation. Currently it would be a qualitative proof, but it's not *analysis* — it's *observation*.

This also sharpens what qualitative proofs are: structural or architectural analysis where the code itself is the evidence. If you need to run the system to prove it, that's a VR, not a qualitative proof.

The RTM gains a traceability link: requirement → VR (in CR-089) → observational evidence.

### 2. Pre-Conditions Section in the VR Form

If VRs must be reproducible by a Verifier, they need a pre-conditions block: what state the system must be in before verification starts.

Example: "Services running on ports 8000/8001, container launched from image v2.3, branch `cr-089-health-check` checked out at commit abc1234."

Without this, a Verifier can't establish the same starting conditions. It also forces the Performer to be explicit about what they assumed — which is exactly the kind of unstated assumption that caused the CR-088 failure (assumed services were running, never actually started them).

### 3. VAR and ADD Templates Also Get the VR Column

VARs and ADDs have their own EI tables for resolution/correction work. If that work involves code changes, those EIs should also be flaggable for VR. The pattern is consistent: **any EI table that can contain code-affecting work should support VR flagging.** This includes TEMPLATE-CR, TEMPLATE-VAR, and TEMPLATE-ADD.

### 4. Simplify CR-084 Integration Verification Language

CR-084 added integration verification language to SOP-002 Section 6.8 and the CR/VAR templates. With VRs, this language can be simplified: instead of describing what integration verification *is* and how to document it (the mandate-without-form pattern), it can say **"integration verification shall be documented in Verification Records."** The VR form handles the structure. The SOP defines the *requirement*; the form enforces the *rigor*.

This is a clean example of the "form instead of mandate" principle in action — replacing paragraphs of procedural language with a reference to a structured form.

### 5. VR Scope Guidance: Forest-Level by Default

VRs should default to forest-level scope unless there's a specific reason to be narrow. The instruction shouldn't be "verify the health check endpoint returns 200" — it should be "verify the service health monitoring works correctly."

The broader framing naturally leads the Performer to check adjacent behavior. When you're asked to verify "service health monitoring," you check the health check endpoint, look at logs, verify status commands, check for side effects. When asked to verify "the endpoint returns 200," you hit the endpoint once and stop.

Tree-level surgical scope should be the exception requiring justification, not the default. The TEMPLATE-VR or SOP guidance should encode this: **"VR objectives should describe the capability being verified, not the specific mechanism."**

---

## Periodic Reviews

A separate but complementary concept to VRs. VRs verify that *new changes* work at the time of implementation. Periodic reviews verify that *existing claims* are still true and that *past work* met quality standards.

### Concept

A periodic review is a structured quality check that can be triggered on a schedule, ad hoc, or at milestones. The defining characteristic is **blind, independent verification** — the reviewer assesses evidence quality or system behavior without reference to existing proof artifacts.

### Review Types

| Type | Method | What It Catches |
|------|--------|-----------------|
| **Requirement spot-check** | Select N REQs at random; verify them manually without referencing the RTM or existing tests | RTM drift, phantom tests, stale qualitative proofs, ambiguous requirements |
| **CR evidence audit** | Select an old CR at random; evaluate whether its execution evidence actually demonstrates what it claims | Weak EI summaries, insufficient VRs, surgical-only verification |
| **INV root cause review** | Select an old INV at random; assess whether the root cause analysis was thorough and whether CAPAs actually addressed the root cause | Superficial RCA, symptom-treatment CAPAs, recurrence of "fixed" problems |

### Connection to VRs

The periodic review is the Verifier role at scale. Each requirement selected for spot-check produces a VR documenting the independent verification. If the VR outcome contradicts the RTM's claim, that's a finding.

For CR and INV audits, the reviewer doesn't produce VRs but rather evaluates the quality of existing evidence — applying the same standards QA uses during post-review, but retroactively and independently.

### Outputs

- **Findings:** Requirements that fail verification, RTM inaccuracies, weak evidence, unaddressed root causes
- **Disposition:** Findings may spawn INVs (for systemic issues), CRs (for corrections), or RTM updates (for drift)
- **VRs:** One per spot-checked requirement (the evidence of independent verification)

### Trigger and Scope

Specifics deferred — could be calendar-based, milestone-based (every N CRs), or purely ad hoc at the Lead's discretion. The important thing is the mechanism exists and can be invoked.

---

## Idea Grab Bag: Extensions, New Types, Techniques

Extrapolations from the VR and periodic review discussion, organized from most concrete to most speculative. None are committed — these are seeds for future consideration.

### 1. Acceptance Criteria as a First-Class CR Field

CRs have "Proposed State" but not explicit, testable acceptance criteria. A dedicated section — "This CR is successful if and only if: A, B, C" — gives VRs concrete targets to verify against and gives QA an unambiguous post-review checklist. The VR objective maps directly to an acceptance criterion. Pre-approved, so no goalpost-shifting during execution.

### 2. Negative Testing in VRs

VRs naturally gravitate toward happy-path verification: "show that X works." Equally important is: "show that Y does *not* happen." For access control: "demonstrate agent Z is blocked from git operations." For error handling: "demonstrate malformed input produces a clean error, not a crash." The TEMPLATE-VR could include a "Negative Verification" section prompting: "What should NOT happen? Verify it doesn't."

### 3. Pre-Mortem as a CR Planning Step

Before executing a CR, ask: "Assume this CR failed post-review. What went wrong?" Document the top 3 failure modes and how they'd be detected. One paragraph, lightweight, forces anticipatory thinking. CR-088's health check failure was predictable — "what if the new HTTP method also produces errors?" would have surfaced it during planning. Could be a field in the CR template between Implementation Plan and Execution.

### 4. Evidence Taxonomy

Formalize which evidence types are acceptable for which claims:

| Claim Type | Acceptable Evidence | Insufficient Evidence |
|------------|--------------------|-----------------------|
| Code exists/changed | Commit hash, diff | "Modified file X" |
| Tests pass | CI run link, commit + PASS | "Tests pass" (no link) |
| Service behavior | VR with log excerpts, terminal output | Ad hoc script result |
| Visual/UI change | Screenshot, screen recording | "Renders correctly" |
| Document updated | Document ID + version | "Updated per plan" |
| Access control | VR with denied-access evidence | "Permissions configured" |

Could live in SOP-004 as guidance for sufficient evidence in EI summaries and VRs. Makes "is this evidence adequate?" less subjective for both the Performer and the Reviewer.

### 5. Exploration Record (XR)

The third test type — exploratory — still has no QMS home. An XR is a lab notebook: structured enough to be useful, unstructured enough to not impede discovery. Fields: question being investigated, what was tried, what was observed, conclusions, follow-up actions. Not pass/fail — discovery-oriented.

Natural companion to INV investigations (the investigative work is exploratory, but currently gets crammed into CAPA execution summaries). Also useful for technology evaluations, performance profiling, and debugging sessions.

### 6. Dual-Path Verification for High-Risk Changes

For critical changes (security, data integrity, infrastructure), QA could flag a CR as requiring both automated tests AND a VR — belt and suspenders. Not for every CR, but as a risk-proportionate escalation. QA already decides whether TUs are needed; this extends that judgment to verification depth. The VR column in the EI table already supports this — QA could request-updates during pre-review if a high-risk EI isn't flagged for VR.

### 7. Right-First-Time Metrics

Track how often documents pass review on the first round vs. requiring request-updates. A leading indicator of process health — rising rejection rates signal unclear expectations, poor templates, or rushed work. Trailing indicators:

- VARs per CR (planning quality)
- ADDs per CR (execution thoroughness)
- Time from release to post-review routing (execution efficiency)
- Review rounds before approval (document quality)

Not for gamification — for spotting systemic trends that warrant investigation.

### 8. Traceability Completeness Automation

Periodically verify the traceability chain is intact: every REQ has RTM evidence, every RTM entry references a valid commit, every commit hash exists in git, every CI run link resolves. Currently all manual claims. A script could validate the mechanical links (does commit abc1234 exist? does test file X exist at that commit?). Doesn't replace human judgment about whether evidence is *sufficient*, but catches broken references and phantom citations. Connects to the "automate RTM generation" to-do item.

### 9. Configuration Baseline Records

We track code at specific commits but not the environment. Docker image versions, Python versions, dependency versions, MCP server configurations — all implicit. A configuration baseline snapshot at each System Release would make the qualified state truly reproducible.

Example: "At CLI-9.0, the system was qualified at commit X, with Python 3.11, dependencies per requirements.txt at commit X, Docker image sha256:Y."

If a periodic review fails a requirement that previously passed, the first question is "what changed?" Without a configuration baseline, the answer might be invisible.

### 10. Adversarial Review Mode

A QA review mode where the reviewer's explicit goal is to find the weakest claim and attempt to disprove it. Not "does this look complete?" but "what's the most likely thing that's wrong here, and can I find evidence?" Different mindset from standard review. Could be used selectively — every Nth CR, or for CRs in specific risk domains. The periodic review concept touches this retrospectively; adversarial review applies to *active* workflows.

---

## Decisions Made

1. VRs will be a new QMS document type (Option 2 — lightweight child documents)
2. VRs are reviewed as part of parent CR post-review, not via their own workflow
3. VRs come "pre-approved" — the template is the approval (batch record model)
4. Observational evidence and committed test results are acceptable; ad hoc scripts are not
5. Signature types formalized: Performer (executes), Witness (witnesses), Verifier (reproduces), Reviewer (reviews executed document)
6. Current practice uses Performer + Reviewer; Witness and Verifier are future possibilities
7. CR template EI table gains a VR column (static flag at planning, VR ID at execution)
8. VR requirement is per-EI, not blanket — determined at planning, approved as part of CR scope
9. VR is a third RTM verification type alongside Unit Test and Qualitative Proof
10. VR form includes a pre-conditions section for Verifier reproducibility
11. VR column applies to all EI tables: TEMPLATE-CR, TEMPLATE-VAR, TEMPLATE-ADD
12. CR-084 integration verification language to be simplified to reference VRs
13. VR scope defaults to forest-level; objectives describe capabilities, not mechanisms

## Open Items

### VR Implementation
- TEMPLATE-VR design (fields, structure, evidence guidance)
- QMS CLI support for VR document type
- Mechanical questions: VR state machine, naming convention (CR-089-VR-001?), creation workflow
- How signature types should be reflected in VR form fields
- Template updates: TEMPLATE-CR, TEMPLATE-VAR, TEMPLATE-ADD (add VR column to EI tables)
- RTM structure update to support VR as a verification type

### SOP/Process Updates
- SOP updates (SOP-002, SOP-004, SOP-006) to reference VRs
- SOP-002 Section 6.8 simplification (replace integration verification prose with VR reference)
- Whether the "mandate escalation cycle" insight should inform a broader review of existing mandates

### Periodic Reviews
- Document type or format for periodic reviews (new type? or ad hoc use of existing INV/CR?)
- Trigger mechanism (schedule, milestone, ad hoc — specifics deferred)
- Selection methodology for random sampling
- How findings are dispositioned (INV threshold vs. direct CR correction)
