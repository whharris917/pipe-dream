# Agent Identity and Multi-Step Prompts: Conceptual Outline

*Session-2026-01-09-001*

---

## 1. The Problem Statement

### 1.1 Identity is Established by Prompt Injection

In the current QMS agent model, identity is a social contract, not a technical guarantee:

```
┌─────────────────┐    spawns     ┌─────────────────┐    executes   ┌─────────────────┐
│     claude      │ ────────────► │       qa        │ ────────────► │     qms.py      │
│  (orchestrator) │   agentId:    │   (subagent)    │   --user qa   │     (CLI)       │
│                 │   abc123      │                 │               │                 │
│                 │               │                 │               │                 │
│ KNOWS: qa is    │               │ KNOWS: "I am    │               │ KNOWS: only     │
│ agent abc123    │               │ qa" from prompt │               │ --user arg      │
└─────────────────┘               └─────────────────┘               └─────────────────┘
```

**What each component actually knows:**

| Component | Knows | Does Not Know |
|-----------|-------|---------------|
| Orchestrator (claude) | Which subagent_type it spawned; the returned agentId | — |
| Spawned agent (qa) | Its role identity from prompt content | Its own agentId; no cryptographic proof |
| CLI (qms.py) | The `--user` argument string | Who is actually calling; no verification |

**The gap:** There is no way for the CLI to verify that the entity claiming to be `qa` is actually the QA agent spawned by the orchestrator. The CLI must trust the `--user` flag.

### 1.2 Why This Matters

The QMS permission model (SOP-001 Section 4.2) assumes identity is meaningful:

- Only QA can assign reviewers
- Only assigned reviewers can approve
- Initiators cannot approve their own documents

If identity is unverifiable, these controls are social/behavioral rather than technical.

**Current mitigations:**
- Honor system + audit trail (forensic analysis after the fact)
- Agent prompts that emphasize role boundaries
- Orchestrator discipline (not impersonating other agents)

---

## 2. Three Related Problems

### 2.1 Problem A: Orchestrator Influence on Review

From idea tracker (2026-01-08):

> When spawning QA or reviewer agents, Claude (the orchestrator) should not dictate specific review criteria in the task prompt.

**Violation pattern:**
```
Task(subagent_type="qa", prompt="Review CR-017. Verify it includes EI-1, EI-2, EI-3...")
```

**Preferred pattern:**
```
Task(subagent_type="qa", prompt="Review CR-017 for pre-approval per SOP-002.")
```

**Why this matters:** If the orchestrator prescribes review criteria, the reviewer becomes a rubber stamp executing the orchestrator's checklist rather than applying independent judgment derived from SOPs.

### 2.2 Problem B: Agents Don't Know Valid Actions

Agents must internalize the workflow state machine from SOPs to know what actions they can take. This creates:
- Cognitive load (agents must remember workflow states)
- Error potential (agents may attempt invalid transitions)
- No guardrails (CLI rejects invalid actions after the fact)

### 2.3 Problem C: No Identity Verification

The CLI cannot verify caller identity. Any agent can claim any identity.

---

## 3. Multi-Step Prompts: Concept

From idea tracker (2026-01-05):

> Instead of agents needing to know the full workflow state machine, the CLI provides contextual "what can I do next?" guidance after each action.

**Example output after QA submits a review:**

```
✓ Review submitted for CR-012 (RECOMMEND)

Document state: IN_PRE_REVIEW → PRE_REVIEWED

Available actions for user 'qa':
  [1] Route for approval:  qms route CR-012 --approval
  [2] Assign additional reviewers:  qms assign CR-012 --assignees <users>
  [3] Check document status:  qms status CR-012

Select action or press Enter to exit:
```

**Benefits:**
1. **Reduces workflow errors** — Agents can't easily take invalid actions
2. **Self-documenting** — Agents learn valid transitions by using the system
3. **Implicit identity feedback** — Prompts show actions valid for *this* user only
4. **Replaces memorization** — No need to internalize SOP workflow diagrams

---

## 4. How Multi-Step Prompts Address the Problems

### 4.1 Problem A (Orchestrator Influence): Partial Mitigation

Multi-step prompts don't directly address orchestrator influence on review content. However, they reinforce that:
- The CLI (not the orchestrator) defines valid actions
- Review criteria should come from SOPs, not task prompts

**Remaining gap:** The orchestrator can still influence *what* the reviewer looks for. This requires behavioral/procedural controls (e.g., CLAUDE.md directive, SOP-007).

### 4.2 Problem B (Unknown Valid Actions): Direct Solution

Multi-step prompts directly solve this by:
- Presenting only valid actions for current state
- Presenting only actions valid for current user
- Eliminating guesswork

### 4.3 Problem C (Identity Verification): Partial Mitigation

Multi-step prompts provide **mismatch detection**:
- CLI outputs the claimed `--user` prominently
- Orchestrator can notice if output doesn't match expected subagent
- Creates audit trail of claimed identity + action

**Not a technical solution:** Still relies on honest `--user` claims. True verification would require Claude Code infrastructure changes.

---

## 5. Implementation Considerations

### 5.1 CLI Changes

**Current flow:**
```
qms --user qa review CR-012 --recommend --comment "..."
→ Success message
→ Exit
```

**Proposed flow (interactive mode):**
```
qms --user qa review CR-012 --recommend --comment "..."
→ Success message
→ State transition display
→ Available next actions (filtered by user permissions + document state)
→ Prompt for selection OR exit
```

**Non-interactive mode (for scripting/testing):**
```
qms --user qa review CR-012 --recommend --comment "..." --no-interactive
→ Success message only
```

### 5.2 State-Action Mapping

The CLI needs a mapping of:
- (document_status, user_group) → valid_actions

This largely exists implicitly in the current permission checks. Making it explicit enables:
- Action menu generation
- Better error messages ("You cannot X because document is in state Y")
- Workflow visualization

### 5.3 Agent Prompt Changes

If the CLI becomes interactive, agent prompts may need adjustment:
- Agents should use menu selections when available
- Fallback to direct commands when needed
- Handle the interactive prompt gracefully

---

## 6. Complementary Controls

Multi-step prompts are one piece. Other controls to consider:

### 6.1 Behavioral Directive in CLAUDE.md

Add to orchestrator instructions:
```
When spawning reviewer agents, do not prescribe specific review criteria.
Provide context (what the CR is about, history) but not checklists.
Reviewers derive criteria from SOPs and their domain expertise.
```

### 6.2 SOP-007: Agent Orchestration

Formalize rules for:
- Spawning subagents
- Identity propagation
- Agent-to-agent communication boundaries
- What context can/cannot be passed in task prompts

### 6.3 Identity Verification (Infrastructure Dependent)

Long-term possibilities (require Claude Code changes):
- Environment variable: `CLAUDE_AGENT_TYPE` set by Claude Code
- Session token injection: Verifiable token passed to spawned agents
- Registry pattern: Orchestrator writes agentId→identity mapping; CLI queries

---

## 7. Design Decisions (from discussion)

### 7.1 Multi-Step Prompts: Interactive Mode

**Decision:** Interactive (blocking) mode preferred.

The CLI will present available actions and wait for selection before exiting. This creates a guided workflow where agents are led through valid transitions.

**Consideration:** We need to verify that agents can handle interactive prompts gracefully. If blocking input proves problematic, we can fall back to suggestion-only with an `--interactive` flag.

### 7.2 Identity Verification: Behavioral Controls + Future Token System

**Current approach:** Behavioral controls are sufficient for now (honor system + audit trail + prompt discipline).

**Future direction:** Explore a password/token system where:
- A randomly-generated token is assigned to each agent at spawn time
- The agent must present this token when calling the CLI
- The CLI verifies the token matches the expected identity

**The puzzle:** How to inject the token so that:
- The spawned agent can see/use it
- The orchestrator (and other agents) cannot see it

---

## 8. The Token Injection Puzzle

### 8.1 The Core Challenge

When the orchestrator spawns a subagent via `Task()`, everything in the prompt and everything in the response is visible to the orchestrator. There's no "private channel" to the spawned agent.

```
Orchestrator                    Claude Code                     Subagent
     │                              │                              │
     │ Task(prompt="...")           │                              │
     │─────────────────────────────►│                              │
     │                              │ spawns agent, passes prompt  │
     │                              │─────────────────────────────►│
     │                              │                              │
     │                              │◄─────────────────────────────│
     │                              │        agent output          │
     │◄─────────────────────────────│                              │
     │     returns output           │                              │
```

If Claude Code generates a token and includes it in the agent's context, the orchestrator sees the output. If the token is in the prompt, the orchestrator wrote the prompt.

### 8.2 Potential Solutions

#### Option A: Environment Variable Injection (Infrastructure Change)

Claude Code injects an environment variable that:
- Is set for the spawned agent's process
- Is NOT reported back to the orchestrator
- Can be read by the CLI via `os.environ`

```python
# In spawned agent's environment (set by Claude Code)
CLAUDE_AGENT_TOKEN=abc123xyz
CLAUDE_AGENT_TYPE=qa

# CLI reads this
def verify_caller():
    token = os.environ.get('CLAUDE_AGENT_TOKEN')
    agent_type = os.environ.get('CLAUDE_AGENT_TYPE')
    # Verify token maps to agent_type in some registry
```

**Pros:** Clean separation; orchestrator can't intercept
**Cons:** Requires Claude Code changes; we don't control that infrastructure

#### Option B: Encrypted Token in Prompt (Cryptographic)

1. QMS generates a keypair at initialization
2. When orchestrator spawns agent, CLI generates a token and encrypts it with the agent's public key
3. Spawned agent decrypts with its private key
4. Spawned agent includes decrypted token in CLI calls

**Problem:** Where does the agent get its private key? Same visibility problem.

#### Option C: Time-Based One-Time Password (TOTP)

1. Each agent type has a shared secret with the CLI
2. Agent generates TOTP from shared secret + current time
3. CLI verifies TOTP

**Problem:** Where is the shared secret stored? If in the agent prompt (readable by orchestrator), it's compromised.

#### Option D: CLI-Generated Challenge-Response

1. CLI generates a challenge when agent first identifies itself
2. Challenge is specific to (agent_type, session, timestamp)
3. Agent must respond correctly (but how does it know the correct response without a shared secret?)

**Problem:** Still needs a secret that only the agent knows.

#### Option E: Trust the Orchestrator, Verify in Audit

Accept that the orchestrator could impersonate agents, but:
1. All actions are logged with claimed identity
2. Post-hoc audit can detect anomalies
3. Orchestrator is instructed (via CLAUDE.md) not to impersonate

This is the current approach. The "improvement" would be making impersonation *harder* even if not impossible.

### 8.3 A Hybrid Approach: Spawn-Time Token Registry

**Concept:** The orchestrator cooperates in token generation but cannot predict tokens.

1. Orchestrator calls `Task()` to spawn agent
2. Claude Code generates a random token internally
3. Claude Code writes `{agentId: token}` to a registry file
4. Claude Code injects token into spawned agent's context (visible only to agent)
5. CLI reads registry file to verify token → agentId → expected agent_type

**The "visible only to agent" step is the unsolved puzzle.**

One possibility: Claude Code could inject the token via a mechanism that's processed *before* returning output to the orchestrator (e.g., agent receives token, uses it, but token itself is stripped from output).

### 8.4 Practical Path Forward

Given infrastructure constraints:

1. **Immediate:** Behavioral controls (CLAUDE.md directive, audit trail)
2. **Near-term:** Multi-step prompts that display claimed identity prominently (mismatch detection)
3. **Exploratory:** Document the token injection puzzle and share with Claude Code team as a feature request

---

## 9. Open Questions

1. **Agent handling of interactive prompts:** Can agents reliably interact with blocking CLI prompts, or will they hang/timeout?

2. **Scope of behavioral directive:** Should orchestrator-to-reviewer communication rules be in CLAUDE.md, SOP-007, or both?

3. **Agent reuse interaction:** How do multi-step prompts interact with agent resumption? (Agent context includes prior CLI outputs.)

4. **State machine formalization:** Should the workflow state machine be extracted into a declarative format (e.g., YAML) that both SOPs and CLI consume?

5. **Token injection feature request:** Is this worth pursuing with the Claude Code team?

---

## 10. The Governance Architecture

### 10.1 Three-Layer Model

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: Procedures (SOPs)                                     │
│  ───────────────────────────                                    │
│  SOP-007: Agent Orchestration                                   │
│    - Rules for spawning agents                                  │
│    - Identity management                                        │
│    - Communication boundaries                                   │
│    - What context can/cannot be passed                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ enforced/reminded by
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2: Tooling (QMS CLI)                                     │
│  ──────────────────────────                                     │
│  - Multi-step prompts guide valid actions                       │
│  - Injected reminders about SOP requirements                    │
│  - Interactive mode for workflow navigation                     │
│  - Identity display for mismatch detection                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ governed by (eventually)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 3: SDLC Governance (RS/RTM)                                  │
│  ─────────────────────────────────                                  │
│  SDLC-QMS-RS: Requirements Specification for QMS CLI                │
│    - REQ-CLI-xxx: Multi-step prompt requirements                    │
│    - REQ-CLI-xxx: When/what prompts appear                          │
│    - REQ-CLI-xxx: Identity verification requirements                │
│                                                                     │
│  SDLC-QMS-RTM: Traceability for QMS CLI                             │
│    - Maps requirements to implementation                            │
│    - Verification evidence for prompt behavior                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 10.2 Evolution Path

| Phase | What | Outcome |
|-------|------|---------|
| **Current** | Behavioral controls in CLAUDE.md; ad-hoc CLI prompts | Functional but informal |
| **Phase 1** | Create SOP-007 defining agent orchestration rules | Procedures formalized |
| **Phase 2** | Update CLI to inject prompts aligned with SOP-007 | Tooling enforces procedures |
| **Phase 3** | Bring QMS CLI under SDLC governance (RS, RTM) | Code is formally governed |
| **Future** | Token injection if/when Claude Code supports it | Technical identity verification |

### 10.3 Key Insight

The CLI becomes the **enforcement layer** between procedures (SOPs) and agents. Agents don't need to memorize SOPs because the CLI:
1. Tells them what actions are valid (multi-step prompts)
2. Reminds them of procedural requirements (injected prompts)
3. Makes their claimed identity visible (mismatch detection)

Eventually, this CLI behavior itself is governed by an RS, creating full traceability from procedure → code → verification.

### 10.4 SOPs as Behavioral Baselines (Critical Clarification)

**SOPs set floors, not ceilings.** The RS/CLI can always *exceed* SOP requirements. There is no GMP rule against additional strictness.

#### Two Types of SOP Requirements:

**1. Behavioral requirements** — Define what agents must/must not do
- Example: "The orchestrator shall not prescribe specific review criteria when spawning reviewer agents"
- Followable immediately through behavioral discipline
- No tooling required; compliance is a choice
- SOP can be approved without any infrastructure changes

**2. Tooling-dependent requirements** — Mandate use of specific infrastructure
- Example: "Documents shall be created using `qms create` with official templates"
- Requires the referenced tooling to exist
- Cannot be followed until infrastructure is in place
- Must wait for infrastructure to be qualified before SOP approval

#### Implication for SOP-007:

Write SOP-007 in **behavioral terms**:
- "The orchestrator shall not prescribe review criteria" ✓
- "The CLI shall remind the orchestrator..." ✗ (tooling-dependent)

This allows SOP-007 to be approved immediately. The CLI can later *exceed* these requirements by adding reminders, guardrails, and interactive prompts—but these are enhancements governed by the RS, not SOP mandates.

#### The Relationship:

```
SOP-007 (Behavioral Baseline)
  │
  │ "Orchestrator shall not prescribe review criteria"
  │  → Followable today through discipline
  │
  ▼
SDLC-QMS-RS (Can Exceed Baseline)
  │
  │ "REQ-CLI-042: CLI shall display reminder about review criteria rules"
  │  → Enhancement; makes compliance easier
  │  → Not required by SOP; adds additional strictness
  │
  ▼
QMS CLI Implementation
  │
  │ Actually implements the reminder
  │  → Governed by RS, verified by RTM
```

**Key principle:** SOPs define what agents must do. Tooling makes compliance easier but is not a prerequisite for SOP approval when the SOP is written in behavioral terms.

---

## 11. Token Injection: Feature Request (Tabled)

### 11.1 The Problem

Agent identity is established by prompt injection only. The CLI cannot verify caller identity.

### 11.2 Desired Capability

A mechanism where Claude Code assigns a token to each spawned agent that:
- Is visible to the spawned agent
- Is NOT visible to the orchestrator
- Can be verified by CLI tools

### 11.3 Status

Tabled for now. Behavioral controls (SOP-007, CLI prompts, audit trail) are sufficient. Document as feature request for Claude Code team if identity verification becomes critical.

---

## 12. Proposed Next Steps

| Priority | Item | Complexity |
|----------|------|------------|
| 1 | Draft SOP-007: Agent Orchestration | Medium |
| 2 | Implement multi-step prompts in CLI (interactive mode) | Medium |
| 3 | Align CLI prompts/reminders with SOP-007 | Medium |
| 4 | Document token injection as feature request | Low |
| 5 | (Future) Bring QMS CLI under SDLC governance | High |

---

*Document finalized: Session-2026-01-09-001*
