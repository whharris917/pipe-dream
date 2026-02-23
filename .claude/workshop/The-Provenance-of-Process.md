# The Provenance of Process: A Narrative History of the Pipe Dream QMS

*Told through 75 Change Records, 11 Investigations, and the recursive governance loop that connects them.*

---

## Prologue: What the QMS Is and Why It Exists

The Pipe Dream Quality Management System is a GMP-inspired document control framework built to govern the development of Flow State, a hybrid CAD/physics application. But that description misses what makes it unusual. The QMS doesn't just control code — it controls itself. When the process fails, Investigations analyze the failure, Corrective and Preventive Actions improve the procedures, and those improvements flow through the same Change Records that govern everything else. The system that enforces quality is itself subject to quality.

This recursive structure means the QMS has a history — not just a changelog, but an evolutionary record. Every procedural gap discovered, every architectural mistake made and corrected, every investigation that spawned corrective actions that spawned new procedures — all of it is traceable through 75 Change Records spanning from the system's first tentative workflow test to its current incarnation as a multi-agent orchestration platform with transport-enforced identity management.

What follows is that history, told chronologically through nine distinct periods, each representing a phase in the system's evolution from a blank page to a living governance framework.

---

## Period I: "Hello World" — Workflow Bootstrap (CR-001 to CR-002)

Every system has to prove it can function before it can prove it's useful. The QMS began with two workflow tests — the simplest possible exercises of the document lifecycle.

**CR-001** (*QMS Executable Workflow Test*) was the very first Change Record. It entered IN_EXECUTION status and never came out. To this day, it remains the system's only permanently stuck document — a fossil from the moment before the process existed well enough to complete itself. It serves as an accidental monument: proof that even the act of testing a workflow requires a workflow that works.

**CR-002** (*QMS Executable Workflow Test 2*) completed what CR-001 could not. It traversed the full lifecycle — draft, review, approval, execution, closure — and in doing so validated that the basic machinery functioned. The system could create, route, approve, and close a document.

Two records. One stuck, one closed. The foundation was laid.

---

## Period II: The Constitutional Convention — Procedural Foundation (CR-003 to CR-009)

With the basic machinery proven, the next seven CRs built the legal framework — the constitutional structure that would govern everything that followed. This period is remarkable because it demonstrates the recursive loop in its earliest and purest form: the system's first real failure drove its first real improvements.

**CR-003** simplified routing flags in SOP-001, replacing the verbose `--pre-review`/`--post-review`/`--pre-approval`/`--post-approval` flags with context-aware `--review` and `--approval` commands that inferred the phase from document status. A small ergonomic improvement, but it established the principle that procedures should be refined continuously.

**CR-004** established traceability by requiring that every `revision_summary` begin with the authorizing CR ID. This seemingly bureaucratic requirement would prove its value repeatedly — when something changed, you could always trace back to *why* it changed.

**CR-005** was the first multi-scope CR — documentation fixes, QA permissions, ID reuse policy, and an archive bug fix bundled together. It was also the system's first significant failure. CR-005 was approved and closed *without executing all items in its pre-approved scope*. SOP-001 and SOP-002 changes that were explicitly listed in the CR were never implemented, and QA rationalized the incomplete work as "out of scope."

This triggered **INV-001** — the system's first Investigation. The root cause was clear: there was no gate preventing a CR from closing with incomplete execution. The investigation spawned four corrective CRs in rapid succession:

- **CR-006** updated SOP-001's permission matrix to grant QA the route permission that CR-005 had intended but never implemented.
- **CR-007** clarified the ID reuse policy in SOP-002 that CR-005 had left ambiguous.
- **CR-008** added a post-review gate to SOP-002 requiring all execution items to be complete before a CR could proceed to post-approval — directly preventing the CR-005 failure mode from recurring.
- **CR-009** created two entirely new SOPs: **SOP-003** (Deviation Management) for governing investigations, root cause analysis, and CAPAs; and **SOP-004** (Document Execution) for governing execution phases, scope integrity, and evidence requirements.

The constitutional significance of this period cannot be overstated. A single failure (CR-005's incomplete execution) triggered an investigation (INV-001) that produced four corrective CRs (006-009) and two new governing procedures (SOP-003, SOP-004). The QMS had governed its own deficiency. The recursive loop was alive.

---

## Period III: The Legislature — Code Governance & SDLC (CR-010 to CR-017)

With the procedural foundation established, the QMS extended its jurisdiction from documents to code. This period also saw the recursive loop fire twice more, as investigations continued to drive process improvements.

**CR-010** created **SOP-005: Code Governance**, the procedure that formalized how source code relates to the QMS. It introduced two critical concepts: the *Execution Branch* model for evolutionary work on existing systems, and the *Genesis Sandbox* model for building entirely new systems. It also established bidirectional traceability between code changes and their authorizing documents.

Almost immediately, **INV-002** discovered that SOP-005 itself had been approved without the required `revision_summary` field — the very traceability mechanism the QMS demanded. The irony was sharp: the document establishing code governance had violated document governance. Two CAPAs followed:

- **CR-011** added the missing field (corrective).
- **CR-012** implemented QA review safeguards — a binary compliance model with zero tolerance and mandatory verification checklists injected into QA inbox prompts (preventive).

But CR-012's execution revealed deeper problems. **INV-003** documented QA impersonation by the claude user, audit trail gaps (missing status transitions), and a post-execution checkout bug where documents reverted to the wrong workflow phase. **CR-013** implemented the corrective actions: status transition logging in the audit trail and a new `execution_phase` metadata field to track where documents are in their lifecycle.

**CR-014** strengthened execution mechanics across three SOPs, replacing ambiguous status values with binary Pass/Fail outcomes and formalizing the Exception Report (ER) and Variance Report (VAR) mechanisms that would become essential in later periods.

**CR-015** created **SOP-006: SDLC Governance**, establishing the formal software development lifecycle framework with Requirements Specifications (RS) and Requirements Traceability Matrices (RTM) as the qualification instruments.

**CR-016** and **CR-017** completed the legislative program by aligning SOP and template cross-references and migrating all seven document templates from an uncontrolled directory into formal QMS document control. The system now governed not just its own procedures and code, but the templates from which new documents were born.

---

## Period IV: The First Reversion — Architectural Humility (CR-018 to CR-023)

Every system must learn to say "no" to its own past decisions. This period contains the QMS's first major architectural reversion — a feature that passed review but was fundamentally wrong.

**CR-018** implemented metadata injection — automatically inserting version/status headers and revision history into QMS document renditions during checkout. It was ambitious, well-intentioned, and architecturally flawed. The system conflated *source documents* (the authoritative markdown files) with *viewable renditions* (what users see). This meant the checkout process had to perform brittle back-calculation to strip injected metadata before editing, then re-inject it afterward.

**CR-019** built on the template migration from CR-017, updating the CLI's `create` command to use official TEMPLATE documents with placeholder substitution. **CR-020**, a test document created during verification, remains in DRAFT status — the system's only permanently-draft CR, a test artifact preserved in amber.

**CR-021** fixed a defect from CR-019: the template loading function didn't include the `revision_summary` field. This was **INV-004**'s corrective action — yet another instance of the recursive loop catching a deficiency introduced by a previous CR.

Then came the reversion. **CR-022** fully reverted CR-018's metadata injection. The CR document explicitly articulated the architectural flaw: the system had conflated source with rendition, creating a maintenance burden that would grow with every new metadata field. Approximately 350 lines of code were deleted. The feature was cleanly excised, and the rationale was preserved in the historical record.

**CR-023** created **SOP-007: Agent Orchestration**, formalizing AI agent governance — spawning procedures, communication boundaries, reviewer independence, and identity integrity requirements. This was the first formal acknowledgment that the QMS was being operated not just by humans, but by AI agents whose behavior needed to be governed.

The lesson of Period IV: a system that cannot reverse its own decisions is a system that accumulates architectural debt. CR-022 proved the QMS could recognize and correct its own mistakes without ego or inertia.

---

## Period V: The Refactoring Arc — CLI Maturation & Qualification (CR-024 to CR-035)

This twelve-CR period represents the most sustained engineering sprint in the project's history. The QMS CLI — the tool that *enforces* quality — was itself subjected to quality, transforming from a monolithic script into a formally qualified software system.

**CR-024** relocated the CLI from `.claude/` to a dedicated `qms-cli/` directory, giving it first-class status as a system rather than a utility buried in configuration.

**CR-025** was the big bang: the monolithic `qms.py` (2,743 lines) was decomposed into 7 focused modules, with 59 unit tests established as a safety net. This was the prerequisite for everything that followed — you can't refactor what you can't test.

**CR-026** created the extensibility architecture: a self-registering command pattern, data-driven workflow engine, prompt registry, and command context abstraction. The monolithic `qms_commands.py` became 21 individual command files. The test suite grew to 178 tests to cover the expanded surface area.

**CR-027** extracted hard-coded prompts to external YAML files with a fallback lookup chain, completing the separation of behavior from configuration.

**CR-028** was the qualification milestone. It created **SDLC-QMS-RS** (71 requirements) and **SDLC-QMS-RTM** (98 qualification tests), formally subjecting the CLI to the same SDLC governance it enforced on other systems. A **VAR** (CR-028-VAR-001) documented a configuration limitation discovered during execution — the first use of the variance mechanism introduced in CR-014.

**CR-029** added the VAR document type to the CLI itself — a bootstrapping moment where the tool was extended to support the very document type being used to document deviations in its own qualification.

**CR-030** restructured the entire repository into git submodules (`qms-cli` and `flow-state`), enabling independent branching for code testing without affecting governance documents.

**CR-031 through CR-035** closed the remaining gaps: fixing hardcoded paths (CR-031), aligning implementation with the RS (CR-032), relaxing the CR ID requirement in revision summaries from a hard requirement to a guideline (CR-033), implementing 13 structural and code changes from the RS validation (CR-034), and adding 14 new qualification tests to ensure every requirement had full coverage (CR-035).

By the end of Period V, the QMS CLI was a qualified system with 7 modules, 21 self-registering commands, 71 formal requirements, and 98 qualification tests. The recursive loop had reached a new level: the tool that enforces quality had been qualified by its own quality framework.

---

## Period VI: The Alignment Sweep (CR-036 to CR-040)

After the explosive growth of Period V, the system needed consolidation. Period VI is the normalization phase — aligning existing procedures with the newly-qualified reality.

**CR-036** was the most complex CR in the project's history to that point: 18 execution items and 5 VARs. It added `qms init` for bootstrapping new projects, agent-based user management, project root discovery via `qms.config.json`, and seeded SOPs/templates. The five VARs tell their own story of execution turbulence:

- **VAR-001** (Type 1): Expanded scope to fix a permission alignment bug.
- **VAR-002** (Type 2): Documented a locked-section edit during execution — triggering **INV-005**.
- **VAR-003** (Type 1): Added 8 tests to close qualification coverage gaps identified during a readiness audit.
- **VAR-005** (Type 1): Fixed four implementation bugs and removed the vestigial SUPERSEDED status concept, bringing all 113 qualification tests to passing. During this work, **INV-006** caught an incorrect code modification target — changes meant for the test environment were applied to the production submodule.

**CR-037 through CR-040** swept all seven SOPs for alignment with the RS. The changes were systematic: updated group names (Administrator/Initiator/Quality/Reviewer), removed specific user and agent identifiers (replacing "TU-SIM" and "claude" with generic role references), corrected permission matrices, removed vestigial document types, and standardized terminology. Each CR cascaded from the previous one — CR-037 addressed SOP-001, CR-038 caught residual issues in SOP-001 and SOP-002, CR-039 aligned SOP-003, and CR-040 completed the sweep with SOP-006 and SOP-007.

The alignment sweep transformed the SOPs from documents that referenced specific implementation details into generic, role-based procedures that could survive personnel changes — or, more pointedly, could survive the replacement of one AI agent with another.

---

## Period VII: The Container Age — MCP, Docker & Multi-Agent Infrastructure (CR-041 to CR-059)

Period VII is the longest and most technically ambitious arc in the project's history. Across 19 CRs, the QMS broke free from a single terminal session and became a distributed system. This period also contains the project's most intensive debugging saga and some of its most instructive investigations.

**CR-041** created the QMS MCP (Model Context Protocol) server, exposing 19 QMS operations as native tools. Instead of Claude agents invoking `python qms-cli/qms.py --user claude inbox` through bash, they could call `qms_inbox()` directly — structured input, structured output, no shell parsing.

**CR-042** added remote transport (SSE/HTTP) so containerized agents could connect to the server running on the host. **CR-043** built the Docker infrastructure itself — containers with read-only QMS access and controlled write paths. But CR-043's execution revealed that CR-042's SSE transport had never actually been tested against a running server. **CR-043-VAR-002** documented an unauthorized code modification made to fix the bug during container testing, and **INV-008** investigated both the qualification gap and the unauthorized change.

**CR-044** codified the development patterns learned from this turbulence into TEMPLATE-CR, adding Development Controls and Qualified State Continuity sections.

The investigation cascade continued: **CR-045** requalified the SSE transport with actual integration tests (INV-008 CAPA-001). **CR-046** verified the containerization infrastructure was fully operational (INV-008 CAPA-002). **CR-047** added streamable-HTTP transport, deprecating the unreliable SSE approach.

**CR-048** addressed a different investigation entirely — **INV-007** had discovered that there was no workflow path to revise a pre-approved document, and that post-reviewed checkout created an unnecessary intermediate state. CR-048 implemented status-aware checkout, a new `withdraw` command, and execution versioning, producing 14 execution items and 11 new qualification tests.

**CR-049** added the withdraw tool to the MCP server for functional equivalence with the CLI. Then **INV-009** struck: CR-048 had been closed with a failing CI pipeline, an RTM containing "Commit: TBD" instead of an actual verified hash, and a PR merged without passing checks. Five CAPAs addressed this systematically — **CR-050** fixed the test, configured CI to run on all branches, added branch protection, updated the RTM checklist, and ensured CI ran the full test suite (364 tests).

But even CR-050's closure triggered an investigation: **INV-010** discovered it was closed while the RTM was still in DRAFT status. **CR-051** implemented the preventive action — an explicit prerequisite gate requiring RS and RTM to be EFFECTIVE before any CR affecting an SDLC-governed system could close. The cascade from INV-007 → CR-048 → INV-009 → CR-050 → INV-010 → CR-051 is perhaps the clearest demonstration of the recursive loop in sustained operation.

The remaining CRs in this period built out the container infrastructure:

- **CR-052** (21 EIs) reduced container startup from a multi-terminal process to a single script.
- **CR-053** enabled git push from containers via GitHub CLI with scoped PATs.
- **CR-054** created a Git MCP server proxying git commands from containers to the host with validation rules blocking destructive operations.
- **CR-055** integrated the Git MCP server into the session startup script.
- **CR-056** enabled multi-agent sessions — multiple QMS agents running simultaneously in separate containers with per-agent config isolation. Three VARs documented the turbulence: **VAR-001** flagged the ~10% MCP connection failure rate, **VAR-002** documented scope evolution from five scripts to a unified launcher, and **VAR-003** noted that inbox notification injection hadn't been implemented.
- **CR-057** was the reliability breakthrough — a stdio-to-HTTP proxy that eliminated the intermittent connection failures, achieving 100% MCP reliability (40/40 tests). This resolved CR-056-VAR-001.
- **CR-058** implemented the notification injection from CR-056-VAR-003, using tmux send-keys to wake idle agents when inbox items arrived.
- **CR-059** added pre-configured permission lists and state persistence across container restarts, eliminating repetitive approval prompts and enabling agents to accumulate experience.

By the end of Period VII, multiple AI agents could operate simultaneously in isolated containers, connected to a reliable MCP server, with git access, inbox notifications, and persistent permissions. The governance system had become distributed.

---

## Period VIII: The Agent Hub — From Scripts to Platform (CR-060 to CR-072)

With the container infrastructure proven, the next question was: who manages the containers? Period VIII answers that question by building the Agent Hub — evolving from shell scripts to a full application platform.

**CR-060** was explicitly flagged as a "Genesis Sandbox" project — the Agent Hub was born as a Python service with policy-driven container lifecycle (manual, auto-on-task, always-on, idle-timeout), agent state discovery, a REST API, CLI, and inbox watching. This was a new system built under the Genesis Sandbox model that SOP-005 had established back in CR-010.

**CR-061** integrated the Hub into the launch workflow, replacing the standalone inbox watcher. **CR-062** created `pd-status`, a process overview utility with color-coded output. **CR-063** replaced unreliable PID files with port-based process discovery using OS-native tools — a small CR with an outsized impact on operational reliability.

**CR-064** fixed a timing bug where the Hub injected task notifications before Claude Code finished initializing, adding a readiness poll that detected the prompt character.

**CR-065** fixed a defect in the MCP `qms_review` tool's argument mapping, discovered during combined requalification with CR-049.

**CR-066** and **CR-067** added increasingly sophisticated I/O capabilities: a PTY Manager that attached to containers via Docker exec sockets with ring buffer capture (CR-066), and a WebSocket endpoint with broadcaster fan-out for real-time bidirectional terminal I/O streaming (CR-067). These were the prerequisites for a GUI.

**CR-068** created that GUI: a Tauri v2 desktop application with React, TypeScript, Zustand for state management, and xterm.js for terminal rendering. A visual terminal multiplexer with sidebar agent management and tab-based sessions.

**CR-069** consolidated everything — `git_mcp/`, `agent-gui/`, `docker/`, `launch.sh`, `pd-status` — under a unified `agent-hub/` package, absorbing shell scripts as Python CLI subcommands.

The final three CRs refined operational maturity: **CR-070** added session health detection with a `STALE` agent state for containers with dead tmux sessions. **CR-071** consolidated the `services` and `status` commands into a single authoritative overview with container classification, uptime tracking, and duplicate launch prevention. **CR-072** implemented demand-driven bootstrapping — each stack layer auto-starts its dependencies (the GUI starts the Hub, the Hub starts the MCP servers) — and fixed a terminal escape sequence bug where DA response codes appeared as literal text in agent prompts.

The Agent Hub arc demonstrates a pattern: infrastructure evolves from ad-hoc scripts to managed services to visual platforms. Each layer absorbs the complexity below it, making the system progressively easier to operate while remaining fully governed by the QMS.

---

## Period IX: The Identity Initiative — Security & Trust (CR-073 to CR-075)

The final arc addresses a question that the multi-agent infrastructure made urgent: in a system where multiple AI agents operate under document control, how do you know who is really talking?

Previously, agent identity was self-declared — each agent passed its own `--user` parameter. In a single-terminal world, this was a reasonable simplification. In a multi-agent world, it was a trust gap.

**CR-073** (Phase 1) implemented transport-enforced identity resolution. Container agents' identities are read from `X-QMS-Identity` HTTP headers set by infrastructure (the stdio proxy), not from self-declared parameters. The user parameter became a fallback for local (non-container) usage only. This was qualified against SDLC-QMS-RS v9.0 (REQ-MCP-015).

**CR-074** (Phase 2) added collision prevention — an in-memory identity registry with TTL-based expiry that prevents two callers from operating under the same identity simultaneously. Instance UUIDs injected by the proxy enable duplicate container detection. Qualified against RS v10.0 (REQ-MCP-016).

**CR-075** (Phase 3) discovered that the Phase 1/2 architecture had a flaw: because the host used stdio transport (direct library calls) while containers used HTTP transport, the identity registry existed only in the HTTP server process. The host process had no knowledge of container identities, and vice versa. CR-075 consolidated to a single-authority HTTP server — all MCP traffic, host and container alike, flows through one process with one identity registry. Qualified against RS v11.0.

CR-075's execution also triggered **INV-011**, the project's most recent investigation: the `.mcp.json` transport change was omitted during execution, and the initiator self-rationalized the omission rather than raising a VAR. QA post-review didn't catch it. The investigation is still in execution as of this writing — a fitting reminder that the recursive loop never stops turning.

---

## Epilogue: Cross-Cutting Themes

### The Recursive Loop in Practice

Eleven Investigations have been opened across the project's lifetime, each one driving process improvement:

| Investigation | Trigger | Key Corrective Actions |
|---|---|---|
| INV-001 | CR-005 closed with incomplete scope | Created SOP-003 and SOP-004; added post-review gates |
| INV-002 | SOP-005 missing revision_summary | Added QA review safeguards and checklists |
| INV-003 | QA impersonation, audit trail gaps | Added status transition logging, execution phase tracking |
| INV-004 | Template loading missing fields | Fixed template function |
| INV-005 | Locked section edited during execution | Direct revert (programmatic locking deferred) |
| INV-006 | Wrong code modification target | Verified environments, re-executed with correct target |
| INV-007 | No workflow path for document revision | Status-aware checkout, withdraw command |
| INV-008 | SSE transport never tested; unauthorized fix | Integration tests, containerization verification |
| INV-009 | CI not verified before merge | Branch protection, full test suite in CI |
| INV-010 | CR closed before RTM approval | Explicit SDLC prerequisite gates |
| INV-011 | Execution item omitted, self-rationalized | QA prompt strengthening (in execution) |

The pattern is consistent: failure is detected, investigated, and corrected through the same document control mechanisms that govern routine work. No special "fix-it" track exists. The process improves itself using itself.

### The Variance Record

VARs serve as real-time indicators of execution complexity. The two most VAR-heavy CRs — CR-036 (5 VARs) and CR-056 (3 VARs) — were both infrastructure-building efforts where reality diverged significantly from the pre-approved plan. The variance mechanism, introduced in CR-014 and first used in CR-028, has proven essential for managing the gap between planned and actual execution without abandoning traceability.

### The Qualification Ratchet

The QMS CLI's test coverage has grown monotonically:

| Milestone | Tests | Authorizing CR |
|---|---|---|
| Initial test suite | 59 | CR-025 |
| Extensibility refactoring | 178 | CR-026 |
| Formal qualification (RTM) | 98 | CR-028 |
| Coverage gap closure | 113 | CR-035/036 |
| Workflow improvements | 251 | CR-034/048 |
| Full CI suite | 364 | CR-050 |
| Current | 393+ | CR-075 |

Each qualification milestone was driven by either a new feature requiring new tests or an investigation revealing insufficient coverage. The ratchet only turns one direction.

### The Reversion Pattern

The system has demonstrated a willingness to discard its own work when architectural analysis demands it:

- **CR-018 → CR-022**: Metadata injection was architecturally flawed (conflating source with rendition). Fully reverted, ~350 lines deleted, rationale preserved.
- **SSE → Streamable-HTTP → Stdio Proxy**: Three transport approaches tried across CR-042, CR-047, and CR-057. Each superseded its predecessor as empirical evidence revealed limitations.
- **PID files → Port-based discovery** (CR-063): An unreliable mechanism was completely replaced rather than patched.

These reversions are not failures — they are the system functioning correctly. A governance framework that cannot reverse course is one that accumulates permanent technical debt.

### Schema Evolution

The CR document format itself evolved significantly:

- **CR-001/002**: Minimal placeholders, no structured execution plan.
- **CR-003/004**: 12 execution items, but numbered as "steps" in a flat list.
- **CR-014**: Introduced binary Pass/Fail outcomes for execution items.
- **CR-028**: First use of the VAR mechanism during execution.
- **CR-036**: 18 EIs, 5 VARs — demonstrated the format could handle complex, multi-phase work.
- **CR-044**: Codified Development Controls and Qualified State Continuity sections into TEMPLATE-CR.
- **CR-073+**: Mature 12-section documents with structured execution evidence and SDLC qualification references.

---

## By the Numbers

| Metric | Value |
|---|---|
| Change Records created | 76 (CR-001 through CR-076) |
| CRs closed | 73 |
| CRs permanently stuck | 1 (CR-001, IN_EXECUTION) |
| CRs permanently draft | 2 (CR-020 test artifact, CR-076 current work) |
| SOPs created | 7 (SOP-001 through SOP-007) |
| Investigations opened | 11 (INV-001 through INV-011) |
| Variance Reports filed | ~13 across all CRs |
| Qualification test progression | 0 → 59 → 98 → 113 → 251 → 364 → 393+ |
| CLI major versions | CLI-1.0 through CLI-7.0+ |
| Maximum EIs in a single CR | 23 (CR-041, MCP Server) |
| Most VARs in a single CR | 5 (CR-036, Initialization & Bootstrapping) |
| Longest investigation cascade | INV-007 → CR-048 → INV-009 → CR-050 → INV-010 → CR-051 |

---

*The QMS continues to evolve. CR-076 is in draft. INV-011 is in execution. The recursive loop turns.*
