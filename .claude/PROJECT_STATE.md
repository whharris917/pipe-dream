# Project State

*Last updated: Session-2026-02-22-002*

---

## 1. Where We Are Now

**CR-097 CLOSED.** VR compilation rendering fixes — three defects in compiled VR step subsections: added labels (Instructions/Expected/Actual/Outcome), switched instructions from bold to blockquote, improved auto-commit message format. 673 tests, SDLC-QMS-RTM v23.0.

55 CRs CLOSED (CR-042 through CR-097).

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

---

## 3. What's Built

### SDLC Document State

| Document | Version | Tests |
|----------|---------|-------|
| SDLC-QMS-RS | v18.0 EFFECTIVE | 139 requirements |
| SDLC-QMS-RTM | v23.0 EFFECTIVE | 673 tests, qualified commit d73f154 |
| Qualified Baseline | CLI-14.0 | qms-cli commit d73f154 (main: 6867966) |

### Controlled Document State

| Document | Version |
|----------|---------|
| SOP-001 | v21.0 EFFECTIVE |
| SOP-002 | v14.0 EFFECTIVE |
| SOP-003 | v3.0 EFFECTIVE |
| SOP-004 | v9.0 EFFECTIVE |
| SOP-005 | v6.0 EFFECTIVE |
| SOP-006 | v5.0 EFFECTIVE |
| SOP-007 | v2.0 EFFECTIVE |
| TEMPLATE-CR | v8.0 EFFECTIVE |
| TEMPLATE-VAR | v3.0 EFFECTIVE |
| TEMPLATE-ADD | v2.0 EFFECTIVE |
| TEMPLATE-VR | v2.0 EFFECTIVE |

---

## 4. Open QMS Documents

| Document | Status | Context |
|----------|--------|---------|
| CR-091-ADD-001 | IN_EXECUTION v1.0 | VR evidence remediation. Unblocked now that submodule is updated. |
| CR-091-VR-001 | IN_EXECUTION v1.0 | Inadequate — freehand, not interactive. To be superseded by CR-091-ADD-001-VR-001. |
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

### Next: Resume CR-091-ADD-001

CR-091-ADD-001 is IN_EXECUTION. Author CR-091-ADD-001-VR-001 via `qms interact`, complete remaining EIs, route for post-review.

### Interaction System Phase 2+ (future)
- **Phase 3:** Expand to executable documents (TEMPLATE-CR, TEMPLATE-VAR, TEMPLATE-ADD)
- **Phase 4+:** Non-executable documents, intent decomposition layer

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
| Govern checkin.py bug fix (commit `532e630`) via CR | Trivial | INV-012 / Session-2026-02-21-002 |
| Interactive document write protection (REQ-INT-023) | Medium | Session-2026-02-21-001 defect |
| Fix stale help text in `qms.py:154` ("QA/lead only" -> "administrators only") | Trivial | To-do 2026-01-17 |
| Remove stdio transport option from both MCP servers | Small | To-do 2026-02-16 |
| Stop tracking total counts of tests/REQs across documents | Small | To-do 2026-02-16 |

### Bundleable (natural CR groupings)

**Identity & Access Hardening** (~1 session) — proxy header validation (L7), Git MCP access control
**Agent Hub Robustness** (~1-2 sessions) — C3, H4, M6, M8, M9, M10
**GUI Polish** (~1-2 sessions) — H6, M3, M4, M5, M7, L3, L4, L5, L6
**Process Refinement** (~1-2 sessions) — branch protection/merge strategy in SOPs, commit column in EI table
**QMS Workflow** — proceduralize adding new documents, comments visibility restriction during active workflows

### Discussion / Design Needed

| Item | Context |
|------|---------|
| Automate RTM generation | RTM is large, repetitive, error-prone to maintain manually |
| Improve RTM readability | One test per line with row-spanning REQ IDs |
| Simplify SOPs to behavioral baselines | Review for tooling-dependent language |
| Production/test environment isolation | Programmatic separation between production and test environments |
| Subconscious agent | Design discussion complete; implementation design pending |

### Deferred

| Item | Rationale |
|------|-----------|
| Remove EFFECTIVE status / rename to APPROVED | High disruption, low value |
| Metadata injection into viewable rendition | No current pain point |

---

## 8. Gaps & Risks

**checkin.py bug fix needs governance.** Commit `532e630` fixed an `UnboundLocalError` in interactive checkin. Needs a proper CR for traceability.

**CR-091-VR-001 inadequacy.** Freehand VR bypassed the interaction system. Remediation via CR-091-ADD-001 in progress (unblocked).

**Legacy QMS debt.** Nine open documents from early iterations. Bulk cleanup recommended.

**Container security.** C3 (root user) remains the last critical code review finding.

**Hub/GUI test coverage.** Hub 42 tests, GUI 0%. QMS CLI well-tested at 673.
