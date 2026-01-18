# Agent Orchestration Concepts

**Date:** 2026-01-04
**Session:** 009
**Status:** Discussion notes (not implemented)

---

## Overview

Discussion of architectural improvements to agent orchestration, focusing on reliability, efficiency, and parallelism.

---

## Concept 1: Decoupling Orchestration from Procedural Knowledge

### Problem

When spawning agents (e.g., QA), Claude currently provides detailed prompts explaining the workflow, CLI commands, and SOP requirements. This is brittle because:
- Claude's knowledge may be stale relative to current SOPs
- Procedural changes don't automatically propagate to agent prompts
- Token-inefficient (repeating SOP content in every spawn)

### Solution: Three-Layer Architecture

**Layer 1: Structured Inbox Messages**

Route actions generate machine-readable inbox entries:
```json
{
  "doc_id": "CR-009",
  "action": "POST_REVIEW",
  "routed_by": "claude",
  "sop_reference": "SOP-002#7.3"
}
```

**Layer 2: Agent Responsibility Manifests**

Each agent role has a manifest (e.g., `.claude/agents/qa.md`) defining:
- Triggers (what inbox actions activate this agent)
- On-activation behavior (read inbox, read referenced SOP)
- Available commands (derived from SOP-001 permissions)

**Layer 3: Activation Hooks**

Programmatic hooks on QMS commands (e.g., `route --review`) that:
- Format standardized inbox entries
- Optionally auto-resume the assigned agent

### Model C: Manifest as Behavioral Layer

The chosen decomposition:
- **SOPs define WHAT** must happen (policy, requirements)
- **Manifests define HOW** agents operationalize it (tools, sequence, response format)

Manifests don't duplicate SOP content; they translate requirements into agent behavior. This creates a natural testing boundary.

---

## Concept 2: Multiple Agent Instances

### Use Case

Parallelism — if QA has multiple inbox items, spawn qa-1, qa-2, etc. to handle them concurrently.

### Design Decision: Ephemeral Instances

Agents are fundamentally ephemeral (created fresh each session). Therefore:
- No long-term memory persistence
- No cross-instance learning infrastructure
- "Learning" belongs in the QMS, not the agent

**The agent doesn't learn. The QMS learns.** Edge cases become INVs or CRs, codified in SOPs, available to all future instances.

### Two-Layer Identity Model

**Identity Layer (QMS-visible):**
- There is one "qa" role
- Documents are "approved by qa" (never "qa-1")
- Audit trail knows nothing about instances

**Orchestration Layer (internal):**
- Instances (qa-1, qa-2) are implementation details
- Pooled and reused within a session for efficiency
- Spawning is expensive (~15-60s); resuming is cheap

### Instance Pool Management

Claude tracks internally:

| Instance | Status | Current Task |
|----------|--------|--------------|
| qa-1 | idle | — |
| qa-2 | busy | CR-012 |

- New task arrives → resume idle instance or spawn new
- Task completes → mark instance idle
- Session ends → pool is gone (inbox persists pending work)

---

## Implementation Notes

- Agent manifests should live in `.claude/agents/` (outside QMS, versioned with code)
- Manifests can evolve without CR overhead (operational config, not policy)
- Hooks should be context-aware and generate standardized inbox messages
- Claude's spawn prompt reduces to "Check your inbox" — details come from manifest + SOP

---

## Open Items

- Exact manifest format and location
- Hook implementation for auto-activation
- Inbox message schema
- Pool management within Claude's session state

---

**End of Notes**
