# Idea Tracker

*Personal scratch-pad for free-form musing. Not part of QMS or any official tracking.*

---

## 2026-02-04

### Formalize UATs as Stage Gates

During CR-055 execution, the Lead performed User Acceptance Testing (UAT) before the CR was routed for post-review. This pattern—having the user verify functionality before closing execution—proved valuable for ensuring actual user-facing validation occurs.

**Current state:**
- UAT is ad-hoc, requested informally during execution
- No formal EI template language for UAT steps
- No distinction between "developer testing" and "user acceptance testing"

**Potential formalization:**
- Add UAT as a named stage gate in executable document workflows
- CR execution tables could have explicit UAT rows: `| EI-N | User Acceptance Testing | [Protocol] | [Pass/Fail] | lead - DATE |`
- Define what qualifies as UAT vs. regular testing (user performs vs. developer performs)
- Consider whether UAT should be mandatory for user-facing changes or optional

**Questions:**
- Should UAT be a distinct EI or a suffix on the final implementation EI?
- Who can perform UAT? Only `lead`, or any human user?
- Should UAT protocols be formal documents or inline in execution comments?
- Does this overlap with any GMP testing concepts (IQ/OQ/PQ)?

---

## 2026-01-19

### Agent resume failures and wasteful fresh spawns

Frequently observe agent resume attempts completing immediately with "0 tool uses · 0 tokens" followed by spawning an entirely new agent. This is wasteful since fresh agents must rebuild context from scratch.

**Observed causes:**
1. **API concurrency errors (400):** Conflict in underlying API calls, possibly from resuming too quickly after previous action
2. **Context/state mismatches:** Agent's preserved context leads it to believe task is already complete
3. **Insufficient resume prompts:** Prompt doesn't give agent actionable work in its current state

**Current pattern:**
```
qa(QA post-review of CR-033) resuming a77b9a2
  ⎿  Done (0 tool uses · 0 tokens · 1s)

# Then immediately:
qa(QA post-review of CR-033) spawning new agent...
```

**Potential improvements:**
- Add delay/backoff before resume attempts
- Provide more explicit context in resume prompts about what still needs to be done
- Implement retry logic for resume failures instead of immediately spawning fresh
- Investigate whether Claude Code infrastructure changes could improve resume reliability

**Questions:**
- Is this a Claude Code limitation or user error in resume prompts?
- Would structured "agent handoff" context help (e.g., "previous action was X, next action should be Y")?
- Can agent state be inspected before deciding to resume vs. spawn fresh?

---

## 2026-01-09

### SOP approval requires executable infrastructure (refined)

An SOP must not be approved until the procedures it enforces are able to be executed/followed. **However**, the applicability of this rule depends on how the SOP is written.

#### Two types of SOPs:

**1. Behavioral SOPs** — Define what agents *must do* or *must not do*
- Example: "The orchestrator shall not prescribe specific review criteria when spawning reviewer agents"
- Followable immediately through behavioral discipline
- No tooling required; compliance is a choice
- Can be approved without any infrastructure changes

**2. Tooling-dependent SOPs** — Mandate use of specific infrastructure
- Example: "Documents shall be created using `qms create` with official templates"
- Requires the referenced tooling to exist
- Cannot be followed until infrastructure is in place
- Must wait for infrastructure CR to close before SOP approval

#### The key insight:

SOPs set **behavioral baselines**. Tooling (CLI, templates, etc.) can *exceed* SOP requirements by adding reminders, guardrails, and conveniences—but the SOP itself need not mandate these enhancements.

**Example for SOP-007 (Agent Orchestration):**
- SOP says: "The orchestrator shall not prescribe review criteria" → behavioral, followable today
- RS/CLI *may later* add: "Inject reminder about review criteria rules" → enhancement, not requirement
- The RS can be stricter than the SOP; the SOP sets the floor, not the ceiling

#### When the infrastructure rule applies:

| SOP Type | Infrastructure Required? | Example |
|----------|-------------------------|---------|
| Behavioral | No | "Agents shall not impersonate other agents" |
| Tooling-dependent | Yes | "All documents shall use official templates from `QMS/TEMPLATE/`" |
| Hybrid | Partial | Behavioral rules can be approved; tooling-dependent sections wait |

**Considerations:**
- Write SOPs in behavioral terms where possible to avoid chicken-and-egg
- Reserve tooling mandates for cases where behavioral compliance is insufficient
- RS can always exceed SOP requirements; there's no GMP rule against *additional* strictness

---

## 2026-01-08

### Restrict Claude from prescribing review requirements in agent messages

When spawning QA or reviewer agents, Claude (the orchestrator) should not dictate specific review criteria or acceptance requirements in the task prompt. This undermines the independence of the review function.

**Problem:** Prompts like "verify the CR has X, Y, Z" or "if conditions A and B are met, approve" effectively pre-determine the review outcome. The reviewer becomes a rubber stamp executing Claude's checklist rather than applying independent judgment.

**Principle:** Reviewers should derive review criteria from:
1. The governing SOPs (SOP-001, SOP-002, etc.)
2. Their domain expertise (for TUs)
3. Their independent assessment of the document

**Current violation pattern:**
```
Task(subagent_type="qa", prompt="Review CR-017. Verify it includes EI-1, EI-2, EI-3...")
```

**Preferred pattern:**
```
Task(subagent_type="qa", prompt="Review CR-017 for pre-approval per SOP-002.")
```

**Considerations:**
- Context is fine (what the CR is about, why it was returned previously)
- Prescriptive criteria are not (what must be present for approval)
- May need to formalize this in CLAUDE.md or a future SOP-007

---

## 2026-01-06

### Visual distinction for executed content in closed documents

When viewing a post-approved/closed CR, it's not immediately obvious at a glance which parts were filled in during execution vs. what was pre-approved content. This requires prior knowledge of the document template structure.

**Problem:** The execution table and execution summary blend in visually with the rest of the document.

**Possible solutions:**

1. **Section headers with visual markers:**
   - `## 6. Execution ▶ COMPLETED` or similar suffix
   - Use emoji or symbols to mark executed sections

2. **Blockquote or callout wrapping:**
   - Wrap execution content in a styled blockquote
   - Use GitHub-style callouts: `> [!NOTE]` or custom `> [!EXECUTED]`

3. **Horizontal rule boundaries:**
   - Double horizontal rules (`---\n---`) to demarcate execution block
   - Or distinctive ASCII art separators

4. **Background shading (renderer-dependent):**
   - HTML `<div>` with background color (works in some markdown renderers)
   - Not portable across all viewing contexts

5. **Prefix/suffix markers in content:**
   - `[EXECUTION START]` / `[EXECUTION END]` visible markers
   - Clear but adds textual noise

**Considerations:**
- Must work in raw markdown (Claude reads raw)
- Should also render meaningfully in GitHub/rendered views
- Should not interfere with auditability or document integrity
- Consider whether this applies to all executable docs or just CRs

---

### VAR scope handoff requirements

Just as an ER defines its own scope and closure requirements, a VAR must explicitly specify, from the parent EI:

1. What was successfully accomplished in the parent (before the variance)
2. What the VAR "absorbs" (takes responsibility for)
3. Confirmation that no items were lost in the handoff

If scope is truly reduced (i.e., something from the original plan will not be done), this must be explicitly stated and justified.

**Auditor confidence:** When an auditor sees an EI with an attached VAR, they must have confidence that closure of the VAR is equivalent to complete closure/success of the EI. The VAR is not a loophole—it is a container that fully accounts for the remaining work.

**Rationale:** Prevents scope leakage during variance handling. The VAR becomes a complete record of what transferred from parent to child, ensuring traceability and preventing items from silently disappearing.

---

### GMP conventions for signature and timestamp formats

Define standard formats for signatures and timestamps in executable documents.

**Example format:** `lead 06Jan2025 05:24 PM`

**Considerations:**
- User identifier (lowercase username)
- Date format (DDMmmYYYY — no ambiguity between US/EU conventions)
- Time format (12-hour with AM/PM, or 24-hour?)
- Timezone handling: Use UTC for total unambiguity (e.g., `lead 06Jan2025 17:24 UTC`)

This affects TC, TP, ER, and any document with execution-phase signatures.

---

### Investigate: CRs in draft state in QMS directory when IN_EXECUTION

Double check why CRs appear in draft state (`CR-XXX-draft.md`) in the QMS directory even when:
- Status is IN_EXECUTION
- `checked_out` is false

Expected behavior: Once a CR is released for execution (IN_EXECUTION), the document should probably be in a non-draft state in the filesystem. Need to investigate whether this is:
1. Expected behavior (draft filename is just a naming convention)
2. A bug where the file should be renamed/moved on release
3. A gap in the document lifecycle handling

---

### Execution instructions: comments vs. visible content

When designing executable document templates, should execution instructions (guidance on what to fill during execution phase) be placed in:

1. **HTML comments** (`<!-- ... -->`)
   - Pros: Doesn't clutter rendered output; clearly meta-content
   - Cons: Invisible when viewing rendered markdown; easy to overlook; some tools strip comments

2. **Visible document content** (blockquotes, callout boxes, labeled sections)
   - Pros: Always visible; harder to miss; part of the auditable record
   - Cons: Adds visual noise; mixes instructions with content

**Hybrid approach?**
- Use visible callouts for critical instructions (e.g., "DO NOT MODIFY Sections 1-5")
- Use comments for detailed reference material (status values, examples)

**Considerations:**
- Who is the audience? Agents read raw markdown; humans may view rendered
- Should instructions remain after execution, or be replaced/removed?
- Do instructions need to be part of the audit trail?

---

### SOP-007: Security, User Management, and Agent Orchestration

Consider a new SOP covering:

- **User Management:** Formal definition of user accounts (lead, claude, qa, tu_*, bu), onboarding/offboarding procedures, permission changes
- **Agent Orchestration:** Rules for spawning subagents, identity propagation, agent reuse within sessions, agent-to-agent communication boundaries
- **Security:** Access control principles, prohibited behaviors, audit trail requirements, identity verification (ties to the identity verification architecture gap noted below)

**Rationale:**
- SOP-001 Section 4 defines user groups and permissions, but doesn't cover the full lifecycle or orchestration model
- Agent orchestration is currently implicit in CLAUDE.md but not formally governed
- Security considerations are scattered across multiple documents

**Questions to resolve:**
- Should this be one SOP or split into separate concerns?
- Does user management warrant its own SOP, or is it an extension of SOP-001?
- How does this interact with the identity verification gap (prompt injection vs. cryptographic verification)?

---

## 2026-01-05

### `--review-and-approval` flag for streamlined routing

Add a `--review-and-approval` flag to `qms route` so that documents can be routed for combined review+approval. When QA is the only reviewer, they would be reminded after submitting a "recommend" review that they can proceed directly to approval.

This replaces the current ad-hoc mechanism where QA chooses to approve immediately after reviewing in all cases - making it explicit and opt-in at routing time.

**Potential usage:**
```
qms route DOC-ID --review-and-approval
```

**Behavior:**
- Routes for review as normal
- After QA submits RECOMMEND, system prompts: "You are the sole reviewer. Proceed to approval? [Y/N]"
- If Y, transitions directly to approval workflow without requiring separate `route --approval`

---

### Multi-step prompts for workflow guidance

Expand the usage of multi-step prompts that guide agents through permitted channels in various workflow contexts.

**Concept:** Instead of agents needing to know the full workflow state machine, the CLI provides contextual "what can I do next?" guidance after each action. Example:

```
✓ Review submitted for CR-012 (RECOMMEND)

You are in: IN_PRE_REVIEW → PRE_REVIEWED

Available actions for user 'qa':
  [1] Route for approval:  qms route CR-012 --approval
  [2] Assign additional reviewers:  qms assign CR-012 --assignees <users>
  [3] Check document status:  qms status CR-012

Select action or press Enter to exit:
```

**Benefits:**
- Reduces workflow errors (agents can't take invalid actions)
- Self-documenting (agents learn valid transitions by using the system)
- Prevents impersonation (prompts show actions valid for *this* user only)
- Replaces need to memorize SOP workflow diagrams

---

### Identity verification architecture gap (critical insight)

**The fundamental problem:** Agent identity is established purely through prompt injection. There is no programmatic way for the CLI to verify caller identity.

**What each component knows:**

| Component | Knows | Doesn't Know |
|-----------|-------|--------------|
| Orchestrator (claude) | Which subagent_type it spawned, the returned agentId | - |
| Spawned agent (qa) | "I am qa" from its prompt content | Its own agentId, any cryptographic proof |
| CLI (qms.py) | The `--user` argument string | Who is actually calling, any verification |

**The gap visualized:**

```
┌─────────────┐     spawns      ┌─────────────┐     executes    ┌─────────────┐
│   claude    │ ──────────────► │     qa      │ ──────────────► │   qms.py    │
│ (orchestr.) │  agentId: abc   │  (subagent) │  --user qa      │   (CLI)     │
│             │                 │             │                 │             │
│ knows: qa   │                 │ knows: "I   │                 │ knows:      │
│ is abc      │                 │ am qa" from │                 │ NOTHING     │
│             │                 │ prompt only │                 │ about caller│
└─────────────┘                 └─────────────┘                 └─────────────┘
```

**Agent IDs (e.g., `a3cc3ae`):** These are session identifiers for resuming agents, but:
- CLI doesn't receive agent ID as context when executed
- No API exists for CLI to query "who is calling me?"
- Agent ID is known to orchestrator, not to spawned agent or CLI

**Possible solutions (require Claude Code infrastructure changes):**

1. **Session token injection**: Claude Code injects verifiable token into subagent context; subagent passes to CLI; CLI verifies token maps to claimed identity

2. **Environment variable propagation**: Claude Code sets `CLAUDE_AGENT_ID` and `CLAUDE_AGENT_TYPE` env vars that CLI can read

3. **Registry + callback**: Orchestrator writes `{agentId: identity}` to registry file; CLI receives agentId somehow and queries registry

4. **Cryptographic attestation**: Each agent receives a signed identity claim that CLI can verify against a public key

**Current practical options (within our control):**

1. **Honor system + audit trail**: Trust prompt injection, but log everything for forensic analysis
2. **Two-step confirmation**: Force explicit identity assertion (psychological deterrent, not technical enforcement)
3. **Mismatch detection in output**: CLI outputs the claimed `--user` prominently; orchestrator notices if it doesn't match expected subagent

**Open question:** Can we petition Claude Code team for identity propagation features?

---

### `/idea` slash command

Create an `/idea` slash command that expands into:

```
Please add the following to the idea tracker:
```

Makes capturing ideas frictionless - just type `/idea <your idea>` and it gets appended to IDEA_TRACKER.md with timestamp.

---

### `revision_summary` field - relax CR requirement

The `revision_summary` frontmatter field currently has language (possibly in QA review prompts or qms.py) requiring it to start with "CR-". This isn't always appropriate.

**Cases where no CR exists:**
- Initial document creation (v0.1 drafts)
- Documents created outside CR workflow (INV, CAPA created reactively)
- Foundational documents that predate the CR process
- SOPs created to establish the QMS itself (chicken-and-egg)

**Current problematic language (to find and fix):**
- QA review checklist: "revision_summary begins with CR ID (e.g., CR-XXX:)"
- Possibly in `generate_review_task_content()` in qms.py

**Proposed fix:**
- For v1.0+ documents created via CR: require CR reference
- For v1.0+ documents NOT created via CR: require meaningful summary, no CR prefix needed
- For v0.x documents: field not required (per SOP-001 Section 5.1)

**Example valid revision_summary values:**
- `"CR-012: Implement QA review safeguards"` (CR-driven change)
- `"Initial release of SDLC Governance SOP"` (foundational document)
- `"Address findings from INV-003"` (reactive document)

---

### Official document templates under change control

Create official, QMS-governed templates for each document type. Templates themselves would go through the CR/review/approval process.

**Proposed structure:**
```
QMS/
├── CR/
│   ├── CR-TEMPLATE.md      ← Official CR template (governed)
│   ├── CR-001/
│   └── ...
├── SOP/
│   ├── SOP-TEMPLATE.md     ← Official SOP template (governed)
│   └── ...
├── INV/
│   ├── INV-TEMPLATE.md     ← Official INV template (governed)
│   └── ...
└── CAPA/
    ├── CAPA-TEMPLATE.md    ← Official CAPA template (governed)
    └── ...
```

**Benefits:**
- Single source of truth for document structure
- Template changes require CR (prevents drift)
- `qms create` can copy from official template
- Reviewers can compare against template for structure compliance
- Version-controlled templates enable template evolution tracking

**Implementation:**
- Templates are effective documents (approved, in `QMS/` proper)
- Template changes require CR like any other document change

**Location options:**

| Option | Structure | Pros | Cons |
|--------|-----------|------|------|
| A. Co-located | `QMS/CR/CR-TEMPLATE.md` | Templates live with their documents | Only works for doc types with folders |
| B. Subfolder | `QMS/templates/CR-TEMPLATE.md` | Centralized, lowercase convention | Separate from documents |
| C. Dedicated folder | `QMS/TEMPLATE/CR-TEMPLATE.md` | Follows QMS folder convention, can include non-doc templates | New top-level folder |

**Option C advantages:**
- Can house templates beyond document types:
  - `QMS/TEMPLATE/CR-TEMPLATE.md`
  - `QMS/TEMPLATE/INV-TEMPLATE.md`
  - `QMS/TEMPLATE/REVIEW-TEMPLATE.md` (structured review response)
  - `QMS/TEMPLATE/APPROVAL-TEMPLATE.md` (approval checklist)
  - `QMS/TEMPLATE/COMMIT-TEMPLATE.md` (git commit format)
- Templates themselves could be governed documents (TMPL-001, TMPL-002, etc.)
- `qms create CR` copies from `QMS/TEMPLATE/CR-TEMPLATE.md`

---
