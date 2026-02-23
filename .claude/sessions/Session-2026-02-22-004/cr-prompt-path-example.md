# Example: Interactive CR Prompt Path (qms-cli Code Change)

**Source:** Ghost Session (Session-2026-02-22-004 was active for a different task; this discussion occurred in a parallel session)

**Context:** This is a worked example of what a CR authoring session would look like through the proposed interactive workflow engine. The example CR adds a `qms diff` command to qms-cli. The walkthrough covers drafting through EI table construction — not execution.

Annotations in `[engine: ...]` show the workflow engine's internal logic. The `SOP` callouts show where the process layer (SOP dispensation) injects guidance at the moment of relevance.

---

## Phase 1: Framing

```
━━━ cr.title ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  What is the title of this change?

> Add `diff` command to compare document versions

━━━ cr.purpose ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  What problem does this CR solve, or what improvement does it
  introduce?

> The QMS CLI has no way to compare two versions of a document.
> Users must manually read archived versions and spot differences.
> This CR adds a `qms diff` command that produces a unified diff
> between any two versions of a controlled document.

━━━ cr.context ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  What is the origin of this change? Reference a parent document
  (INV, CAPA) if applicable, or describe the driving context.

> Independent improvement identified during Session-2026-02-22.
> No parent document.
```

`[engine: records parent_doc = None; no INV/CAPA cross-reference needed]`

---

## Phase 2: Change Classification

These prompts don't map to a specific CR section — they shape the rest of the workflow.

```
━━━ cr.change_type ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  What type of change is this?
  (a) Code change to a governed system
  (b) Document-only change (SOPs, templates, controlled docs)
  (c) Mixed (code + documents)

> a
```

`[engine: change_type = "code"; enables code CR sections (7.4, 7.5, phases 1-7)]`

```
━━━ cr.target_system ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Which governed system does this CR modify?

  Known systems:
  • qms-cli  (SDLC-QMS, submodule, CLI-14.0, commit d73f154)
  • flow-state  (SDLC-FLOW, submodule)

> qms-cli
```

`[engine: loads system profile — SDLC namespace "QMS", submodule, current release CLI-14.0, qualified commit d73f154, RS at v18.0, RTM at v23.0, 673 tests. This data drives auto-population of Sections 7.4, 7.5, and the EI table structure.]`

```
━━━ cr.adds_requirements ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Does this change add or modify requirements in SDLC-QMS-RS?

  ⓘ  SOP-006 Section 7.4: If the CR touches code in an
     SDLC-governed system, the RTM must reflect the qualified
     state — even if no RS/RTM content changes.

> Yes — new requirements for the diff command behavior.

━━━ cr.modifies_templates ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Does this change modify any QMS templates?

  ⓘ  Templates exist in two locations (QMS/TEMPLATE/ and
     qms-cli/seed/templates/). Both must be updated and
     QA verifies alignment during post-review (SOP-002 §7.3).

> No
```

`[engine: adds_requirements = true → include RS update phase, RTM update phase, and RS/RTM in EI table. modifies_templates = false → skip template alignment EIs.]`

---

## Phase 3: Before/After

```
━━━ cr.current_state ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Describe the current state. Concise, declarative, present tense.

> The QMS CLI provides `read` with `--version` to view a specific
> archived version, and `history` to see the audit trail. There is
> no command to compare two versions side-by-side. Users who want
> to see what changed between versions must read each separately.

━━━ cr.proposed_state ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Describe the proposed state. Same style.

> The QMS CLI provides a `diff` command that accepts a document ID
> and two version specifiers. It produces a unified diff showing
> additions, deletions, and context lines. Defaults to comparing
> the current effective version against the current draft (if one
> exists).
```

---

## Phase 4: Technical Detail

```
━━━ cr.change_description ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Full technical description of the change. Structure freely —
  use subsections, code snippets, diagrams as needed. This is
  the most flexible section.

> ### Command Interface
>
> `qms diff DOC_ID [--from VERSION] [--to VERSION] [--context N]`
>
> Default behavior: `--from` is the effective version, `--to` is
> the current draft. If no draft exists, error with guidance.
>
> ### Implementation
>
> New file: `commands/diff.py`
> - Resolves version specifiers to file paths (effective, draft,
>   or archived via `.archive/`)
> - Reads both versions, strips frontmatter
> - Produces unified diff via `difflib.unified_diff`
> - Colorized output when stdout is a terminal
>
> Integration: register in `qms.py` argument parser.
>
> ### Edge Cases
>
> - Comparing a version to itself: empty diff, info message
> - Non-existent version: error with available versions listed
> - Document with no archive: only effective ↔ draft comparison
```

---

## Phase 5: Files and Impact

```
━━━ cr.files_affected ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  List each file affected and describe the change.

> - `qms-cli/commands/diff.py` — Create: new diff command module
> - `qms-cli/qms.py` — Modify: register diff subcommand
> - `qms-cli/tests/test_diff.py` — Create: unit tests for diff
> - `QMS/SDLC-QMS/SDLC-QMS-RS.md` — Modify: add diff requirements
> - `QMS/SDLC-QMS/SDLC-QMS-RTM.md` — Modify: add verification

━━━ cr.documents_affected ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Which controlled documents will be modified or created?

> - SDLC-QMS-RS — add REQ-MCP-xxx requirements for diff
> - SDLC-QMS-RTM — add verification entries for new requirements

━━━ cr.other_impacts ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Any other impacts? External systems, interfaces, dependencies.

> None. The diff command is read-only and introduces no new
> dependencies.
```

---

## Phase 6: Development Controls (auto-populated)

`[engine: change_type = "code" AND target_system = "qms-cli" → auto-generate Section 7.4 and 7.5 from system profile. Present for confirmation, not freehand authoring.]`

```
━━━ cr.dev_controls (auto-populated) ━━━━━━━━━━━━━━━━━━━━━━━━━━

  Based on target system "qms-cli", the following development
  controls will be included in Section 7.4:

  1. Dev location: .test-env/qms-cli/ (local) or /projects/qms-cli/ (container)
  2. Branch: cr-101
  3. Write protection: .claude/settings.local.json blocks qms-cli/
  4. Qualification: all tests pass before merge
  5. CI: GitHub Actions pass on dev branch
  6. PR gate: merge via PR only
  7. Submodule update: after PR merge only

  Section 7.5 (Qualified State Continuity):

  | Phase          | main branch  | RS/RTM          | Release    |
  |----------------|-------------|-----------------|------------|
  | Before CR      | d73f154     | EFFECTIVE v23.0 | CLI-14.0   |
  | During exec    | Unchanged   | DRAFT           | CLI-14.0   |
  | Post-approval  | Merged      | EFFECTIVE v24.0 | CLI-15.0   |

  Confirm or modify?

> Confirmed.
```

---

## Phase 7: Verification Planning

```
━━━ cr.automated_testing ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ⓘ  SOP-002 §6.8: Code CRs must address both automated
     verification AND integration verification.

  Describe the automated verification approach.

> New tests in test_diff.py:
> - test_diff_effective_vs_draft: basic comparison
> - test_diff_archived_versions: compare two archived versions
> - test_diff_no_draft_error: error when no draft exists
> - test_diff_same_version: empty diff message
> - test_diff_nonexistent_version: error with version list
> - test_diff_frontmatter_stripped: frontmatter excluded from diff
>
> Full existing test suite (673+) must continue to pass.

━━━ cr.integration_testing ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Describe the integration verification approach — what will be
  exercised through user-facing levers in a running system?

  ⓘ  This is distinct from automated tests. Integration
     verification demonstrates the change works as a user
     would experience it. Evidence is captured in a VR.

> Exercise the diff command against real QMS documents:
> 1. Diff an SOP with archived versions (multi-version history)
> 2. Diff a document with an active draft vs effective
> 3. Attempt diff on a non-existent version (verify error)
> 4. Verify colorized output in terminal

━━━ cr.needs_vr ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Based on your integration testing plan, which execution items
  should require a Verification Record?

  ⓘ  SOP-004 §9C: VRs provide auditable behavioral evidence.
     Mark EIs that exercise user-facing functionality with VR=Yes
     during planning. The VR ID replaces "Yes" during execution.

> The integration verification EI (exercising the diff command
> against real documents).
```

`[engine: records vr_flag for integration verification EI]`

---

## Phase 8: EI Table Selection (variant-based)

The engine does not interactively construct or edit the EI table. The classification flags from Phase 2 programmatically select a pre-defined EI table variant. Mandatory/structural EIs are fixed and non-removable. The engine only prompts for task descriptions in the content-specific slots.

`[engine: classification flags → variant selection]`
`[  change_type = code         → include: test env, qualification, merge gate]`
`[  adds_requirements = true   → include: RS update, RTM update]`
`[  modifies_templates = false → exclude: template alignment]`
`[  has_vr = true              → set VR=Yes on integration verification EI]`
`[  selected variant: code-cr + adds-requirements + has-vr]`

The fixed EIs are presented as context. The engine then prompts only for the content-specific slots:

```
━━━ cr.ei_table (variant: code-cr + adds-requirements + has-vr) ━━━

  Your EI table structure (determined by change classification):

  │ EI-1 │ Pre-execution baseline: commit and push         │     │
  │ EI-2 │ Set up test environment, create branch cr-101   │     │
  │ EI-3 │ Update RS to EFFECTIVE                          │     │
  │ EI-4 │ ← your implementation work (see below)          │     │
  │ EI-5 │ Run full suite, push, CI, qualified commit      │     │
  │ EI-6 │ ← your integration verification (see below)     │ Yes │
  │ EI-7 │ Update RTM to EFFECTIVE                         │     │
  │ EI-8 │ Merge gate: PR, merge (--no-ff), submodule      │     │
  │ EI-9 │ Post-execution baseline: commit and push        │     │

  EI-1, EI-9: mandatory (SOP-004 §5)
  EI-2, EI-5, EI-8: required for code CRs (SOP-005 §7.1)
  EI-3, EI-7: included because adds_requirements = true
  EI-6: VR=Yes per your integration testing plan
```

```
━━━ cr.ei_implementation ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Describe the implementation work for EI-4.

> Implement diff command (commands/diff.py) and unit tests
> (tests/test_diff.py) on branch cr-101. Register subcommand
> in qms.py.

━━━ cr.ei_integration_verification ━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Describe the integration verification for EI-6.
  This EI will have an attached VR.

> Exercise diff command against real QMS documents: compare
> archived SOP versions, diff effective vs active draft,
> verify error handling for non-existent versions, confirm
> colorized terminal output.
```

`[engine: inserts author responses into EI-4 and EI-6 task descriptions. Table is complete.]`

---

## Summary: What The Engine Contributed

The author provided **16 substantive responses** across the session. From those, the engine will compile a complete CR with all 12 sections populated. Key engine contributions:

| Contribution | How |
|---|---|
| **Section 7.4 (Dev Controls)** | Auto-populated from system profile |
| **Section 7.5 (Qualified State)** | Auto-populated with current commit, RS/RTM versions, release number |
| **EI table variant** | Selected programmatically from classification flags — not interactively edited |
| **Mandatory EIs** | Fixed, non-removable, with SOP citations |
| **Conditional EIs** | Included/excluded by classification flags, not by author choice |
| **VR flagging** | Set on integration verification EI when `has_vr = true` |
| **SOP guidance** | Surfaced at moment of relevance, not as a wall of text at session start |

**Design constraint:** The engine is entirely programmatic. It does not interpret natural language, negotiate table edits, or act as an AI agent. It is a state machine that presents prompts, records responses, selects template variants based on flags, and compiles output. All structural decisions are deterministic from the classification inputs.

The prompt sequence follows the **author's thinking** (what -> why -> how -> verify -> plan), while the compiled document follows the **reader's structure** (Sections 1-12 in template order). The decoupling between workflow and rendering is what makes this possible.

---

**END OF DOCUMENT**
