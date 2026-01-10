# SOP-007: Agent Orchestration — Draft Outline

*Session-2026-01-09-001*

---

## Design Principles

1. **Behavioral, not tooling-dependent** — Requirements describe what agents must/must not do, not what the CLI must do
2. **Immediately followable** — Every requirement can be followed through discipline alone
3. **Floor, not ceiling** — CLI/RS can exceed these requirements with additional guardrails

---

## Proposed Structure

### 1. Purpose

Establish procedures for spawning, managing, and coordinating AI agents within the QMS. Ensure separation of duties, reviewer independence, and auditable agent interactions.

### 2. Scope

Applies to:
- The orchestrating agent (claude)
- All spawned subagents (qa, tu_*, bu)
- Agent-to-agent communications
- Agent interactions with the QMS CLI

Out of scope:
- Human user interactions (covered by SOP-001)
- Document workflows themselves (covered by SOP-001, SOP-002)

### 3. Definitions

| Term | Definition |
|------|------------|
| **Orchestrator** | The primary agent (claude) that spawns and coordinates subagents |
| **Subagent** | A spawned agent with a specific role (qa, tu_ui, etc.) |
| **Task Prompt** | The instruction provided when spawning a subagent |
| **Context** | Information passed to a subagent about the work to be performed |
| **Review Independence** | The principle that reviewers derive criteria from SOPs, not orchestrator instructions |

### 4. Agent Roles and Permissions

*Reference SOP-001 Section 4 for user groups and permission matrix.*

#### 4.1 Orchestrator Responsibilities

The orchestrator (claude) shall:
- Spawn subagents appropriate to the task
- Provide sufficient context for subagents to perform their work
- Respect subagent independence in review/approval decisions
- Maintain accurate records of agent interactions

The orchestrator shall NOT:
- Impersonate other agents when interacting with the QMS CLI
- Override or circumvent subagent decisions
- Spawn agents for the purpose of bypassing review requirements

#### 4.2 Subagent Responsibilities

Subagents shall:
- Operate within their designated role and permissions
- Derive review/approval criteria from governing SOPs
- Exercise independent judgment in their domain
- Report anomalies or concerns to the orchestrator

Subagents shall NOT:
- Claim an identity other than their assigned role
- Defer to orchestrator preferences over SOP requirements
- Perform actions outside their permission scope

### 5. Spawning Subagents

#### 5.1 When to Spawn

The orchestrator shall spawn subagents when:
- QMS workflow requires action by a specific role (e.g., QA review)
- Domain expertise is needed beyond orchestrator capabilities
- Separation of duties requires independent judgment

#### 5.2 Agent Selection

The orchestrator shall select the appropriate agent type based on:
- The action required (review, approval, technical assessment)
- The domain affected (UI, simulation, sketch, scene)
- SOP requirements for the workflow stage

#### 5.3 Agent Reuse

Within a session, the orchestrator shall:
- Reuse existing agents via resume when the same role is needed again
- Track agent IDs for continuity throughout the session
- NOT spawn fresh agents of the same type unless explicitly directed by the Lead

*Rationale:* There is no need to "refresh context" by spawning new agents. If context refresh is needed, the Lead will direct it explicitly.

### 6. Communication Boundaries

#### 6.1 Principle: Documents Speak for Themselves

The orchestrator shall provide **minimal context** when spawning subagents. Documents, SOPs, and agent definition files provide the necessary context for subagents to perform their work.

#### 6.2 Permitted Context

When spawning a subagent, the orchestrator may provide:
- Document identification (CR-XXX, SOP-XXX)
- Current workflow state (status, version)
- Task type (review, approval, technical assessment)

#### 6.3 Prohibited Context

When spawning a subagent, the orchestrator shall NOT provide:
- Summaries or interpretations of document content
- Specific review criteria or checklists
- Desired review outcomes ("approve if X, Y, Z are present")
- Instructions that pre-determine reviewer judgment
- Pressure or urgency that could compromise review quality
- Background information that the document itself should contain

#### 6.4 Context Sources

Subagents shall derive context from:
1. **The document under review** — Contains all relevant content for the task
2. **QMS-controlled content** — SOPs, templates, SDLC documents (RS, RTM, etc.)
3. **Agent definition files** — Define role, responsibilities, and behavioral directives
4. **CLAUDE.md** — Technical architecture guide
5. **Relevant code** — Source code within scope of the document being reviewed

If a subagent lacks sufficient context to perform its task, this indicates a deficiency in the document or SOPs, not a need for orchestrator explanation.

#### 6.5 Rationale

Review independence ensures that:
- Reviewers apply SOP requirements consistently
- The orchestrator cannot rubber-stamp its own work
- Quality decisions are based on document merit, not orchestrator preference
- Deficiencies in documents are surfaced rather than papered over with verbal context

### 7. Identity and Integrity

#### 7.1 Identity Claims

Each agent shall:
- Use only its assigned identity when interacting with the QMS CLI
- Include its identity in the `--user` flag accurately
- Not claim permissions beyond its role

#### 7.2 Audit Trail

All agent actions are recorded in the QMS audit trail. Agents shall:
- Accept that their actions are logged
- Not attempt to manipulate or circumvent audit logging
- Report any suspected audit trail anomalies

#### 7.3 Prohibited Behaviors

Agents shall NOT:
- Use scripting or tools to bypass CLI permission checks
- Directly manipulate files in `QMS/.meta/` or `QMS/.audit/`
- Craft workarounds that undermine document control
- Access files outside the project directory without authorization

*Reference: Prohibited Behavior sections in CLAUDE.md and agent prompts*

### 8. Conflict Resolution and Enforcement

#### 8.1 Disagreement with Orchestrator

If a subagent disagrees with orchestrator guidance:
- The subagent shall prioritize SOP requirements over orchestrator preferences
- The subagent may document concerns in review comments
- The subagent shall not be overridden on compliance matters

#### 8.2 Escalation

Issues that cannot be resolved between agents shall be:
- Documented in the relevant QMS document (review comments, execution notes)
- Escalated to the Lead (human) for resolution

#### 8.3 Enforcement

Violations of this SOP are addressed through:
- **Primary mechanism:** Audit trail review — all agent actions are logged and can be reviewed
- **Escalation:** Investigation (INV) only if the Lead determines one is warranted

*Rationale:* The audit trail provides sufficient visibility into agent behavior. Formal investigation is reserved for significant or systemic issues at the Lead's discretion.

### 9. References

- SOP-001: Quality Management System - Document Control
- SOP-002: Change Control
- CLAUDE.md: Orchestrator operational instructions
- Agent prompt files (`.claude/agents/*.md`)

---

## Design Decisions (Resolved)

| Question | Decision |
|----------|----------|
| Agent reuse | **Required.** Orchestrator shall reuse agents; no "context refresh" rationale for spawning fresh. Lead directs if refresh needed. |
| Context granularity | **Minimal.** Documents speak for themselves. Only doc ID, status, and task type permitted. |
| Enforcement | **Audit trail sufficient.** Investigation only if Lead determines one is warranted. |
| Work Instructions | **Deferred.** WIs to be drafted alongside SDLC-QMS-RS. |
| Scope | **Implicit.** Applies to this project's agent orchestration; no need to specify "Claude Code." |

---

## Mapping to CLI Enhancements (Future RS)

*These are NOT part of SOP-007. They are potential RS requirements that would exceed the SOP baseline.*

| SOP-007 Behavioral Requirement | Potential RS Enhancement |
|-------------------------------|-------------------------|
| "Orchestrator shall not prescribe review criteria" | CLI reminds orchestrator of this rule when spawning reviewers |
| "Agents shall use only assigned identity" | CLI displays claimed identity prominently for mismatch detection |
| "Orchestrator should reuse agents" | CLI or hook reminds orchestrator of active agent IDs |
| "Subagents shall derive criteria from SOPs" | CLI injects SOP references into subagent context |

---

*End of outline — ready for discussion*
