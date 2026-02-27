---
title: 'System Governance: registration, checkout/checkin, and qualification gate
  for governed submodules'
revision_summary: v0.4 — Aligned with CR-107 grand unification redesign. Replaced
  all qms set references with frontmatter editing (CR-107 eliminated qms set). Updated
  template variable syntax from {%user:...%} to Jinja2 {{ user.foo }}. Updated CR-107
  prerequisite description and references.
---

# CR-106: System Governance: registration, checkout/checkin, and qualification gate for governed submodules

## 1. Purpose

Extend the QMS CLI to treat governed submodules ("systems") as first-class entities with registration, exclusive ownership (via the existing `responsible_user` pattern), a qualification gate on checkin, and versioned releases. This is the foundational step toward the Guided Agent Orchestration vision: agents cannot modify a governed system without an authorizing CR, exclusive checkout, and satisfied qualification conditions — all enforced programmatically by the CLI.

---

## 2. Scope

### 2.1 Context

Independent improvement driven by the Guided Agent Orchestration design discussion (Session-2026-02-25-001). Currently, execution branches, merge gates, and system releases are managed by convention (CLAUDE.md instructions, SOP-005 prose, write-guard hooks). This CR makes the CLI the enforcement mechanism.

- **Parent Document:** None
- **Prerequisite:** CR-107 (Unified Document Lifecycle) — provides universal source files, Jinja2 render engine, `user_properties` in metadata (populated from frontmatter at checkin), and template as living schema authority

### 2.2 Changes Summary

Add a `system` command group to the QMS CLI with five subcommands: `register`, `list`, `status`, `checkout`, and `checkin`. Register is a one-time, identity-only setup (submodule path, namespace, GitHub repo) — it establishes *what* a system is, not *whether* it's qualified. Qualification is driven by the RTM: user properties (`qualified_commit`, `traces_to_rs_version`, `qualified_version`) are set by editing the RTM source frontmatter and populated into `metadata.user_properties` at checkin (CR-107). When the RTM reaches EFFECTIVE, the system record's `qualified_version` and `qualified_commit` are updated — and if the system is not checked out (migration/baseline), `current_release` is also set to match. During active development (system checked out), system checkin is an atomic verify-merge-release operation: `check_qualification_gate()` verifies the evidence chain (CI passes at qualified commit, RTM traces to current RS), auto-discovers the open PR whose HEAD matches `qualified_commit`, merges it via GitHub API (`--no-ff`), and records `current_release` and `release_commit`. Add `target_systems` field to CR metadata. Add corresponding MCP tools.

### 2.3 Files Affected

- `qms-cli/commands/system.py` — New file: system governance commands
- `qms-cli/qms_system.py` — New file: system metadata read/write utilities, qualification gate
- `qms-cli/qms_config.py` — Add system permissions to PERMISSIONS dict
- `qms-cli/commands/create.py` — Add `target_systems` to CR initial metadata
- `qms-cli/workflow.py` — Add post-approval hook: when RTM reaches EFFECTIVE, update registered system's qualification fields (and `current_release` if system not checked out)
- `qms-cli/qms_paths.py` — Add system path helpers
- `qms-cli/qms_mcp/tools.py` — Add 5 new MCP tools
- `qms-cli/qms.py` — Import system commands module
- `qms-cli/tests/test_system.py` — New file: unit tests

---

## 3. Current State

The QMS CLI manages documents through their full lifecycle (create, checkout, checkin, route, review, approve) but has no awareness of governed submodules. Execution branches, merge gates, system releases, and write permissions to submodules are enforced by convention and hooks, not by the CLI. SDLC namespaces (QMS, CQ, FLOW) exist but only generate RS/RTM document types — they have no concept of the underlying system they govern.

---

## 4. Proposed State

Governed submodules are registered as "systems" in the QMS. Each system has metadata tracking two distinct states — **qualified** (proven ready) and **released** (actually deployed on main) — along with ownership. Agents use `qms system checkout` to acquire exclusive ownership (requiring an authorizing CR), then `qms system checkin` to release — but checkin is gated by a qualification check that verifies a complete evidence chain:

**qualified_commit ← RTM qualified_commit ← RTM traces_to_rs_version ← current EFFECTIVE RS ← CI passes**

The system lifecycle has a two-phase progression. RTM qualification metadata (`qualified_commit`, `traces_to_rs_version`, `qualified_version`) is set by editing the RTM source frontmatter while the document is checked out. At checkin, CR-107's unified lifecycle populates these values into `metadata.user_properties` and renders the source through Jinja2 — so `{{ user.qualified_commit }}` in the RTM body becomes a concrete commit hash in the rendered draft that reviewers inspect. Values can be updated incrementally across checkout/checkin cycles as they become known (e.g., `traces_to_rs_version` at the start of work, `qualified_commit` after CI passes). When the RTM reaches EFFECTIVE, the system record's `qualified_version` and `qualified_commit` are updated — the system is now "proven ready." If the system is not checked out (migration/baseline stamping), `current_release` is also set to match, completing the process in one step. If the system IS checked out (active development), `current_release` remains at the old value until system checkin. System checkin is an atomic verify-merge-release operation: it verifies the qualification gate, confirms the PR HEAD matches `qualified_commit` (closing the gap between qualification and merge), merges the PR via GitHub API (`--no-ff`), and records both `current_release` and `release_commit` (the merge commit hash). Between qualification and release, `qms system status` shows a clear "qualified but not yet released" state.

This design closes a critical gap: without the chain, an agent could leave RS/RTM untouched (still EFFECTIVE), gut the test suite, pass CI, and check in. With the chain, the RTM must contain the exact commit being released, which forces the RTM through a review cycle where reviewers verify the evidence.

System ownership uses the same `responsible_user` pattern as document checkout, generalizing the existing exclusivity mechanism rather than introducing a separate locking concept.

---

## 5. Change Description

### 5.1 System Registry

Systems are registered as metadata sidecar files at `QMS/.meta/SYSTEM/{system-id}.json`, following the same pattern as document metadata. Each system record includes:

- Identity: `system_id`, `submodule_path`, `sdlc_namespace`, `github_repo` (e.g., `whharris917/qms-cli`)
- Qualification: `qualified_version` (major.minor, e.g., `19.0`), `qualified_commit` — updated when RTM reaches EFFECTIVE
- Release: `current_release` (major.minor), `release_commit` (merge commit hash) — updated at system checkin, or at RTM EFFECTIVE if system is not checked out (migration sets `release_commit = qualified_commit`)
- Ownership: `responsible_user`, `authorizing_cr`, `checkout_timestamp` (UTC ISO 8601, e.g., `2026-02-26T14:30:45Z`)

This mirrors the document metadata pattern — `responsible_user` provides exclusive ownership, just as it does for documents.

### 5.2 Command: `qms system register NAME`

Administrator-only, one-time identity setup. Creates the system metadata sidecar with identity fields only — no qualification data. The register command's scope is deliberately minimal: it establishes *what* the system is, not *whether* it's qualified. Qualification is the RTM's responsibility (see Section 5.5).

Arguments: `--path`, `--namespace`, `--repo`, `--cr`. Requires `--cr CR-NNN`; the CR must be IN_EXECUTION and the user must be the CR's responsible_user. If a system with the given ID already exists, the command refuses — there is no re-registration.

Verifications at registration:

1. `submodule_path` — exists in `.gitmodules`
2. `sdlc_namespace` — registered in `qms.config.json`, and `SDLC-{NS}-RS` / `SDLC-{NS}-RTM` documents exist
3. `github_repo` — accessible via GitHub API (`gh api repos/{repo}`)

The system record is created with identity fields populated and qualification fields empty. The first RTM checkin with qualification frontmatter values populates the qualification state (via the post-approval hook when the RTM reaches EFFECTIVE).

**Future consolidation:** The register command is architecturally positioned to absorb SDLC namespace registration (currently managed separately in `qms.config.json`). This consolidation is out of scope for CR-106 but the command's design anticipates it.

Corrections to a registered system's identity metadata (e.g., repo migration, namespace change) would use an administrative fix mechanism. Implementing system-level `fix` is out of scope for this CR.

### 5.3 Command: `qms system list` / `qms system status NAME`

Query commands. `list` shows all registered systems with current state. `status` shows detailed info for one system including current owner, authorizing CR, and associated RS/RTM versions.

### 5.4 Command: `qms system checkout NAME --cr CR-NNN`

Acquires exclusive ownership of the system. The authorizing document must be a base CR (e.g., `CR-106`), not a child document (ADD, VAR). Modifying a governed submodule is a major undertaking requiring the full scope, justification, and impact assessment of the CR template. If a child document discovers that system changes are needed, the correct path is a new CR.

Preconditions: system has no `responsible_user` (or current user already owns it), document ID matches `CR-NNN` pattern (no child suffixes), CR is IN_EXECUTION, CR declares this system in `target_systems`, user is the CR's responsible_user. Sets `responsible_user` on the system metadata along with the authorizing CR and checkout date. Does NOT create the git branch — that remains agent work.

### 5.5 RTM Metadata Expansion and Qualification Propagation

The RTM is the qualification authority for its system. The RTM template (`TEMPLATE-RTM.md`) declares three user property keys that capture the evidence chain:

- `qualified_version`: the system version being qualified (e.g., `19.0`)
- `qualified_commit`: the commit hash at which CI verification was performed
- `traces_to_rs_version`: the RS version this RTM traces to

Under CR-107's unified lifecycle, these are frontmatter fields in the RTM source file. The author edits them directly — writing concrete values like `qualified_commit: abc123def` — and at checkin, CR-107 populates `metadata.user_properties` from the frontmatter. In the RTM source body, Jinja2 expressions like `{{ user.qualified_commit }}` reference these values and are rendered to concrete strings in the draft.

**Two-phase qualification lifecycle:**

1. **RTM checkin** — CR-107's Jinja2 render engine resolves expressions in the RTM source body using the metadata context (built from `user_properties` and system metadata), producing a rendered draft with concrete values for reviewer inspection. The source file preserves the Jinja2 expressions for future checkout cycles. Does NOT touch the system record. The RTM is now a *proposal* — "here is the evidence that version 19.0 at commit abc123 is qualified."

2. **RTM reaches EFFECTIVE** — when the RTM is approved (transitioning to EFFECTIVE status), the CLI updates the system record from the RTM's `user_properties`. The behavior depends on whether the system is currently checked out:

   - **System IS checked out** (active development): sets `qualified_version` and `qualified_commit` only. The system is "proven ready" but not yet "released" — `current_release` stays at the old value until system checkin (Section 5.6). `qms system status` shows: "qualified at 19.0, released at 18.0."

   - **System is NOT checked out** (migration/baseline): sets `qualified_version`, `qualified_commit`, `current_release` (= `qualified_version`), and `release_commit` (= `qualified_commit`). The system is both "proven ready" and "released" in one step — appropriate because the system is already deployed at this version.

   This is a targeted side effect in the approval workflow, triggered only for RTMs belonging to registered systems.

**Migration pathway:** For existing systems with EFFECTIVE RS/RTMs, the baseline is established by: (1) registering the system (identity only), (2) checking out the RTM, editing the source frontmatter to set `qualified_commit`, `traces_to_rs_version`, and `qualified_version` to the current known-good state, checking in, and (3) routing through review/approval. When the RTM reaches EFFECTIVE, the system record is fully populated — qualification fields AND `current_release` — because the system is not checked out. No system checkin is needed for migration.

### 5.6 Command: `qms system checkin NAME`

Atomic verify-merge-release operation. This is the second phase of the qualification lifecycle — it transitions a system from "qualified" to "released." No arguments are required beyond the system name — the CLI discovers the PR automatically.

The checkin command enforces a **qualification gate** (`check_qualification_gate()`) before proceeding — the same architectural pattern as `check_approval_gate()` for document routing. The gate verifies:

1. System has `qualified_version` and `qualified_commit` set (populated when RTM reached EFFECTIVE)
2. RTM for this system's SDLC namespace is EFFECTIVE
3. RTM metadata `traces_to_rs_version` matches the current EFFECTIVE RS version
4. CI passes at `qualified_commit` — verified via GitHub API (`gh api repos/{github_repo}/commits/{SHA}/check-runs`)
5. Exactly one open PR exists whose HEAD matches `qualified_commit` — discovered via GitHub API (`gh api repos/{github_repo}/pulls?state=open`, filtered by `.head.sha == qualified_commit`)

Gate check #5 closes a critical gap: without it, an agent could push additional unqualified commits to the execution branch after qualification, and those commits would be included in the merge. By discovering the PR via commit hash match, the CLI guarantees that exactly the qualified code — no more, no less — enters main. If no open PR matches, or if the PR HEAD has moved past `qualified_commit`, checkin is refused.

Every condition is programmatically verified from authoritative sources: system record, document metadata on disk, and GitHub API. If any condition is unmet, checkin is refused with a specific error identifying which link in the chain failed.

On success (all gate checks pass):
1. Merges the discovered PR via GitHub API (`gh api repos/{github_repo}/pulls/{pr}/merge` with `merge_method: merge` for `--no-ff` behavior)
2. Records `release_commit` from the merge response (the merge commit hash on main)
3. Sets `current_release` = `qualified_version`
4. Clears `responsible_user`, `authorizing_cr`, and `checkout_timestamp`

The agent creates the PR but does NOT merge it. The CLI performs the merge as part of the governed release process, ensuring that verification and merge are atomic — there is no window between "verified" and "merged" in which the branch could change.

### 5.7 Qualification Gate: `check_qualification_gate()`

A gate function in `qms_system.py`, following the same pattern as `check_approval_gate()` in `qms_meta.py`. Returns `(bool, str)` — success flag and error message. The gate is evaluated at system checkin time, not as a separate command. This keeps the qualification check atomic with the release.

The full verification chain at system checkin:

```
system checkin
  └─ system record: qualified_version set? qualified_commit set?
  └─ RTM status: EFFECTIVE?
  └─ RTM metadata: traces_to_rs_version == current EFFECTIVE RS version?
  └─ GitHub API: CI passes at qualified_commit?
  └─ GitHub API: open PR with HEAD == qualified_commit? (auto-discovered)
```

Every link is verified from an authoritative source. No self-reported values. The `qualified_commit` and `qualified_version` on the system record were set when the RTM reached EFFECTIVE (Section 5.5), having been reviewed and approved by human reviewers who verified the evidence.

The evidence chain guarantees that any system release has been through a full RTM review cycle with the correct commit and RS version. An agent cannot bypass this by leaving RS/RTM untouched — the RTM must contain the exact commit being released, which forces it to be updated, reviewed, and approved for every release.

The CI verification queries GitHub's check-runs API for the system's `qualified_commit` against the registered `github_repo`. All check runs must have `conclusion: success`. If the commit has no check runs, or any check run is pending/failed, the gate fails with a descriptive error.

### 5.8 CR Metadata Extension

Add `target_systems` field (list of strings) to CR metadata via `create_initial_meta()`. Populated during CR authoring. Validated during system checkout.

---

## 6. Justification

- Currently, nothing prevents an agent from modifying a governed system without authorization — enforcement relies on conventions and hooks that can be bypassed
- The qualification gate makes the merge gate programmatic: agents physically cannot check in a system until RS, RTM, and CI are all qualified
- System checkout uses the existing `responsible_user` pattern, preventing concurrent modification without introducing a new exclusivity mechanism
- This is the foundational infrastructure for the Guided Agent Orchestration vision, where the CLI enforces compliance programmatically rather than relying on agents to read and internalize procedures
- RTM Jinja2 expressions (via CR-107's unified render engine) eliminate manual maintenance of values the system already knows (commit hashes, release numbers, RS versions), reducing error and drift

---

## 7. Impact Assessment

### 7.1 Files Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `qms-cli/commands/system.py` | Create | System governance commands (register, list, status, checkout, checkin) |
| `qms-cli/qms_system.py` | Create | System metadata read/write utilities, `check_qualification_gate()` |
| `qms-cli/qms_config.py` | Modify | Add system permissions to PERMISSIONS dict |
| `qms-cli/commands/create.py` | Modify | Add `target_systems` to CR initial metadata |
| `qms-cli/workflow.py` | Modify | Add post-approval hook: when RTM reaches EFFECTIVE, update registered system's qualification fields (and `current_release` if not checked out) |
| `qms-cli/qms_paths.py` | Modify | Add system path helpers |
| `qms-cli/qms_mcp/tools.py` | Modify | Add 5 new MCP tools |
| `qms-cli/qms.py` | Modify | Import system commands module |
| `qms-cli/tests/test_system.py` | Create | Unit tests for system governance |

### 7.2 Documents Affected

| Document | Change Type | Description |
|----------|-------------|-------------|
| SDLC-QMS-RS | Modify | Add requirements for system governance commands |
| SDLC-QMS-RTM | Modify | Add verification evidence for new requirements |

### 7.3 Other Impacts

The approval workflow gains a targeted side effect: when an RTM belonging to a registered system reaches EFFECTIVE, the system record's `qualified_version` and `qualified_commit` are updated from RTM metadata; if the system is not checked out, `current_release` is also set to match (enabling migration without system checkin). Existing approval behavior is unchanged for all other document types and for RTMs not belonging to registered systems.

This CR depends on CR-107 (Unified Document Lifecycle) for the universal source file system, Jinja2 render engine, and `user_properties` in metadata (populated from frontmatter at checkin). CR-106 defines the RTM qualification fields and their system governance semantics; CR-107 provides the mechanism for declaring them in templates, setting them via frontmatter editing, and rendering them in documents via Jinja2.

### 7.4 Development Controls

This CR implements changes to qms-cli, a controlled submodule. Development follows established controls:

1. **Test environment isolation:** Development in `.test-env/` (local) or `/projects/` (containerized agents). No other locations are permitted.
2. **Branch isolation:** All development on branch `cr-106`
3. **Write protection:** `.claude/settings.local.json` blocks direct writes to `qms-cli/`
4. **Qualification required:** All new/modified requirements must have passing tests before merge
5. **CI verification:** Tests must pass on GitHub Actions for dev branch
6. **PR gate:** Changes merge to main only via PR after RS/RTM approval
7. **Submodule update:** Parent repo updates pointer only after PR merge

### 7.5 Qualified State Continuity

CR-107 (Document Source System) executes first and advances the qualified baseline. CR-106 builds on that state.

| Phase | main branch | RS/RTM Status | Qualified Release |
|-------|-------------|---------------|-------------------|
| Before CR (post-CR-107) | CR-107 merge commit | EFFECTIVE v23.0 / v28.0 | CLI-19 |
| During execution | Unchanged | DRAFT (checked out) | CLI-19 (unchanged) |
| Post-approval | Merged from cr-106 | EFFECTIVE v24.0 / v29.0 | CLI-20 |

---

## 8. Testing Summary

### Automated Verification

- System metadata CRUD operations (create, read, update, write)
- Register command: success, duplicate rejection, invalid namespace, invalid path, CR validation (not in-execution, wrong user, child document rejected), identity verification (submodule not in .gitmodules, namespace not in config, RS/RTM not found, github repo inaccessible)
- Checkout command: ownership acquisition, concurrent ownership rejection, CR validation (not in-execution, wrong target_systems, wrong user)
- System checkin command: qualification gate enforcement (all conditions met, individual condition failures), PR HEAD mismatch rejected, PR merge via GitHub API (mocked), `current_release` and `release_commit` set on success, ownership cleanup
- RTM user properties: `qualified_commit`, `traces_to_rs_version`, and `qualified_version` set via frontmatter editing, populated into `user_properties` at checkin (CR-107), read by qualification gate and post-approval hook
- RTM approval propagation: system record's `qualified_version` and `qualified_commit` updated from RTM `user_properties` when RTM reaches EFFECTIVE and namespace belongs to a registered system; `current_release` and `release_commit` also set if system not checked out; no update when system not registered
- Qualification gate unit tests: system qualification fields not set, RTM not EFFECTIVE, RTM traces_to_rs_version mismatch with current RS, CI not passing at qualified_commit (mocked API response), no check runs, no open PR matching qualified_commit, PR HEAD moved past qualified_commit, all conditions met
- Permission checks: admin-only for register, responsible_user-only for checkin
- Full regression suite (existing tests unaffected)

### Integration Verification

- **New system lifecycle:** register system → create CR with target_systems → release CR → checkout system → develop → create PR → checkout RTM, edit frontmatter with qualification values → checkin RTM (Jinja2 renders expressions, user_properties populated) → approve RTM (verify qualification fields update, `current_release` unchanged) → `system checkin` (auto-discovers PR, verifies gate, merges, releases) → verify `current_release` matches `qualified_version` and `release_commit` is the merge commit
- **Two-phase progression:** after RTM EFFECTIVE with system checked out, verify `qms system status` shows qualified_version ahead of current_release; after system checkin, verify they match
- **CLI-driven merge:** system checkin merges the PR; agent pushing additional commits after qualification → PR HEAD mismatch → checkin refused
- **Migration pathway (system not checked out):** register existing system → checkout RTM, edit frontmatter with qualification values → checkin RTM → approve RTM → verify system record has `qualified_version`, `qualified_commit`, `current_release`, AND `release_commit` all populated in one step — no system checkin needed
- **Evidence chain enforcement:** checkin with qualification fields not set → refused; checkin with RTM tracing to outdated RS version → refused; checkin with CI failure at qualified_commit → refused; checkin with PR HEAD != qualified_commit → refused
- **Register identity verification:** invalid submodule path → refused; namespace not in config → refused; RS/RTM not found → refused; github repo inaccessible → refused
- **Concurrent ownership rejection:** two users attempt checkout

---

## 9. Implementation Plan

### 9.1 Phase 1: Pre-Execution Baseline

1. Commit and push project repository to capture pre-execution state

### 9.2 Phase 2: Test Environment Setup

1. Clone qms-cli to `.test-env/`
2. Create and checkout branch `cr-106`
3. Verify clean test environment (existing tests pass)

### 9.3 Phase 3: Requirements (RS Update)

1. Checkout SDLC-QMS-RS
2. Add requirements for system governance commands (REQ-SYS-001 through ~REQ-SYS-012)
3. Checkin RS, route for review and approval

### 9.4 Phase 4: Implementation

1. Create `qms_system.py` — system metadata utilities, `check_qualification_gate()`
2. Create `commands/system.py` — five subcommands (register, list, status, checkout, checkin)
3. Modify `workflow.py` — add post-approval hook: when RTM reaches EFFECTIVE, update registered system's qualification fields (and `current_release` if system not checked out)
4. Modify `qms_config.py` — add system permissions
5. Modify `commands/create.py` — add `target_systems` to CR metadata
6. Modify `qms_paths.py` — add system path helpers
7. Modify `qms.py` — import system commands
8. Create `tests/test_system.py` — comprehensive unit tests

### 9.5 Phase 5: Qualification

1. Run full test suite, verify all tests pass
2. Push to dev branch
3. Verify GitHub Actions CI passes
4. Document qualified commit hash

### 9.6 Phase 6: Integration Verification (New System Lifecycle)

1. Exercise system governance commands against a test QMS instance
2. Verify end-to-end workflow (register → checkout system → checkout RTM → edit frontmatter → checkin RTM → approve RTM → system checkin with qualification gate)
3. Verify error paths (no ownership, gate failure, concurrent access)

### 9.7 Phase 7: Migration Pathway Verification

Confirm that the migration pathway for existing SDLC systems works on the execution branch BEFORE merging. This is critical: if migration fails post-merge, the new qms-cli version ships without the ability to bring existing systems under governance.

1. In the test QMS instance, set up pre-existing SDLC documents (RS and RTM) in EFFECTIVE state — simulating the current production state of qms-cli and claude-qms
2. Register the simulated system using `qms system register` (identity only — path, namespace, repo)
3. Verify the register command's identity verification accepts valid data and rejects invalid data
4. Checkout the RTM, edit source frontmatter to populate qualification metadata, checkin
5. Verify the qualification gate reads the RTM metadata correctly
6. Verify that a subsequent system checkin succeeds when the evidence chain is valid
7. Verify that a subsequent system checkin fails when any link in the chain is broken (wrong commit, wrong RS version, etc.)

### 9.8 Phase 8: RTM Update and Approval (First Cycle — Verification Evidence)

1. Checkout SDLC-QMS-RTM
2. Add verification evidence for new requirements
3. Checkin RTM, route for review and approval
4. Verify RTM reaches EFFECTIVE status before proceeding

### 9.9 Phase 9: MCP Tools

1. Add 5 new MCP tools to `qms_mcp/tools.py`
2. Verify MCP tools work via test invocations

### 9.10 Phase 10: Merge and Submodule Update

**Prerequisite:** RS and RTM must both be EFFECTIVE.

1. Create PR to merge cr-106 to main
2. Merge via merge commit (--no-ff)
3. Verify qualified commit is reachable on main
4. Update submodule pointer in parent repo

### 9.11 Phase 11: Register Existing Systems

1. Register qms-cli using `qms system register` with `--path`, `--namespace`, `--repo`, `--cr CR-106`
2. Verify system metadata created at `QMS/.meta/SYSTEM/qms-cli.json` with identity fields populated and qualification fields empty
3. Register claude-qms using `qms system register` with `--path`, `--namespace`, `--repo`, `--cr CR-106`
4. Verify system metadata created at `QMS/.meta/SYSTEM/claude-qms.json` with identity fields populated and qualification fields empty

### 9.12 Phase 12: Stamp RTM Metadata Baselines (Second Cycle)

1. Checkout SDLC-QMS-RTM, edit source frontmatter to set `qualified_commit`, `traces_to_rs_version`, `qualified_version` for qms-cli's current qualified state, checkin
2. Checkout SDLC-CQ-RTM, edit source frontmatter to set `qualified_commit`, `traces_to_rs_version`, `qualified_version` for claude-qms's current qualified state, checkin
3. Route both through review and approval to reach EFFECTIVE
4. Verify both RTM metadata sidecars contain the new fields
5. Verify both system records have `qualified_version`, `qualified_commit`, AND `current_release` fully populated (systems were not checked out, so all fields propagated at approval)

### 9.13 Phase 13: Post-Execution Baseline

1. Commit and push project repository to capture post-execution state

---

## 10. Execution

| EI | Task Description | VR | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|----|-------------------|--------------|---------------------|
| EI-1 | Pre-execution baseline: commit and push | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-2 | Set up test environment, create branch cr-106 | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-3 | Update SDLC-QMS-RS with system governance requirements | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-4 | Implement system metadata module, qualification gate, post-approval propagation, and commands | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-5 | Run full test suite, push to cr-106, verify CI | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-6 | Integration verification: end-to-end new system lifecycle (register → checkout system → checkout RTM → edit frontmatter → checkin RTM → approve RTM → system checkin with qualification gate) | Yes | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-7 | Migration pathway verification: register simulated existing system, edit RTM frontmatter with qualification metadata, verify qualification gate works with migrated data | Yes | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-8 | Update SDLC-QMS-RTM with verification evidence (first cycle — enables merge gate) | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-9 | Add MCP tools for system commands | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-10 | Merge gate: PR, merge (--no-ff), submodule update | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-11 | Register qms-cli and claude-qms as governed systems (`qms system register ... --cr CR-106`) | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-12 | Stamp RTM metadata baselines (second cycle): checkout SDLC-QMS-RTM and SDLC-CQ-RTM, edit source frontmatter with qualification metadata, checkin, approve to propagate qualification to system records | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |
| EI-13 | Post-execution baseline: commit and push | | [SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

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

- **Guided Agent Orchestration Vision:** `.claude/sessions/Session-2026-02-25-001/guided-agent-orchestration-v2.md`
- **Design Plan:** `.claude/plans/sleepy-hugging-sunbeam.md`
- **Original Design Discussion:** `.claude/sessions/Session-2026-02-22-004/interactive-engine-redesign.md`
- **Prerequisite CR:** CR-107 (Unified Document Lifecycle)

---

**END OF DOCUMENT**
