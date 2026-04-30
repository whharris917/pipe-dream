# Session-2026-04-29-002

## Current State (last updated: end of session)
- **Active document:** None (engine-submodule direct work on `dev/content-model-unification`)
- **Current EI:** N/A
- **Blocking on:** Nothing
- **Next:** Per Lead. Forward plan now centers on the terminal-execution primitive (Exec/Command Action variant) that lets cr-create's Submit actually mint a real CR. Three engine bugs surfaced during dogfooding deserve their own follow-up CRs. Live populated CR draft remains at /pages/27342915 for inspection.
- **Subagent IDs:** none

## Session start checklist
- [x] Determined this is a new session (today is 2026-04-29; previous session 001 from this date had a complete notes file with no compaction log)
- [x] Created `.claude/sessions/Session-2026-04-29-002/` and updated CURRENT_SESSION
- [x] Read previous session notes (Session-2026-04-29-001 — Experiment D unified Tabs/Sequence motif, six iterations)
- [x] Read SELF.md
- [x] Read QMS-Policy.md, START_HERE.md, QMS-Glossary.md
- [x] Read PROJECT_STATE.md
- [x] Inbox: empty
- [x] Submodule state: `qms-workflow-engine` on `dev/content-model-unification`, clean
- [x] Last engine commit: `5bc0579 Workshop Experiment D — unified Tabs vs Sequence visual motif`
- [x] Last root commit: `efcafc1 Session-2026-04-29-001: Bump engine — Experiment D unified Tabs/Sequence motif`

## Entry context
Auto mode active. Forward plan from PROJECT_STATE §6:

- **Immediate:** build real QMS workflows as component compositions; wire QMS/Workspace/Inbox to real data; triage demo pages.
- **Engine backlog (post-workflow):** decide whether Experiment A (drill-down + read-only ancestor tabs) or Experiment D (unified T-junction tabs / vertical sequence pills intersecting thread) becomes the canonical engine surface for Navigation containers; Graph Builder ↔ Razem alignment + compile-to-Razem; framework rename `qms-workflow-engine` → Razem.

Standing by.

## Progress Log

### [bootstrap] Session bootstrapped
- Folder created, CURRENT_SESSION updated to Session-2026-04-29-002, prior context loaded.
- No queued work; standing by for Lead direction.

### Conversation — Lead reframed Razem's purpose
- Opened with self-reflection: "I've become overly obsessed with perfection in my attempt to build Razem before I ever put it into practice." Confirmed honestly: every recent session has been workshop / motif iteration; "Build real QMS workflows" has been §6.1 immediate in PROJECT_STATE for weeks without progress. Recommended the smallest real workflow page on the existing engine.
- Lead noted Razem has no terminal-execution primitive — my first suggestion (CR-create wired to `qms create`) assumed a capability that doesn't exist. I offered three flavors (in-process Python import, HTTP to qms-mcp, subprocess to qms-cli) and a fallback (read-only Inbox first to surface composition gaps without the exec primitive).
- Lead corrected the framing: Razem's primary purpose IS to build a high-level, *constrained* API (with GUI for free) for qms-cli. Terminal execution is the load-bearing primitive, not a downstream feature. "Constrained API" reads as: engine permits arbitrary commands, page seeds curate which command shapes are exposed.
- Sketched an `Exec`/`Command`/`Run` Action variant: command template + sibling-bound arg substitution + structured result (stdout/stderr/exit/parsed doc_id) → bound store keys consumable by other components. Real design questions are around result surfacing, interactive prompts (qms-cli has some), timeout/streaming, post-success affordance recomputation.

### CR-create scaffolding page — first real QMS workflow on Razem
- Lead's direction: "create a new workflow at /portal by defining a new page under qms-workflow-engine/pages that represents the initial scaffolding of a Create Change Record workflow. Study the Quality Manual to understand the requirements of a compliant change record."

**Research read:**
- `QMS/TEMPLATE/TEMPLATE-CR.md` — full template structure. 12 sections; 1–9 are pre-approved (locked at pre-approval), 10 (Execution) and 11 (Execution Summary) are filled at execution time, 12 (References) authored at drafting + updated during execution. Sections 7.4 (Development Controls) and 7.5 (Qualified State Continuity) and impl phases 9.1/9.2/9.4–9.7 are code-CR-only.
- `Quality-Manual/04-Change-Control.md` — workflow lifecycle; review team composition; the approval gate; CLI command sequence (`qms create CR --title "..."` → checkout → checkin → route review → route approval → release → execute → route post-review → post-approval → close).
- `qms-workflow-engine/pages/__init__.py` — page seeds are auto-discovered from `pages/*.py`; each module exports `definition = Page(...)`. No registration step needed.
- `app/routes.py` /portal route — card grid of all discovered seeds; clicking "+ New Instance" spawns a UUID-keyed instance with its own JSON store.
- Engine surfaces: `engine/page.py`, `engine/textform.py`, `engine/choiceform.py`, `engine/listform.py`, `engine/tableform.py`, `engine/visibility.py`, `engine/action.py`, `engine/group.py`, `engine/navigation.py`, `engine/infodisplay.py`, `engine/sibling_ref.py`. Action's `depends_on` only reads same-scope siblings — important for placement decisions.

**Key design constraint discovered.** Visibility's `depends_on` resolves to siblings in the SAME scope as the Visibility component itself. A Visibility deep inside a Tabs+Group cannot reference a top-level page field. Implication: code-CR-only sections (7.4, 7.5) cannot conditionally appear inside the per-section Tabs based on `cr_type` at page level. Resolution for this scaffold: omit the code-CR-only sections entirely; document this in the seed's docstring as future work. Same constraint forced the page metadata fields (title, cr_type, parent_kind) to be direct page children rather than wrapped in a Group, so Submit's `depends_on=["title", ...]` resolves.

**Implementation:** `qms-workflow-engine/pages/cr_create.py` (~10K, ~330 lines).

Page structure:
- Header `InfoDisplay` — explains what a CR is and what this page captures.
- Page-level metadata: `TextForm` title (min 8 / max 120 chars), `ChoiceForm` cr_type (Document-only / Code CR), `ChoiceForm` parent_kind (None / INV / VAR / Other), `Visibility`-wrapped `TextForm` parent_doc_id (visible only when parent_kind ≠ None).
- `Tabs` "Pre-approved sections" with 10 step tabs (one per drafting-time CR section):
  - 1 Purpose (multiline TextForm)
  - 2 Scope (Group: context, changes_summary, files_affected ListForm)
  - 3 Current State (multiline)
  - 4 Proposed State (multiline)
  - 5 Change Description (multiline)
  - 6 Justification (Group: problem, impact_if_skipped, addresses_root_cause)
  - 7 Impact Assessment (Group: files_impact TableForm with cols [File, Change Type, Description], documents_impact TableForm with same cols, other_impacts multiline)
  - 8 Testing Summary (Group: automated_testing, integration_verification)
  - 9 Implementation Plan (ListForm of phases)
  - 12 References (ListForm)
- `InfoDisplay` "About Submit" — tells the user this is a stub.
- `Action` Submit — `depends_on=["title", "cr_type", "parent_kind"]`, `precondition_fn` requires non-empty title (8+ chars), `action_fn` returns the qms-cli command sequence that *would* run.

Component cross-section exercised: TextForm (single-line + multiline), ChoiceForm, ListForm, TableForm with fixed_columns, Group, Tabs, Visibility, Action, InfoDisplay. Real cross-section of Razem's primitives.

**Engine fix discovered en route.** Parity test `test_no_empty_url_affordances` filtered out DisabledAffordance offenders by checking if the label substring contained "disabled" — a fragile heuristic. component_gallery's similar guarded Action passes the test only because it's nested inside a Tabs that hides it from serialization when the tab isn't active. With my Action at page level (always serialized), the heuristic broke. Surgical fix: `engine/action.py` `DisabledAffordance.serialize()` adds `disabled: True` to the affordance dict, and `tests/test_parity.py` filters on that flag instead of label substring. Both are tiny changes that improve robustness for any future page that puts a guarded Action at top level.

**Verification:**
- Page binds and serializes cleanly (`Page.bind` + `_serialize_full` + `render` all succeed).
- Parity tests: 86/86 passing (was 79/79 in PROJECT_STATE; 7 new tests are the per-page parametrizations of the existing structural-bound suite — cr-create added 6 new param ids, plus one new pass for the test that previously had no equivalent for actions at page level).
- Live server (running on 127.0.0.1:5000):
  - `/portal` returns 200, "Create Change Record" card present.
  - POST `/instances` with `type=cr-create` mints instance `626bba10`.
  - GET `/pages/626bba10` renders 8286 bytes, JSON shows 7 top-level components (Visibility hidden because parent_kind unset — correct).
  - Setting title via POST `/pages/626bba10/title` flips Submit's `enabled` from false to true; `affordances` go from `[]` (DisabledAffordance) to `["Create Change Record (stub)", "Batch"]`.
  - Triggering Submit returns the expected stub preview: `would_invoke` = ["qms create CR --title \"Add particle emitter configuration panel\"", "qms checkout CR-NNN", "(write the populated section bodies into the CR markdown)", "qms checkin CR-NNN"].
  - Cleaned up the test instance.

Files changed:
- `qms-workflow-engine/pages/cr_create.py` (new, ~330 lines)
- `qms-workflow-engine/engine/action.py` (`DisabledAffordance.serialize` adds `disabled: True`)
- `qms-workflow-engine/tests/test_parity.py` (`extract_json_affordances` records `disabled`; `test_no_empty_url_affordances` filters on the structured flag)

### Dogfooding — populated the scaffold with a real hypothetical CR
- Lead's direction: "execute the workflow at /pages/27342915 for some hypothetical change. Let's say we wanted to qualify Flow State."
- Wrote a one-shot `fill_cr.py` loader script using the requests library (urllib hit a transient connection-reset on the dev server). Script POSTed to every field URL, including nested ones inside the Tabs container — `/pages/{inst}/sections/{step_key}/{field}` resolves regardless of which tab is currently active, so no tab-switching was needed.
- Content authored in the form (full text in the live page state):
  - **Title:** "Adopt Flow State under SDLC governance"
  - **CR type:** Document-only CR (this CR creates SDLC-FS-RS / SDLC-FS-RTM, not flow-state code modifications)
  - **Parent kind:** None — independent change
  - **Purpose:** Establish formal SDLC governance over Flow State by authoring SDLC-FS-RS and SDLC-FS-RTM as EFFECTIVE controlled documents and recording a qualified commit on flow-state's main branch.
  - **Scope:** genesis-sandbox-to-adoption framing per SOP-005 §7.4 / QMS-Policy §7.4. Files affected: SDLC-FS-RS.md (new), SDLC-FS-RTM.md (new), .claude/PROJECT_STATE.md (modify), flow-state submodule pointer (modify).
  - **Current State:** Flow State exists as working code but is NOT under SDLC governance — no RS, no RTM, no qualified commit, no merge-gate enforcement, existing tests not traced to formal requirements.
  - **Proposed State:** Flow State is a qualified system per SOP-006. RS and RTM both EFFECTIVE; future code changes flow through CRs that update RS/RTM together; merge gate prevents unqualified code from reaching main.
  - **Change Description:** 8-step plan covering inventory, RS authoring grouped by domain (REQ-FS-SCENE/SKETCH/SIM/COMPILER/TOOLCONTEXT/UI/PERSIST), test-suite run, integration verification, RTM authoring, RS review/approval, RTM review/approval, submodule pointer + PROJECT_STATE update.
  - **Justification:** problem (complexity outside governance, no merge-gate protection); impact-if-skipped (qualification gets harder over time, defects unanchored); root-cause-addressed (QMS already provides the mechanism via SOP-005/SOP-006 — this CR is the adoption, not new machinery).
  - **Impact Assessment:** 4-row Files table + 3-row Documents table + multi-paragraph other_impacts (workflow tightens, in-progress branches must be closed, increased reviewer load on tu_sketch/tu_sim/tu_scene/tu_ui).
  - **Testing Summary:** automated (run existing pytest, capture pass count and any failures as RTM evidence) + integration (launch via `python flow-state/main.py --mode sim`, exercise Brush/Line/Select tools, verify constraint solver with mouse-driven Interaction Constraints, undo/redo, Compile cycle).
  - **Implementation Plan:** 12-phase ordered list from inventory through PROJECT_STATE update.
  - **References:** 11 entries — SOP-001/002/005/006, QMS-Policy §7-§8, Quality-Manual/09-10, etc.
- After population: Submit Action `enabled: true`, page `is_complete: true` (after cleanup of stray empty table rows — see below). Stub Submit returned the expected `would_invoke` sequence: `qms create CR --title "Adopt Flow State under SDLC governance"` → `qms checkout CR-NNN` → `(write populated section bodies)` → `qms checkin CR-NNN`.
- Cleaned up `fill_cr.py` and the debug JSON capture after verification.

### Engine bugs found during dogfooding

1. **`Page._do_reset` does not clear TableForm cell data on Windows.** After resetting the page and re-running the loader, the impact tables retained empty rows from a prior partial run. Suspect: the JSON store's atomic-write rename pattern occasionally leaves orphaned cell data, OR _clear_recursive doesn't reach into typed table internal scopes the way it should. Workaround in this session: iteratively `remove_row` on empty rows. Worth a follow-up CR.

2. **JSON store atomic-write hits Windows file-lock race.** Werkzeug dev server returned HTTP 500 with `PermissionError: [WinError 5] Access is denied: 'data\\27342915.json.tmp' -> 'data\\27342915.json'` on rapid sequential POSTs. The .tmp-then-rename pattern fails when the target file is being read by another request thread. Reproduces consistently with table operations that issue add_row + N set_cell calls back-to-back. Workaround in the loader: retry-with-backoff. The proper fix is to add Windows-aware retry inside the Store, or to serialize per-instance writes via a per-instance lock.

3. **`add_table_rows` script logic over-counted by one.** TableForm seeds row_0 as an empty row when `fixed_columns` is set. My loader called add_row before each set, leaving an extra empty row at the end. Cosmetic in the loader, but the underlying engine behavior (auto-seeded row appears in JSON immediately) is something authoring tools have to know. Document this as a footnote in any future loader.

### Submit returned the expected stub
Final populated CR is live at /pages/27342915. Submit's `would_invoke` previews exactly what the real Submit will run once the terminal-execution primitive lands. The page is the diagnostic for the next concrete piece of engine work.
