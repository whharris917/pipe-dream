---
title: 'Trial: Redirect agent reading directives from SOPs to QMS-Docs'
revision_summary: Initial draft
---

# CR-101: Trial: Redirect agent reading directives from SOPs to QMS-Docs

## 1. Purpose

Replace SOP reading directives in CLAUDE.md and agent definition files with equivalent QMS-Docs references. This is a reversible trial to validate that the QMS-Docs educational layer provides sufficient context for agent operation without SOPs. SOPs remain on disk and are not retired.

---

## 2. Scope

### 2.1 Context

Session-2026-02-22-005 established the three-strand authority model: CLI (mechanism) + Templates (structure) + QMS-Policy.md (judgment). SOPs were identified as scaffolding that tried to be all three strands simultaneously, causing bloat and drift. QMS-Docs was built as the replacement educational layer.

This CR implements the first step: redirecting reading directives. It does NOT retire SOPs.

- **Parent Document:** None (independent improvement from Session-2026-02-22-005 design discussion)

### 2.2 Changes Summary

Update reading directives in CLAUDE.md (Session Start Checklist, Compact Instructions, Permissions) and all 6 agent definition files (qa, bu, tu_ui, tu_scene, tu_sim, tu_sketch) to point at QMS-Docs instead of QMS/SOP/.

### 2.3 Files Affected

- `CLAUDE.md` — Redirect Step 4 reading list, update compact instructions and permissions reference
- `.claude/agents/qa.md` — Replace Required Reading section, update file path reference
- `.claude/agents/bu.md` — Replace Required Reading section
- `.claude/agents/tu_ui.md` — Replace Required Reading section
- `.claude/agents/tu_scene.md` — Replace Required Reading section
- `.claude/agents/tu_sim.md` — Replace Required Reading section
- `.claude/agents/tu_sketch.md` — Replace Required Reading section

---

## 3. Current State

CLAUDE.md Step 4 directs Claude to "Read all Standard Operating Procedures in `QMS/SOP/`" at session start. All 6 agent definition files direct agents to read SOP-001 and SOP-002 before any review or approval action. The compact instructions reference SOP content as "available on disk via `QMS/SOP/`". The permissions section cites "SOP-001 Section 4.2".

---

## 4. Proposed State

CLAUDE.md Step 4 directs Claude to read a curated QMS-Docs reading list (QMS-Policy.md, START_HERE.md, QMS-Glossary.md). Agent definition files direct agents to read role-appropriate QMS-Docs resources instead of SOPs. Compact instructions reference QMS-Docs. Permissions section references QMS-Policy.md.

SOPs remain on disk unchanged. If agent behavior degrades, directives can be reverted.

---

## 5. Change Description

### 5.1 CLAUDE.md — Session Start Checklist (Step 4)

Replace:
```
### 4. Read All SOPs

Read all Standard Operating Procedures in `QMS/SOP/`.
```

With:
```
### 4. Read QMS Documentation

Read the following QMS documents:

1. `QMS-Docs/QMS-Policy.md` — Core policy decisions and judgment criteria
2. `QMS-Docs/START_HERE.md` — Decision tree for common workflows
3. `QMS-Docs/QMS-Glossary.md` — Term definitions

These three documents provide the context needed for QMS operations. For deeper reference on specific topics, consult the numbered guides in `QMS-Docs/` and type references in `QMS-Docs/types/`.
```

### 5.2 CLAUDE.md — Compact Instructions

Replace:
```
- SOP content (available on disk via `QMS/SOP/`)
```

With:
```
- QMS-Docs content (available on disk via `QMS-Docs/`)
```

### 5.3 CLAUDE.md — Permissions

Replace:
```
**Your permissions (per SOP-001 Section 4.2):**
```

With:
```
**Your permissions (per QMS-Policy.md Section 2):**
```

### 5.4 Agent Definitions — QA (qa.md)

Replace Required Reading section with:

```markdown
## Required Reading

Before any review or approval action, read:

1. **QMS-Policy.md** (`QMS-Docs/QMS-Policy.md`) — Core policy decisions and judgment criteria
   - Review independence, evidence standards, scope integrity
   - When to investigate, when to create child documents

2. **Quality Unit Handbook** (`QMS-Docs/guides/quality-unit-handbook.md`) — Your operational playbook
   - Reviewer assignment guidance
   - Pre/post review checklists by document type
   - Approval guidance and common scenarios

3. **QMS-Glossary.md** (`QMS-Docs/QMS-Glossary.md`) — Term definitions
```

Update description frontmatter from "Enforces QMS procedural compliance per SOP-001" to "Enforces QMS procedural compliance per QMS-Policy.md".

Update "Your Role" section header from "per SOP-001 Section 4.2" to "per QMS-Policy.md Section 2".

Update file path reference on line 181. Replace:

```
**To read documents:** Use the Read tool directly on file paths (e.g., `QMS/SOP/SOP-001.md` or `QMS/SOP/SOP-001-draft.md`).
```

With:

```
**To read documents:** Use the Read tool directly on file paths (e.g., `QMS-Docs/QMS-Policy.md` or `QMS/CR/CR-101/CR-101.md`).
```

### 5.5 Agent Definitions — BU (bu.md)

Replace Required Reading section with:

```markdown
## Required Reading

Before reviewing any change, read:

1. **QMS-Policy.md** (`QMS-Docs/QMS-Policy.md`) — Core policy decisions and judgment criteria
   - Evidence standards, scope integrity

2. **Review Guide** (`QMS-Docs/guides/review-guide.md`) — How to conduct reviews
   - Review process and what to look for

3. **QMS-Glossary.md** (`QMS-Docs/QMS-Glossary.md`) — Term definitions
```

### 5.6 Agent Definitions — TU agents (tu_ui, tu_scene, tu_sim, tu_sketch)

Replace Required Reading section in all four files with:

```markdown
## Required Reading

Before reviewing any change, read:

1. **QMS-Policy.md** (`QMS-Docs/QMS-Policy.md`) — Core policy decisions and judgment criteria
   - Review independence, evidence standards, scope integrity

2. **Review Guide** (`QMS-Docs/guides/review-guide.md`) — How to conduct reviews
   - Review process and what to look for

3. **QMS-Glossary.md** (`QMS-Docs/QMS-Glossary.md`) — Term definitions
```

---

## 6. Justification

- SOPs contain ~2,700 lines across 7 files. Agents consume this at session start (Claude) or before each review action (subagents). Most content is redundant with CLI behavior or template structure.
- QMS-Docs + QMS-Policy.md provide the same educational context in a more focused, role-appropriate form.
- The three-strand authority model (CLI + Templates + Policy) makes SOPs structurally redundant — they were scaffolding that is no longer load-bearing.
- This is a reversible trial. SOPs remain on disk. If agent behavior degrades, the pointers revert.

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `CLAUDE.md` | Modify | Redirect Step 4, compact instructions, permissions reference |
| `.claude/agents/qa.md` | Modify | Replace Required Reading, update description/role/path references |
| `.claude/agents/bu.md` | Modify | Replace Required Reading |
| `.claude/agents/tu_ui.md` | Modify | Replace Required Reading |
| `.claude/agents/tu_scene.md` | Modify | Replace Required Reading |
| `.claude/agents/tu_sim.md` | Modify | Replace Required Reading |
| `.claude/agents/tu_sketch.md` | Modify | Replace Required Reading |

### 7.2 Documents Affected

None. No QMS-controlled documents are modified.

### 7.3 Other Impacts

- Agent context window usage decreases significantly (agents no longer consume ~2,700 lines of SOP text)
- QA agents get role-specific guidance (quality-unit-handbook) instead of generic SOPs
- If QMS-Docs content is insufficient, agents may make procedural errors that SOPs would have prevented. Mitigation: SOPs remain on disk and can be re-pointed in a single commit.

---

## 8. Testing Summary

This is a document-only CR affecting agent configuration files. Verification is observational:

- Spawn a QA agent and confirm it reads QMS-Docs instead of SOPs
- Spawn a TU agent and confirm it reads QMS-Docs instead of SOPs
- Verify Claude's session start reads QMS-Docs instead of SOPs
- Monitor agent behavior over subsequent sessions for procedural drift

---

## 9. Implementation Plan

### 9.1 Phase 1: CLAUDE.md Updates

1. Edit CLAUDE.md Step 4 (Session Start Checklist)
2. Edit CLAUDE.md Compact Instructions
3. Edit CLAUDE.md Permissions reference

### 9.2 Phase 2: Agent Definition Updates

1. Edit `.claude/agents/qa.md` — Required Reading, description, role header, file path reference
2. Edit `.claude/agents/bu.md` — Required Reading
3. Edit `.claude/agents/tu_ui.md` — Required Reading
4. Edit `.claude/agents/tu_scene.md` — Required Reading
5. Edit `.claude/agents/tu_sim.md` — Required Reading
6. Edit `.claude/agents/tu_sketch.md` — Required Reading

### 9.3 Phase 3: Verification

1. Confirm all 7 files updated correctly
2. Grep for residual SOP reading directives to ensure none were missed

---

## 10. Execution

| EI | Task Description | VR | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|----|-------------------|--------------|---------------------|
| EI-1 | Pre-execution commit | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | Phase 1: CLAUDE.md updates (Step 4, Compact Instructions, Permissions) | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Phase 2: Agent definition updates (all 6 files) | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-4 | Phase 3: Verification — grep for residual SOP reading directives | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-5 | Post-execution commit | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

---

### Execution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| [COMMENT] | [PERFORMER] - [DATE] |

---

## 11. Execution Summary

[EXECUTION_SUMMARY]

---

## 12. References

- **QMS-Policy.md** — Core policy document (replacement for SOP policy content)
- **QMS-Docs/** — Educational documentation suite (replacement for SOP educational content)
- **Session-2026-02-22-005** — Design session establishing three-strand authority model

---

**END OF DOCUMENT**
