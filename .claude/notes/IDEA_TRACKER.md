# Idea Tracker

*Personal scratch-pad for free-form musing. Not part of QMS or any official tracking.*

---

## 2026-01-06

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
