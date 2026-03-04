# Project State

*Last updated: Session-2026-03-03-001*

---

## 1. Where We Are Now

**DocuBuilder paradigm established; genesis sandbox authorized.** Session 2026-03-03-001 produced a major design pivot: the Kneat eVal-inspired DocuBuilder model replaces the graph-based interaction engine design with a table-primitive approach. The table is the universal interactive primitive. Column types (ID, Design, Recorded Value, Signature, Witness, Issue, Choice List, Prerequisite, Calculated, Row Number) define the full spectrum from authoring to execution. Three property namespaces (system, user, execution), composable importable sections, prerequisite-based ordering, and cross-document references provide the complete framework. CR-108 authorizes a genesis sandbox (`docu-builder/`, git-ignored) for rapid exploratory prototyping.

**CR-107 and CR-106 remain in DRAFT.** The interaction engine portion of CR-107 is superseded by the DocuBuilder paradigm. CR-107's non-interaction content (universal source files, Jinja2 render engine, living schema authority, spectrum model) remains valid. How CR-107 evolves in light of DocuBuilder is TBD — it may be revised, split, or partially superseded once the sandbox yields results.

64 CRs CLOSED (CR-042 through CR-105, plus CR-091-ADD-001). 5 INVs CLOSED (INV-010 through INV-014). 687 tests, SDLC-QMS-RS v22.0, SDLC-QMS-RTM v27.0, SDLC-CQ-RS v2.0, SDLC-CQ-RTM v2.0.

---

## 2. The Arc

**Foundation through Quality Manual** (Feb 1-24, CR-042 through CR-105). See previous PROJECT_STATE versions for detailed arc.

**Unified Document Lifecycle & System Governance** (Feb 25-26, CR-107 + CR-106 — design complete). Grand unification of three document architectures into single Jinja2-based system. CR-106 builds system governance on top.

**Interaction Architecture Exploration** (Feb 27 - Mar 2, design sessions). Multiple competing approaches explored: frontmatter-driven interaction, three-artifact separation, graph-based engine with Python dataclasses. No decisions finalized.

**DocuBuilder Paradigm Shift** (Mar 3, Session-2026-03-03-001). Kneat eVal-inspired pivot. Table as universal interactive primitive. Column types replace graph nodes. Prerequisites replace graph edges. Composable sections replace zone markers. Property namespaces replace schema declarations. Work Instructions replace sequential prompt workflows. CR-108 authorizes genesis sandbox.

---

## 3. What's Built

### SDLC Document State

| Document | Version | Tests |
|----------|---------|-------|
| SDLC-QMS-RS | v22.0 EFFECTIVE | 143 requirements |
| SDLC-QMS-RTM | v27.0 EFFECTIVE | 687 tests, qualified commit 918984d |
| SDLC-CQ-RS | v2.0 EFFECTIVE | 6 requirements |
| SDLC-CQ-RTM | v2.0 EFFECTIVE | Inspection-based, qualified commit d3c34e5 |
| Qualified Baseline | CLI-18.0 | qms-cli commit 309f217 (main) |

### Controlled Document State

| Document | Version |
|----------|---------|
| SOP-001 | v21.0 EFFECTIVE |
| SOP-002 | v16.0 EFFECTIVE |
| SOP-003 | v3.0 EFFECTIVE |
| SOP-004 | v9.0 EFFECTIVE |
| SOP-005 | v7.0 EFFECTIVE |
| SOP-006 | v5.0 EFFECTIVE |
| SOP-007 | v2.0 EFFECTIVE |
| TEMPLATE-CR | v10.0 EFFECTIVE |
| TEMPLATE-VAR | v3.0 EFFECTIVE |
| TEMPLATE-ADD | v2.0 EFFECTIVE |
| TEMPLATE-VR | v3.0 EFFECTIVE |

---

## 4. Open QMS Documents

| Document | Status | Context |
|----------|--------|---------|
| CR-108 | DRAFT v0.1 | DocuBuilder Genesis Sandbox. Exploratory prototyping, no required outcomes. Ready to route. |
| CR-107 | DRAFT v0.1 (content v1.0) | Unified Document Lifecycle. Non-interaction content valid; interaction design superseded by DocuBuilder paradigm. Future TBD. |
| CR-106 | DRAFT v0.1 (content v0.4) | System Governance. Depends on CR-107. Unchanged. |
| CR-091-ADD-001-VAR-001 | PRE_APPROVED v1.0 | Type 2 VAR. VR title bug + SOP-004/TEMPLATE-VR alignment gap. |
| CR-001 | IN_EXECUTION v1.0 | Legacy. Candidate for cancellation. |
| CR-020 | DRAFT v0.1 | Legacy test document. Candidate for cancellation. |
| INV-002 | IN_EXECUTION v1.0 | Legacy — SOP-005 missing revision summary. |
| INV-003 | PRE_REVIEWED v0.1 | Legacy — CR-012 workflow deficiencies. |
| INV-004 | IN_EXECUTION v1.0 | Legacy — CR-019 template loading. |
| INV-005 | IN_EXECUTION v1.0 | Legacy — locked section edit during execution. |
| INV-006 | IN_EXECUTION v1.0 | Legacy — incorrect code modification target. |
| CR-036-VAR-002 | IN_EXECUTION v1.0 | Legacy — documentation drift. |
| CR-036-VAR-004 | IN_EXECUTION v1.0 | Legacy — partial test coverage analysis. |

---

## 5. Forward Plan

### Immediate: Route CR-108 → Begin Sandbox

1. Route CR-108 for review/approval
2. Set up `docu-builder/` sandbox (`.gitignore` entry, directory structure)
3. Write informal RS from `authoring-and-executing-controlled-documents.md` principles
4. Begin Python prototyping — interactive REPL exploration of core data model

### CR-107 / CR-106: On Hold

CR-107's interaction engine design is superseded by DocuBuilder. The non-interaction content (universal source files, Jinja2 render engine, spectrum model, living schema authority) remains valid. How these CRs evolve depends on what the DocuBuilder sandbox reveals. Options: revise CR-107 to incorporate DocuBuilder, split into separate CRs, or supersede entirely.

### DocuBuilder Design Artifacts (Session 2026-03-03-001)

| Artifact | Location | Status |
|----------|----------|--------|
| Core principles | `.claude/sessions/Session-2026-03-03-001/authoring-and-executing-controlled-documents.md` | Active — 10 sections (I-X) covering principles, data model, and implementation strategy |
| Document DNA | `.claude/sessions/Session-2026-03-03-001/document_dna.json` | Active — prototype JSON data model (see below) |
| Workspace mockup | `prompt.txt` (project root) | Active — rendering concept showing agent-facing view |
| Interaction design plan | `.claude/sessions/Session-2026-03-03-001/interaction-design-plan.md` | Superseded by DocuBuilder |
| TEMPLATE-INTERACT.j2 | `.claude/sessions/Session-2026-03-03-001/` | Superseded |
| TEMPLATE-CR.j2 | `.claude/sessions/Session-2026-03-03-001/` | Superseded |

**Document DNA** (`document_dna.json`) is the prototype JSON structure for DocuBuilder documents. Key design decisions: named tables for stable cross-references, `column_order` array separating schema from rendering, sparse row values (only populated columns present), `::` separator for hierarchical prerequisite paths (e.g., `section_1::table_name::row`), hierarchical locking at section/element/row levels, and string-keyed sections for reorder-safe references. The workspace mockup (`prompt.txt`) demonstrates how this structure renders for agents. Together, these two artifacts define the starting point for sandbox prototyping.

---

## 6. Code Review Status

Comprehensive audit Session-2026-02-14-001. 27 findings, 8 fixed (CR-077 + CR-088).

### Open — Critical (1)
| ID | Finding | Bundle |
|----|---------|--------|
| C3 | Container runs as root | Agent Hub Robustness |

### Open — High (2)
| ID | Finding | Bundle |
|----|---------|--------|
| H4 | No Hub shutdown on GUI exit | Agent Hub Robustness |
| H6 | Agent action errors not surfaced to user | GUI Polish |

### Open — Medium/Low/Note (13)
See Session-2026-02-14 notes. Grouped into Agent Hub Robustness, GUI Polish, and Identity Hardening bundles.

---

## 7. Backlog

### Ready (no blockers)

| Item | Effort | Source |
|------|--------|--------|
| Fix CLI title metadata propagation in interactive engine | Small | CR-091-ADD-001-VAR-001 |
| Align SOP-004 Section 9C.4 with TEMPLATE-VR v5 | Small | CR-091-ADD-001-VAR-001 |
| Govern checkin.py bug fix (commit `532e630`) via CR | Trivial | INV-012 |
| Interactive document write protection (REQ-INT-023) | Medium | Session-2026-02-21-001 |
| Fix stale help text in `qms.py:154` | Trivial | To-do 2026-01-17 |
| Remove stdio transport option from MCP servers | Small | To-do 2026-02-16 |
| Delete `.QMS-Docs/` | Trivial | CR-103 |
| Propagate Quality Manual cleanup from workshop | Medium | Session-2026-02-24-003 |
| Standardize metadata timestamps to UTC ISO 8601 | Small | Session-2026-02-26-001 |

### Bundleable

**Identity & Access Hardening** (~1 session) — proxy header validation, Git MCP access control
**Agent Hub Robustness** (~1-2 sessions) — C3, H4, M6, M8, M9, M10
**GUI Polish** (~1-2 sessions) — H6, M3, M4, M5, M7, L3, L4, L5, L6

### Deferred

| Item | Rationale |
|------|-----------|
| Remove EFFECTIVE status / rename to APPROVED | High disruption, low value |
| Metadata injection into viewable rendition | No current pain point |
| Consolidate SDLC namespaces into system registry | Depends on CR-106 |

---

## 8. Gaps & Risks

**checkin.py bug fix needs governance.** Commit `532e630` fixed an `UnboundLocalError` in interactive checkin. Needs a proper CR.

**Legacy QMS debt.** Nine open documents from early iterations. Bulk cleanup recommended.

**Container security.** C3 (root user) remains the last critical code review finding.

**Hub/GUI test coverage.** Hub 42 tests, GUI 0%. QMS CLI well-tested at 687.

**Claude Code deny rules non-functional.** Platform bug. PreToolUse hooks provide actual enforcement.

**SOP-004/TEMPLATE-VR alignment gap.** Documented in CR-091-ADD-001-VAR-001, corrective CR pending.

**CR-107 interaction design superseded.** The graph-based interaction engine design explored across four sessions is superseded by the DocuBuilder paradigm. CR-107's non-interaction content remains valid but the CR needs revision once DocuBuilder prototyping yields results.
