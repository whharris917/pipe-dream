# Project State

*Last updated: Session-2026-02-24-001*

---

## 1. Where We Are Now

**claude-qms starter repo and hardened qms init complete.** CR-104 created `whharris917/claude-qms` as the canonical distribution repo and redesigned `qms init` with marker-based root detection, confirmation prompt, and `--yes` flag. New CQ namespace with RS/RTM. 688 tests, SDLC-QMS-RS v21.0, SDLC-QMS-RTM v26.0.

63 CRs CLOSED (CR-042 through CR-104, plus CR-091-ADD-001). 5 INVs CLOSED (INV-010 through INV-014).

---

## 2. The Arc

**Foundation (Feb 1-5, CR-042 through CR-055).** Remote MCP transport, container infrastructure, streamable-HTTP, process improvements from INV-007 through INV-010.

**Multi-Agent Infrastructure (Feb 6-7, CR-056 through CR-063).** Unified launcher, Agent Hub, port-based discovery, agent permissions.

**Feature Build (Feb 8-9, CR-064 through CR-072).** PTY manager, WebSocket endpoint, Tauri GUI, demand-driven bootstrap.

**Identity and Security (Feb 9-10, CR-073 through CR-076).** Four-phase identity system, 396 tests, RS v12.0/RTM v14.0.

**Audit, Hardening, and Verification (Feb 14, CR-077 through CR-081).** Code review (27 findings, 4 fixed), Phase A integration testing (2 containerized agents, full QMS lifecycle), GUI terminal hardening.

**QMS Process Evolution (Feb 15-16, CR-082 through CR-088).** ADD document type. Merge gate. Integration verification mandate. Pre/post-execution commits. Rollback procedures. CLI quality and workflow enforcement. Agent Hub observability.

**Testing & Evidence Framework (Feb 16-18, CR-089).** VR document type — CLI support (424 tests), SDLC docs (RS v15.0, RTM v19.0), TEMPLATE-VR, 4 SOP updates, 3 template updates.

**Deficiency Resolution (Feb 19, CR-090).** MCP health checks switched from HTTP POST to TCP connect.

**Interaction System (Feb 19-21, CR-091).** Template parser, source data model, interaction engine, compilation engine, CLI command, MCP tool. 22 requirements (REQ-INT-001 through REQ-INT-022), 611 tests. SOP-004 Section 11, TEMPLATE-VR v3 (interactive).

**Governance Failure Investigation (Feb 21, INV-012).** CR-091 code never propagated to production submodule. CR-092 (corrective: submodule merge) and CR-093 (preventive: SOP-005 v6.0, SOP-002 v14.0) both CLOSED.

**Compilation Defects (Feb 21, CR-094).** Four defects in compiled VR output fixed: duplicate frontmatter, broken tables, guidance leak, no visual distinction. TEMPLATE-VR v4 with `@end-prompt`. 643 tests.

**Attachment Lifecycle + Compiler Refinements (Feb 22, CR-095).** Attachment document classification, cascade close, terminal state checkout guard. TEMPLATE-VR v5, auto-metadata, block rendering, step subsection numbering. 673 tests.

**Compaction Resilience (Feb 22, CR-096).** 5-layer defense-in-depth: Compact Instructions, post-compaction recovery protocol, incremental session notes, PreCompact hook, SessionStart recovery hook. Config/docs only.

**VR Compilation Rendering Fixes (Feb 22, CR-097).** Step subsection labels, blockquoted instructions, improved auto-commit messages. 673 tests, SDLC-QMS-RTM v23.0.

**Template Divergence Investigation (Feb 22, INV-013).** Systematic drift between QMS-controlled and seed templates across all 9 pairs. CR-098 aligned all templates. CR-099 added dual-template awareness to TEMPLATE-CR and SOP-002.

**SDLC Governance Bypass Investigation (Feb 22, INV-014).** CR-098 committed directly to qms-cli main bypassing SOP-005 execution branch workflow. Discovered all Claude Code deny rules are non-functional (platform bug). CR-100 tightened SOP-005 (dev location, PR mandate, file scope), TEMPLATE-CR (explicit locations, PR enforcement), SOP-002 (PR verification in QA checklist). PreToolUse hook as enforcement. Seed aligned via PR #18.

**VR Evidence Remediation (Feb 22, CR-091-ADD-001).** Replaced inadequate freehand CR-091-VR-001 with interactive VR authored through the system it verifies. 4 verification steps (progress tracking, compilation, amendment workflow, sequential enforcement), all Pass. Type 2 VAR (VAR-001) documents empty title field (CLI bug) and SOP-004/TEMPLATE-VR alignment gap.

**Documentation Architecture & Bootstrap Overhaul (Feb 22-23, CR-101, CR-102).** Three-strand authority model: CLI (mechanism) + Templates (structure) + QMS-Policy.md (judgment). Built QMS-Docs suite, genericized for portability (zero instance-specific references). CR-101 redirected agent reading directives from SOPs to QMS-Docs. CR-102 overhauled qms-cli bootstrap: seeds QMS-Docs, generic TU agent, starter CLAUDE.md, write guard hook; removed SOP seeds; added `tu` user. 677 tests, RS v19.0, RTM v24.0.

**Docs/Manual Directory Split (Feb 23, CR-103).** Separated qms-cli documentation into `docs/` (7 new software doc files) and `manual/` (38 files from `seed/docs/`). Removed `seed_docs()` from init — projects no longer get a `QMS-Docs/` copy. `pipe-dream/QMS-Docs/` untouched (deferred to follow-up CR). 678 tests, RS v20.0, RTM v25.0.

**Distribution & Init Hardening (Feb 24, CR-104).** Created `whharris917/claude-qms` as canonical starter repo (marker file + qms-cli submodule). Redesigned `qms init`: marker-based root detection, confirmation prompt, `--yes` flag, `--root` marker placement. New CQ SDLC namespace (SDLC-CQ-RS v1.0, SDLC-CQ-RTM v1.0). 688 tests, RS v21.0, RTM v26.0.

---

## 3. What's Built

### SDLC Document State

| Document | Version | Tests |
|----------|---------|-------|
| SDLC-QMS-RS | v21.0 EFFECTIVE | 143 requirements |
| SDLC-QMS-RTM | v26.0 EFFECTIVE | 688 tests, qualified commit 1761b0a |
| SDLC-CQ-RS | v1.0 EFFECTIVE | 5 requirements |
| SDLC-CQ-RTM | v1.0 EFFECTIVE | Inspection-based, qualified commit 6b22747 |
| Qualified Baseline | CLI-17.0 | qms-cli commit f6f82db (main) |

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
| CR-091-ADD-001-VAR-001 | PRE_APPROVED v1.0 | Type 2 VAR. Documents VR title propagation bug and SOP-004/TEMPLATE-VR alignment gap. Awaiting future corrective CR. |
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

### Interactive Engine Redesign (design discussion complete)

A design discussion explored decoupling the interaction system into three independent artifacts. Design documents captured in Session-2026-02-22-004:

- `interactive-engine-redesign.md` — Full architecture: workflow specs (YAML/Python), Jinja2 rendering templates, template inheritance hierarchy, two-layer (authoring + process) architecture, workflow language progression (Levels 1-4)
- `cr-prompt-path-example.md` — Worked example: interactive CR authoring with 8 phases, variant-based EI table selection, auto-populated development controls

**Key insight:** Prompt sequence follows author's thinking (what -> why -> how -> verify -> plan), while compiled document follows reader's structure (Sections 1-12). The `.source.json` is the clean interface between them.

**Implementation approach:** Build for Level 3 (Python declarative), start at Level 2 (YAML + Jinja2). Design engine interfaces against an abstract workflow API so the backend can evolve independently.

### Phase B: Git MCP Access Control (~1 session)
- Add identity resolution to `agent-hub/git_mcp/server.py`
- Allowlist: `["claude", "lead"]` — other agents blocked

### Phase D: GUI Enhancement (~2-3 sessions)
- D.1: MCP health monitoring
- D.2: QMS status panel
- D.3: Notification injection API
- D.4: Identity status visibility

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
| Align SOP-004 Section 9C.4 with TEMPLATE-VR v5 (remove Signature requirement) | Small | CR-091-ADD-001-VAR-001 |
| Govern checkin.py bug fix (commit `532e630`) via CR | Trivial | INV-012 / Session-2026-02-21-002 |
| Interactive document write protection (REQ-INT-023) | Medium | Session-2026-02-21-001 defect |
| Fix stale help text in `qms.py:154` ("QA/lead only" -> "administrators only") | Trivial | To-do 2026-01-17 |
| Remove stdio transport option from both MCP servers | Small | To-do 2026-02-16 |
| Stop tracking total counts of tests/REQs across documents | Small | To-do 2026-02-16 |
| START_HERE.md elevator pitch | Small | Session-2026-02-23-001 design discussion |
| Migrate pipe-dream/QMS-Docs/ to read from qms-cli/manual/ submodule | Medium | CR-103 deferred scope |

### Bundleable (natural CR groupings)

**Interactive Engine v2** (~2-3 sessions) — Three-artifact separation (workflow spec, rendering template, source data), Jinja2 compilation, template inheritance, CR/VAR/ADD interactive authoring. See design docs in Session-2026-02-22-004.
**Identity & Access Hardening** (~1 session) — proxy header validation (L7), Git MCP access control
**Agent Hub Robustness** (~1-2 sessions) — C3, H4, M6, M8, M9, M10
**GUI Polish** (~1-2 sessions) — H6, M3, M4, M5, M7, L3, L4, L5, L6
**Process Refinement** (~1-2 sessions) — commit column in EI table
**QMS Workflow** — proceduralize adding new documents, comments visibility restriction during active workflows

### Discussion / Design Needed

| Item | Context |
|------|---------|
| Automate RTM generation | RTM is large, repetitive, error-prone to maintain manually |
| Improve RTM readability | One test per line with row-spanning REQ IDs |
| Formal SOP retirement | Trial live (CR-101). Monitor agent behavior before deciding. |
| Production/test environment isolation | Largely addressed by INV-014 (PreToolUse hook, SOP-005 v7.0). Remaining: programmatic separation beyond hooks. |
| Subconscious agent | Design discussion complete; implementation design pending |

### Deferred

| Item | Rationale |
|------|-----------|
| Remove EFFECTIVE status / rename to APPROVED | High disruption, low value |
| Metadata injection into viewable rendition | No current pain point |

---

## 8. Gaps & Risks

**checkin.py bug fix needs governance.** Commit `532e630` fixed an `UnboundLocalError` in interactive checkin. Needs a proper CR for traceability.

**Legacy QMS debt.** Nine open documents from early iterations. Bulk cleanup recommended.

**Container security.** C3 (root user) remains the last critical code review finding.

**Hub/GUI test coverage.** Hub 42 tests, GUI 0%. QMS CLI well-tested at 688.

**Claude Code deny rules non-functional.** All deny rules in settings.local.json are silently ignored due to a known platform bug (GitHub #8961, #6699, #6631). PreToolUse hooks provide actual enforcement. Deny rules retained as defense-in-depth. Note: CR-104 removed qms-cli/flow-state deny rules since they were false-positive blocking .test-env/ writes; hook provides the actual enforcement.

**SOP-004/TEMPLATE-VR alignment gap.** SOP-004 Section 9C.4 still lists "Signature" as required VR content, but TEMPLATE-VR v5 (approved under CR-098) removed it. Documented in CR-091-ADD-001-VAR-001, corrective CR pending.
