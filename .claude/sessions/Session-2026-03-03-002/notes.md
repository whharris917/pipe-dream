# Session-2026-03-03-002

## Current State (last updated: 2026-03-04 EI-3 continued, compaction 7)
- **Active document:** CR-108 (IN_EXECUTION v1.1, checked out)
- **Current EI:** EI-3 (Write informal RS + begin prototyping)
- **Blocking on:** Nothing
- **Next:** Continue iterating on prototype per Lead direction
- **Total usability tests:** 20 (14 from compaction 6 + 3 README update round + 3 stress tests)

## Progress Log

### Session Start
- Previous session: Session-2026-03-03-001 — DocuBuilder paradigm shift, CR-108 drafted
- Read all SOPs (001-007), QMS-Policy, START_HERE, QMS-Glossary
- Read authoring-and-executing-controlled-documents.md (core design principles)
- Read document_dna.json and prompt.txt (design artifacts)
- CR-108 status: DRAFT v0.1, responsible user: claude, not checked out
- Goal: Execute CR-108 (route, approve, execute EIs, close)

### CR-108 Routing
- Routed for pre-review, QA recommended
- Routed for pre-approval, QA approved -> PRE_APPROVED v1.0
- Released for execution -> IN_EXECUTION
- EI-1: Pre-execution commit `6798bf5`

### EI-2: Create Sandbox
- Added `docu-builder/` to `.gitignore`
- Created `docu-builder/docubuilder/` package directory

### EI-3: Write Informal RS + Prototyping
- Drafted RS collaboratively with Lead — 35 requirements across 10 sections
- Consistency review found and fixed: 1 contradiction, 1 duplication, 2 omissions
- Built working prototype: model.py, renderer.py, commands.py, engine.py
- Usability test 1 (general-purpose agent, no context): 3.5/5
  - Succeeded fully, found naming confusing (checkout/checkin), wanted examples
  - Fixed: renamed to view/submit, added module docstring with example and column types
- Usability test 2 (general-purpose agent, minimal context): 4/5
  - Succeeded fully, found nav state loss on reload, cosmetic section ID bug
  - Fixed: persist session.json, section IDs now `[S:id]` not `[Sid]`
- Usability test 3 (comprehensive: template + seal + execute + amend): 4/5
  - 34/34 steps passed, zero errors
  - Tested: template creation, sealed rows, template instantiation, sealed deletion prevention, execution, amendment
  - Suggestions: Engine.from_template(), multi-word column quoting, configurable ID prefix, progress indicator, performer in view
  - Fixed: Added Engine.from_template(), id_prefix support in add_table, execution progress counter in renderer
- Usability test 4 (minimal context, "figure it out from source"): 4/5
  - Zero errors, agent built a test protocol from scratch by reading source code
  - Confirmed: multi-word column quoting is fiddly, row-level locking coarser than ideal
  - New suggestion: view_all mode for seeing multiple sections at once

### EI-3 continued (2026-03-04): Features + README + ALCOA+ alignment

#### Features added
- `view_all` command — show all sections expanded at once
- `save_template` command — save document as reusable template file
- `Engine.from_template()` classmethod
- Configurable `id_prefix` on tables (e.g., `id_prefix=EI-` for EI-1, EI-2)
- Execution progress counter (`Progress: 3/6 cells executed`)
- `[SEALED]` vs `[LOCKED]` distinction in section list and error messages
- Section navigation marker changed from `>>` to `->` (avoided conflict with command prompt)

#### Architecture change: checkout/edit/checkin cycle (ALCOA+ compliance)
- Lead identified that agents were bypassing the intended interface by calling submit() in loops
- Refactored Engine to file-based workflow: checkout() writes document.txt, agent edits it, checkin() parses commands
- document.txt IS the interface — agent reads/writes this file, never touches JSON
- submit() kept as convenience shortcut for testing/scripting
- Auto-checkout after each checkin for seamless cycle

#### README written and iterated
- Concise README focused on checkout/edit/checkin workflow
- Tested by 6 agents total across 2 rounds — all rated 4/5
- Integrated feedback after each round

#### Usability tests 5-7 (README-only, submit()-based): all 4/5
- Test 5: Template creation — zero errors, rated README 4/5
- Test 6: Template instantiation + seal verification — zero errors, 4/5
- Test 7: Full execution + amendment — zero errors, 4/5

#### Usability tests 8-10 (README-only, file-based checkout/edit/checkin): all 4/5
- Test 8: Template creation via file workflow — zero errors, 4/5
- Test 9: Template instantiation via file workflow — zero errors, 4/5
- Test 10: Execution via file workflow — zero errors, 4/5
- Multi-agent pipeline proven: 3 different agents, each with minimal context, each operating on the workspace produced by the previous agent

#### Prerequisite blocking system
- Lead identified that prerequisite enforcement is essential for ALCOA+ compliance
- Requirements: (1) blocked rows must be visually distinct, (2) execution must be rejected if prereqs not met, (3) prereq rows must be completed in a PRIOR checkin cycle (different timestamps)
- Implemented in model.py:
  - `evaluate_prerequisites()` — parses "X complete" prereq format, resolves row IDs, checks completion
  - `is_row_complete()` — checks all executable cells in a row have audit entries
  - `get_cell_status()` — returns "complete", "ready", or "blocked" for any cell
  - `execute_cell()` now rejects blocked rows with clear error message
- Visual distinction in renderer.py:
  - `<<  >>` = ready (empty, can execute)
  - `<< -- >>` = blocked (prereq not met or sequence not reached)
  - `[BLOCKED]` row-level tag for rows with unmet prerequisites
- Cascade behavior: completing row N only unblocks direct dependents, not entire chain
- One command per checkin enforced by single `>> ` prompt in rendition file

#### Usability test 11 (prerequisite blocking, file-based): 5/5
- First 5/5 rating!
- Agent tested: initial blocking state, rejected out-of-order execution, cascade unblocking, full sequential progression
- Called visual distinction "immediately clear at a glance"
- Called enforcement "well-implemented" with "informative error messages"

### EI-3 continued (2026-03-04): Lead walkthrough + renderer redesign (compaction 3)

#### Renderer redesign (Lead-driven, iterative)
- Switched from ASCII-art rendering (.txt) to proper markdown (.md)
- Removed all bold/italic formatting per Lead preference
- Consistent `##` section headers for all regions (TOC, sections, commands)
- Removed redundant `---` separators (markdown headings already have rules)
- Navigation renamed to "Table of Contents" — rendered as markdown table
- Section expand/collapse: `[-]` visible, `[+]` collapsed — on section headers
- Document body boundaries: `> **>>> START/END OF DOCUMENT BODY <<<**`
- "Active Section" region with empty-section placeholder text

#### Type-specific element IDs (Lead-driven)
- Elements now identified as `TXT-0`, `TXT-1`, `TBL-0`, `TBL-1` (type-specific 0-indexed)
- Sections identified as `SEC-N:id` (1-indexed with human-readable ID)
- Element labels rendered as blockquotes with backticks: `> \`[TXT-0:name]\``
- Tags use parentheses: `(LOCKED)`, `(SEALED)`, `(EXTENDABLE)`
- All commands accept type IDs, names, or flat indices for element references
- `resolve_element_index()` and `resolve_section_index()` handle resolution

#### New commands added
- `edit_text` — edit text block content (respects lock/seal)
- `move_section` — reposition sections with `before=`/`after=`
- `add_column` — add column to existing table with `before=`/`after=`
- `rename_column` — rename column (updates column_order and all row values)
- `move_column` — reorder columns with `before=`/`after=`
- Named text blocks: `name=X` option on `add_text`
- Positional insertion: `before=`/`after=` on `add_text`, `add_table`, `add_section`
- Auto-navigate to newly created sections

#### Architecture notes
- `element_type_id()` computes display IDs dynamically from section element list
- Section ordering via dict rebuild (Python 3.7+ ordered dicts)
- Column operations modify both `columns` dict and `column_order` list

### EI-3 continued (2026-03-04): Usability tests 12-14 + bug fixes (compaction 4)

#### Usability tests 12-14: all 4/5
- Test 12: Template creation (3 sections, 6-column EI table, sealing, save_template) — 4/5
- Test 13: Full lifecycle (author + finalize + execute 4 rows with prereqs + amend) — 4/5
- Test 14: Error handling (10 error scenarios, all handled gracefully, no crashes) — 4/5

#### Bugs found and fixed
1. **`nav` error prefix inconsistency** — returned `"Section 'x' does not exist."` without `Error:` prefix. Fixed to match all other error messages.
2. **`save_template` Windows path mangling** — `shlex.split()` treats backslashes as escape chars, corrupting Windows paths. Fixed by extracting path from raw command text instead of shlex-parsed parts.
3. **`finalize` accepts empty documents** — allowed transitioning to execution with no sections. Added guard: "Error: Cannot finalize a document with no sections."
4. **`add_row` silently accepts unknown column names** — stored values for columns not in table definition. Now validates column names and returns error listing available columns.

#### RS updated
- Added REQ-INT-009 (Input Validation), REQ-INT-010 (Finalization Guard), REQ-INT-011 (Consistent Error Format)

#### README updated
- Prerequisite documentation expanded (must be a column type, not just a row value)
- Table extendability explained (default: extendable)
- Template example updated to include prerequisite column

### EI-3 continued (2026-03-04): Enforce/locked model + required element names (compaction 5)

#### Enforce/locked model (Lead-driven redesign)
- Lead identified sealed/locked system was overcomplicated — replaced with enforce/locked
- `locked` = system-controlled, born False, prevents modification (set only during template instantiation)
- `enforced` = user-controlled, born False, no effect during authoring — only takes effect when template is instantiated (enforced→locked in destination)
- Removed `lock` and `seal` commands, added single `enforce` command
- Changes across model.py, commands.py, renderer.py, README.md, rs.md
- Fixed edit_text to check section-level lock (not just element-level)
- REQ-LOCK-001 through REQ-LOCK-005 rewritten for new model

#### Required element names (Lead request)
- All elements now require an alphanumeric name/ID for stable identification
- Text blocks were the gap — `name` was optional, now required positional parameter
- `add_text` syntax changed: `add_text <section> <name> <text>` (was `add_text <section> <text> [name=X]`)
- model.py: `add_text()` name is required, empty names rejected with ValueError
- commands.py: `_cmd_add_text()` updated for new syntax, minimum parts 3→4
- renderer.py: always renders `[TXT-N:name]` (no bare `[TXT-N]` fallback)
- RS: REQ-AUTH-001 updated — all elements require a name
- README: command reference and quick start example updated
- All 6 verification tests passed

### EI-3 continued (2026-03-04): Renderer polish + column modes + inspect + cascade (compaction 6)

#### Renderer polish
- Element labels now gold bold HTML: `<span style="color: gold">**[TXT-0:intro]**</span>`
- Removed `>` blockquote prefix from element labels
- Removed document body boundary markers (START/END OF DOCUMENT BODY)
- Empty prerequisite cells render as "N/A"
- Executable cells during authoring render as `[EXECUTABLE]` (was blank)

#### Column modes — first-class concept (Lead-driven)
- Three modes: Executable, Auto, Non-Executable
- Centralized in model.py: `COLUMN_MODES` dict, `VALID_COLUMN_TYPES` set, `col_is_executable()`, `col_is_auto()`
- Replaced all 7 scattered hardcoded type-tuple checks across model.py and renderer.py
- RS: REQ-COL-001 rewritten for three modes, REQ-COL-004 added for Auto types
- README: column types table updated with Mode column

#### Inspect command and Context section
- `inspect <element_ref>` populates a Context section with element properties and available actions
- Table inspect shows: column properties table (index, name, type, mode), row count, pre-filled command templates
- Text and section inspect show available actions with pre-filled command syntax
- Context section sits after command reference, shows usage hint when empty
- Click target / superscript approach explored and abandoned (index instability, visual noise)

#### Element ID validation (Lead request)
- All element IDs enforce lowercase alphanumeric only: `[a-z0-9]+`
- Validated in `add_section`, `add_text`, `add_table` via `_validate_element_id()`

#### Sequential amendment cascade
- Amending a cell in a sequential row auto-reverts all subsequent executable cells
- Revert entries use `value: None` in the audit trail with reason linking to triggering amendment
- `_has_execution_value()` updated to check last entry's value is not None
- Renderer handles reverted cells (shows `<<  >>`) and counts only non-revert entries for amendment display

#### Cross Reference column type
- New executable column type: `cross_reference` (display: "Cross Ref")
- Used for Issue columns linking to VARs when execution steps fail
- Counts toward row completion — executors fill "N/A" for passing rows or VAR ID for failures
- Natural prerequisite gate: failed row with empty Issue stays incomplete, blocking dependents

#### RS comprehensive update
- Full pass to sync RS with implemented features
- New requirements: REQ-AUTH-011 (element IDs), REQ-COL-006 (executable blocked during authoring), REQ-COL-009 (cross reference), REQ-COL-010 (empty prereq display), REQ-EXEC-010 (sequential cascade), REQ-INT-011 (inspect command)
- Fixed stale references: sealed→enforced throughout
- Renumbered to fill gaps from removed requirements

### EI-3 continued (2026-03-04): README update, stress tests, design fixes (compaction 7)

#### README comprehensive update
- Added `inspect` command to both authoring and execution command tables (README + renderer)
- Updated element labels description (gold bold HTML, not blockquotes)
- Added `[EXECUTABLE]` during authoring, N/A for empty prerequisites
- Added Context section to rendered regions list
- Added sequential amendment cascade documentation
- Added element ID constraints (lowercase alphanumeric)
- Added status column documentation
- Clarified `id_prefix` in `add_table` syntax
- Fixed template example to use lowercase table names
- Added cross_reference to column types table

#### Usability tests 15-17 (README update round): all PASS, zero errors
- Test 15: Full authoring flow (16 commands) — zero errors
- Test 16: Template workflow with enforced→locked + prerequisite blocking (17 commands) — zero errors
- Test 17: Execution features: [EXECUTABLE], amendments, extendable tables (22 commands) — zero errors

#### Sequential tables — table-level property (Lead-driven)
- Sequential is now a table-level property (default: True), not per-row
- All `row.get("sequential")` checks changed to `table.get("sequential")` in model.py
- `add_table` accepts `sequential=false` option
- `(SEQ)` tag now appears on table label, not individual rows
- Inspect shows `Sequential: Yes/No`
- RS: REQ-EXEC-009 rewritten from "Sequential Row Execution" to "Sequential Tables"
- Removed per-row `sequential` from `add_row`

#### Stress tests 18-20: all PASS (19 scenarios)
- Test 18: Sequential cascade (5 scenarios) — PASS
  - Sequential enforcement, amendment cascade, mid-row cascade, multi-row independence, double amendment
- Test 19: Prerequisites + blocking (7 scenarios) — PASS
  - Chain blocking, fan-out unblocking, partial completion, deep chain, parallel branch, amend-reblock
- Test 20: Template/locking/inspect/non-sequential (4 phases, 39 steps) — PASS
  - Locked element protection, non-sequential tables, error edge cases

#### Bugs found and fixed from stress tests
1. **Progress counter bug** — cascade-reverted cells (last entry `value: null`) counted as filled. Fixed: check `val["entries"][-1].get("value") is not None`
2. **Stale inspect context** — failed `inspect` left previous Context section visible. Fixed: clear `inspect_context` when inspect command doesn't produce `__INSPECT__` result

#### Design fixes (4 observations from stress tests, all addressed)
1. **Cell status indicators changed**: `<< >>` / `<< -- >>` replaced with `[READY]` / `[BLOCKED]` per Lead preference
2. **Sequential blocking render bug fixed**: After cascade revert, all reverted cells showed `[READY]` instead of respecting sequential order. New `_exec_cell_indicator()` helper calls `get_cell_status()` for both empty and reverted cells
3. **Amendment counter fixed**: Only counts user-initiated amendments (entries with `reason` from non-system performers). Cascade-reverted + re-executed cells no longer show spurious `(amended x1)`
4. **Inspect scope-aware resolution**: `inspect TBL-0` now resolves within the currently-navigated section first. `parse_and_execute()` receives `current_section` parameter, passed to `_cmd_inspect()`
5. **Cascade-reblock documented**: Added README note explaining that amending in a sequential table can cascade-revert cells, making the row incomplete, which re-blocks prerequisite dependents

#### RS and README updated
- REQ-DATA-006: `[READY]` / `[BLOCKED]` replace `<< >>` / `<< -- >>`
- README: cell status indicators, cascade-reblock note, sequential tables section

---

## Reflection: The Rapid Prototyping Loop

CR-108's genesis sandbox approach — stop thinking, start building — proved itself
decisively in this session. The loop that emerged was:

**Build -> Deploy to naive agent -> Collect feedback -> Fix -> Repeat**

This cycle ran 11 times in a single (extended) session. Each iteration was tight:
the agent would attempt a task, report what confused it, rate the system, and suggest
improvements. We'd fix the top issues and immediately launch the next agent. No
planning documents, no design reviews, no tickets — just build, test, learn.

### What made the loop effective

**Agents as genuine users.** Spawning agents with minimal context (eventually just
"read the README") created honest usability data. These agents had no insider
knowledge of the design intent — they discovered the system fresh each time.
When three separate agents all flagged multi-word column quoting as fiddly, that
was a real signal, not a hypothetical concern.

**Progressive context reduction.** The first agent got "no docs, just the source code"
(3.5/5). The next got "there's a Python library, use it" (4/5). Eventually agents
got only the README, and the scores stabilized at 4/5. This progression told us
exactly when the documentation was "good enough" — when removing more context
stopped hurting the score.

**Lead as architectural compass.** The two most impactful changes in the session
came from the Lead, not from agent feedback:

1. **The checkout/edit/checkin refactor.** Agents were happily calling `submit()` in
   loops and rating the system 4/5 — they didn't know they were bypassing the
   intended ALCOA+ workflow. The Lead saw this and redirected: the file IS the
   interface. This was a principle-driven correction that no amount of agent testing
   would have surfaced, because the agents had no concept of ALCOA+.

2. **Prerequisite enforcement across checkin cycles.** Same pattern — agents would
   cheerfully execute rows out of order in a single script and call it done. The Lead
   caught that same-cycle execution would produce identical timestamps, which an
   auditor would reject. Again, a domain-knowledge intervention that testing alone
   couldn't discover.

This reveals the shape of the loop more precisely: **agents find usability problems;
the Lead finds compliance problems.** Both are essential. Agent feedback optimizes
the surface; Lead feedback protects the invariants.

### What the scores tell us

| Test | Context Given | Interface | Score | Key Learning |
|------|--------------|-----------|-------|--------------|
| 1 | Source code only | submit() | 3.5 | Naming matters (checkout/checkin confused) |
| 2 | Minimal prompt | submit() | 4 | State must persist across loads |
| 3 | Minimal prompt | submit() | 4 | Need template API, progress counter, id_prefix |
| 4 | Source code only | submit() | 4 | view_all needed; confirms quoting issue |
| 5-7 | README only | submit() | 4, 4, 4 | README is sufficient; multi-agent pipeline works |
| 8-10 | README only | file-based | 4, 4, 4 | File workflow works; same quality as submit() |
| 11 | README only | file-based | 5 | Prerequisite blocking nailed on first try |

The 3.5 -> 4 jump came from fixing basic usability (naming, examples, persistence).
The stable 4 plateau across tests 2-10 reflects a system that works but has minor
documentation gaps. The 5 on test 11 suggests that when we implement features
with the accumulated design knowledge (clear visual states, good error messages,
proper enforcement), the result is immediately polished.

### What this means for DocuBuilder's next phase

The genesis sandbox served its purpose: we broke through analysis paralysis and
produced a working system that 11 different agents can use successfully. The
prototype now has real shape — not the shape we imagined during weeks of design
exploration, but the shape that emerged from actual use.

The system already supports the core document lifecycle (author, seal, template,
finalize, execute, amend) with ALCOA+-aligned controls (file-based workflow,
prerequisite enforcement, audit trails, timestamp separation). The RS requirements
we drafted are largely validated by working code. The remaining RS items
(calculated columns, section visibility, work instructions, cross-document references,
property namespaces) are extensions, not foundations.

The rapid prototyping loop itself is reusable: for any future subsystem where we're
stuck in design, we can spin up a sandbox, build the minimum, and let agents tell
us what's missing. It's empirical design — and it works.
