# Session 2026-02-10-004: CR-075 Execution, INV-011 Investigation, UAT

## Overview

This session executed CR-075 (Single-Authority MCP + HTTP Hardening), discovered an incomplete EI during UAT preparation, opened INV-011 to investigate, executed two of three CAPAs (including deploying the single-authority architecture), and ran a full UAT with 7/7 PASS.

## What Was Done

### 1. CR-075 Execution (all 6 EIs Pass)

| EI | Description | Key Artifacts |
|----|-------------|---------------|
| EI-1 | Test environment setup | Branch `cr-075-single-authority-mcp`, 392-test baseline |
| EI-2 | RS update (6 requirement revisions) | SDLC-QMS-RS v11.0 EFFECTIVE |
| EI-3 | Code implementation | `resolve_identity()` header-based mode selection, commit `486bc0b` |
| EI-4 | Qualification | 393 tests, CI green |
| EI-5 | RTM update | SDLC-QMS-RTM v13.0 EFFECTIVE (1 correction cycle) |
| EI-6 | Merge to main | PR #11 merged (`386ff44`), submodule updated |

CR-075 post-review/post-approval completed, CR CLOSED (v2.0).

### 2. Deviation Discovered

During UAT preparation, discovered that CR-075 EI-3's `.mcp.json` transport change was never executed. The initiator (claude) had rationalized the omission as "operational" in the execution comments, and QA post-review did not catch it.

### 3. INV-011 Created and Partially Executed

- **Root causes:** (1) QA post-review prompt too vague to enforce EI cross-referencing, (2) no post-closure correction mechanism in QMS
- **CAPA-001 (Corrective):** Updated `.mcp.json` from stdio to HTTP transport. Host MCP now connects to `localhost:8000/mcp`. Verified working. **PASS.**
- **CAPA-002 (Preventive):** Strengthened QA CR post-review prompt in `cr.yaml` — replaced vague "describe what was done" with explicit cross-reference check. Commit `94345fa` in qms-cli. **PASS.**
- **CAPA-003 (Preventive):** Implement ADD (Addendum) document type. **Deferred to future session** — requires child CR.
- INV-011 remains IN_EXECUTION pending CAPA-003.

### 4. UAT — 7/7 PASS

| Test | Description | Result | Notes |
|------|-------------|--------|-------|
| P1-T1 | Host trusted mode via HTTP | PASS | Was stdio, now HTTP — regression verified |
| P1-T2 | Container enforced mode | PASS | `qa` registered as instance `1647e18c` |
| P1-T4 | HTTP without header | PASS | Was VULNERABILITY — now explicit trusted mode, no warning |
| P2-T1 | Container locks identity | PASS | Lock active for `qa` |
| P2-T2 | Cross-transport collision | PASS | Was NOT TESTABLE — trusted-mode `user=qa` rejected while container holds lock |
| P2-T3 | Duplicate container blocked | PASS | agent-hub rejects second QA launch |
| P2-T4 | Different identities coexist | PASS | `qa` + `tu_ui` concurrent without collision |

### 5. UAT Observation: Silent Identity Override (P1-T3)

tu_ui container passed various `user` parameters (`tu_sim`, `""`, `"not_a_real_username"`, omitted). In all cases, enforced mode silently overrode to `tu_ui`. The agent received no indication its parameter was ignored and drew false conclusions about system behavior (e.g., "the inbox endpoint doesn't validate usernames"). This is a confusion risk for any operation with side effects. Added to TO_DO_LIST.md for future investigation.

## Key Decisions

- CAPA-003 (ADD document type) deferred to future session — too large for current session
- `.mcp.json` change requires MCP HTTP server to be running for host QMS operations (`start-mcp-server.sh --background`)

## Artifacts

| Artifact | Version/Ref |
|----------|-------------|
| CR-075 | CLOSED v2.0 |
| INV-011 | IN_EXECUTION v1.2 (CAPA-003 pending) |
| SDLC-QMS-RS | EFFECTIVE v11.0 |
| SDLC-QMS-RTM | EFFECTIVE v13.0 |
| qms-cli main | `94345fa` (CAPA-002 prompt change) |
| pipe-dream main | `ae393e9` |
| CI run | https://github.com/whharris917/qms-cli/actions/runs/21886071685 |

## QA Agent

- Agent ID: `ae2c12c` — reused across all review/approval cycles

## Open Items

- **INV-011 CAPA-003:** Create child CR for ADD (Addendum) document type — next session
- **INV-011 closure:** Blocked on CAPA-003 completion
- **Identity mismatch visibility:** Surface enforced-mode override to callers (TO_DO_LIST.md)
- **Defensive fallback investigation:** Is `resolve_identity()` fallback still needed? (TO_DO_LIST.md)

## Continuation Notes

This session spanned multiple context windows. Started as CR-075 execution (plan from Session 2026-02-10-003), discovered the `.mcp.json` deviation post-closure, pivoted to INV-011, executed two CAPAs, restarted Claude Code for MCP config change, and ran full UAT. The Identity Management Initiative (Phases 1, 2, 2.5) is now fully deployed and verified. INV-011 remains open for CAPA-003.
