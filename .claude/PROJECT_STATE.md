# Project State

*Last updated: 2026-05-12 (Session-2026-05-11-001 continued — emergent-phenomena stack: R1 per-pair LJ ε override mechanism + R2 palette (4 new materials, 4 seeded cross-pair overrides, 3 new molecule helpers) + R3 demo presets + UI surfaces (Demos menu, Tools→Cross-ε editor, LjOverrideDialog) + two render/hit-rect bug fixes. Suite 801 → 937 passing + 1 skipped, +136 tests.)*

Living planning document for Pipe Dream. Tracks where the project is, what's next, and what's waiting. Per CLAUDE.md it is pruned aggressively and **does not accumulate session-level detail** — for that, read the relevant session's notes.md.

---

## 1. Project Overview

Pipe Dream has two intertwined objectives:

- **Flow State** — a Python application combining a geometric constraint solver (CAD) with a particle-based physics engine.
- **The QMS** — a GMP-inspired Quality Management System governing AI agent orchestration, with a recursive governance loop where the QMS controls its own evolution through the same mechanisms it uses to control application code.

Current center of gravity: Flow State (beach-trip arc). The Razem framework (in `qms-workflow-engine/` submodule, rename queued) is paused; will host the QMS's own UI as the first real application built on it.

---

## 2. Current Status

**Active focus:** **CR-116 IN_EXECUTION v1.2** — first Exploration CR (free-form Flow State beach-trip work). EI-1 + EI-2 Pass; EI-3 (free-form exploration) active and expected to remain so for the trip duration. Branch `cr-116-beach-trip-exploration` from `flow-state/main@da012b4`. Will close out as FLOW-STATE-1.3 when Lead chooses to qualify. Latest test suite: **937 passing + 1 skipped** (Session-2026-05-11-001 continued through 2026-05-12; +136 from session start). For round-level detail of recent work, see relevant session notes; high-level arcs are listed in §3.

**CR-115 (Permit Exploration CRs under existing scope-integrity machinery) — CLOSED v2.0.** Two-round design collaboration produced a lighter-touch design rejecting artifact proliferation. Six clarifying additions: QMS-Policy §6, SOP-002 §6.2 + §7.1, qa.md `## Exploration CRs` section, scope-change-guide.md. No new artifacts/templates/SOPs. QM submodule advanced `e1755e3` → `c6a0a04`. Pre/post split worked as designed: post-review caught a verbatim-sourcing over-claim that pre-review couldn't have foreseen. Closure: pipe-dream@`a05cb31`.

**CR-114 (Resize World UX + brush_tool orphan deletion) — CLOSED v2.0.** First post-CR-113 Flow State CR. Bundled: InputField visibility fix; generic `ConfirmDialog` widget; deletion of orphan `ui/brush_tool.py`. Qualified flow-state@`f69455f` reachable from main via merge `da012b4`; **FLOW-STATE-1.2** tag. SDLC-FLOW-RS unchanged, SDLC-FLOW-RTM v3.0 EFFECTIVE with line-citation re-anchors. Seven pre-review + four RTM cycles + one in-scope regression fix surfaced more procedural cost than the change deserved; Lead flagged token cost as untenable. Two limitations deferred and later landed in CR-116 (ResizeWorldCommand, bounds clipping). Closure: pipe-dream@`89b5a77`.

**CR-113 (Agent definition + Quality Manual cleanup, CR-112 retrospective) — CLOSED v2.0.** Document-only CR addressing eight friction points from CR-112. Outcomes: 4 TU agent files had stale references removed; tu_sketch + tu_sim "one-way bridge" framing corrected to two-way coupling; project-specific Reviewer Assignment table added to qa.md (Quality Manual stays generic); all 6 agent files got Invocation Modes (Task tool + containerised paths). QM changes via SOP-005 §7.1 execution-branch + PR + regular-merge in submodule (QM master `5650425` → merge `e1755e3`). Establishes precedent: documentation submodules follow full execution-branch workflow without RS/RTM gates. Closure: pipe-dream@`d62c396`.

**CR-112 (ToolContext Migration Completion + Documentation Reconciliation) — CLOSED v2.0.** Bundled CR fixing SourceTool ToolContext-migration miss (first post-CR-111 user crash) plus three CR-111 follow-ups (Tool base-class `self.app` cleanup, `ctx.set_interaction_data` adoption, CLAUDE.md drift). Qualified flow-state@`ec450e2` reachable from main via merge `c82c8e2`; **FLOW-STATE-1.1** tag. CLAUDE.md drift corrected across §§2.2, 2.3, 4.2, 5.3, 5.4, 5.5, 6.2, 7. Closure: pipe-dream@`453195d`.

**71 CRs CLOSED, 5 INVs CLOSED, 1 CR IN_EXECUTION (CR-116).**

**SDLC docs:**
| Document | Version | Notes |
|----------|---------|-------|
| SDLC-QMS-RS | v22.0 EFFECTIVE | 143 requirements |
| SDLC-QMS-RTM | v27.0 EFFECTIVE | 687 tests, qualified at `918984d` |
| SDLC-CQ-RS | v2.0 EFFECTIVE | 6 requirements |
| SDLC-CQ-RTM | v2.0 EFFECTIVE | Inspection-based, qualified at `d3c34e5` |
| SDLC-FLOW-RS | v3.0 EFFECTIVE | CR-112 strengthened REQ-FS-ARCH-004/CAD-003 |
| SDLC-FLOW-RTM | v3.0 EFFECTIVE | CR-114 EI-10 — qualified at flow-state@`f69455f` |
| SDLC-WFE-RS | v0.1 DRAFT | Razem track; rewrite deferred while Flow State is active |
| Qualified Baselines | CLI-18.0 + FLOW-STATE-1.2 | qms-cli main `309f217`; flow-state main `da012b4` |

**Razem engine** (paused): 26 component classes, 12 page seeds (incl. cr-create scaffold), 7 themes, 86/86 parity tests. The MCP-call primitive (reframed from "terminal-execution primitive") remains the load-bearing missing piece. Engine track resumes after the beach trip.

---

## 3. Arc to Date

Full per-session record in `.claude/sessions/`. Compressed phase narrative:

- **QMS Foundation (Jan – Feb 24).** ~80 sessions establishing document control: CR/INV/VAR/ADD/VR types, SOP-001 through SOP-007, Quality Manual, qms-cli, agent orchestration, recursive governance loop.
- **Workflow Engine v1 → v2 → Unification (Mar 3-19).** CLI graph engine; web UI + Agent Portal sandbox; clean-room rewrite into single runtime with LNARF spine representation.
- **Restructure + Workshop Era (Mar 20-25).** Multi-instance; AffordanceSource protocol; workshop-driven exploration. Architectural audit eliminated YAML; **all engine code deleted and rebuilt from scratch** — foundation of current Razem.
- **Component Expansion (Mar 26-31).** Fractal complexity plan: Switch, registry, persistence, actions, self-modifying pages. 30+ component types. Theoretical re-examination revised "Component" meaning from self-contained → identity-preserving under transformation (HATEOAS-completeness).
- **Rendering Modernization + HTMX Detour (Apr 1-4).** Event delegation (XSS-eliminated structurally); CSS extraction; Jinja2 templates with parity tests; HTMX excised after eval. Stateless server refactor; instance spawning.
- **Affordance & Container Consolidation (Apr 4-5).** Affordance flotation; container nav O(N)→O(1); InfoDisplay; Embedded Page; Supervisor/Operator + Sleek theme.
- **Sleek Theme Polish + Documentation/Framing/Naming (Apr 5-18).** Edit-mode unification; structural editor; Eigenform→Component rename; class taxonomy refactor (`*Form`/containers unsuffixed/`*Display`/`*Action`/`*Runner`/`*App`); action-dispatch registry. Framework named **Razem** (Polish, "together"). Wiki, Learning Portal, Components Reference.
- **Workshop Hub + Nesting + Graph Builder (Apr 18-28).** Right-click inspect panel; Navigation split into Tabs/Sequence/Accordion; 5 new themes (paper, chat, task, debug, liquid-glass). **Experiment A** converged in nesting workshop (drill-down on thread + read-only ancestor tabs + Change selection pill). **Graph Builder** workshop rebuilt across 12 iterations: railroad-track wiring, containers-as-concept, recursive page-builder for Tabs/Sequence/Group.
- **Strategic Refocus + Beach-Trip Pivot (Apr 13, 29-30).** Lead refocused: stop side quests, build QMS for Flow State. Then shelved Razem entirely for beach trip; returned to Flow State with existing QMS as governance vehicle.
- **CR-111 Adopt Flow State (Apr 30).** CR-111 closed v2.0 with 10/10 EIs Pass. SDLC-FLOW-RS v1.0 + SDLC-FLOW-RTM v0.2 EFFECTIVE. **FLOW-STATE-1.0** tag at `a26f7fb`. QMS surfaced ~9 pieces of latent architectural knowledge through review cycles.
- **CR-112 + Razem/MCP Framing (Apr 30 – May 1).** CR-112 closed v2.0 with **FLOW-STATE-1.1** at `ec450e2`/`c82c8e2`. CLAUDE.md drift corrected. Parallel arc: long Razem/MCP discussion crystallized vision — Razem as interface generator for MCP servers; documentation lives in the interface; parity rule (humans can only do what agents can do). MCP-call primitive is the load-bearing piece. Framing captured in `.claude/sessions/Session-2026-04-30-002/design-discussion.md`.
- **Architecture Atlas + CR-113 + CR-114 (May 2-3).** Built `flow-state-architecture-atlas.html` (~2300 lines) covering codebase + tool-facade follow-up. CR-113 closed v2.0 (QM cleanup, retrospective). CR-114 closed v2.0 (**FLOW-STATE-1.2**); procedural cost flagged as untenable; reviewer model downgrade queued.
- **CR-115 + CR-116 (May 4-5).** CR-115 closed v2.0 establishing Exploration CR pattern (lighter touch, rejected artifact proliferation). CR-116 opened as first Exploration CR; beach-trip free-form Flow State work begins.
- **CR-116 EI-3 Active (May 3 – present).** Free-form exploration: 489-test regression suite; six TU-driven fixes; thermostat perf arc (Berendsen serial 2-30× faster); parallel atom-centric LJ pair loop (6-7× speedup); LJ benchmark suite + parallel `build_neighbor_list` (60-fps ceiling moves N≈15k → N≈20-25k); periodic boundary conditions as third boundary mode; F7 render-mode toggle (FULL/DOTS/OFF); Newton-3 kernel as opt-in (1.42× at N=5k crossover); Sink ProcessObject; Source Properties dialog with material palette; `rate`→`flux` intensive-metric refactor; SmartSlider/MiniSlider auto-expand fixes; **per-particle mass** physics engine refactor (kernel scalar→array, 4 sites classic + 5 Newton-3); per-substep medium drag (slider was wall-only); **Molecule Builder** (R1-R4: bond engine + data model + placement tool + dialog + palette); R5 Maxwell-Boltzmann COM velocity at placement (thermostat-can't-heat-from-zero fix); R6 three-body angle springs `U=k(θ-θ_eq)²` + four new starter molecules (CO₂, ammonia, methane, benzene). Suite trajectory 327 → 489 → 513 → 523 → 653 → 801 passing + 1 skipped.
- **CR-116 EI-3 Emergent-Phenomena Stack (May 11-12, Session-2026-05-11-001).** Designed and shipped the mechanism + palette + presets + UI for coarse-grained MD demos (oil-water demixing, surfactant micelles, polymer dynamics, crystal annealing). **R1:** per-pair LJ ε override mechanism — breaks Berthelot's geometric-mean rule via `Sketch.lj_cross_overrides: dict[frozenset, float]`. Plumbed through `Simulation.atom_material_id` array + `eps_ij_matrix` + both kernels (classic + Newton-3) + all atom-creation sites (Source, brush, Compiler, AddMoleculeCommand) + Scene.rebuild matrix push. -1 material_id falls back to per-atom ε_sqrt (legacy path preserved). +31 tests. **R2:** palette — 4 new materials (Polar/Nonpolar matched-σ for clean demixing, Heavy dense/slow, LightGas vapor-at-typical-T) + 4 seeded cross-pair overrides (Polar-Nonpolar 0.25, Polar-LightGas 0.15, Heavy-LightGas 0.20, Nonpolar-Heavy 1.5) seeded only on fresh `__init__` (not on restore — legacy saves stay legacy) + 3 new molecule helpers (`make_surfactant` 5-atom amphiphile, `make_lipid` 6-atom Y-shape with 60° tail splay, `make_polymer` 15-atom chain). Fresh Sketch now ships with 9 starter molecules. +40 tests. **R3:** `core/demo_presets.py` with `preset_demixing` / `preset_micelles` / `preset_crystal_anneal` — each clears the sim, sets physics params, populates state with Maxwell-Boltzmann velocities, pushes the current eps_ij_matrix. Deterministic when given a seed. Plus end-to-end demixing-phenomenology test: 5000 substeps from random initial state → nearest-LIKE-neighbour distance becomes clearly smaller than nearest-UNLIKE — the matched-σ Polar/Nonpolar pair (R2 design) was specifically chosen to make this signal robust. +20 tests. **UI surfaces:** menu bar `Tools→Cross-ε Overrides...` opens the new `LjOverrideDialog` (two material dropdowns, ε input, Apply/Reset/Done, active-overrides list panel up to 7 rows); menu bar `Demos` category with Demixing/Micelles/Crystal Anneal items; AppController.run_demo_preset auto-switches to MODE_SIM. +21 tests. **Bug fixes during the session:** (i) molecule-palette dropdown click fall-through — OverlayProvider protocol drew above the tree but didn't route events first; new `UIManager.try_dispatch_to_overlay` gives registered overlays first crack at MOUSEBUTTONDOWN events landing inside their overlay rect (+5 tests). (ii) menu dropdown render-order — MenuBar drew dropdown inside its own draw() (tree-order pass), then panels painted over it; split into `draw()` (bar only) + `draw_dropdown_overlay()` called from `UIManager._draw_overlays` so dropdown lands on top of everything (+11 tests). (iii) menu hit-rect drift — `handle_event` rebuilt item_rects with fixed width=60 but `draw()` used actual text width; clicking visually on "Demos" hit "Help" rect to its left; removed duplicate rebuild + dropped default `Help: []` from MenuBar.__init__ + `draw()` skips empty categories (+8 tests). Suite trajectory across the session: 801 → 806 (overlay fix) → 837 (R1) → 877 (R2) → 897 (R3) → 918 (UI) → 929 (menu render-order) → **937 passing + 1 skipped** (menu hit-rect).

---

## 4. What's Built

### Controlled documents

| Document | Status |
|----------|--------|
| SOP-001 through SOP-007 | All EFFECTIVE (latest revs: v21 / v17 / v3 / v9 / v7 / v5 / v2) |
| TEMPLATE-CR / VAR / ADD / VR | v10 / v3 / v2 / v3 EFFECTIVE |

### Razem engine (in `qms-workflow-engine/`)

Major surfaces — see `engine/` for full directory:
- **Core:** `component.py`, `page.py` + `page_mutations.py`, `store.py`, `registry.py`, `affordances.py`.
- **Data forms:** TextForm, NumberForm, DateForm, BooleanForm, ChoiceForm, CheckboxForm, MultiForm, ListForm, SetForm, TableForm, DictionaryForm.
- **Containers:** Tabs, Sequence, Accordion (Navigation base), Group, Repeater, Switch, Visibility.
- **Sibling-reading:** Computation, Validation, plus `SiblingBind` on any field.
- **Imperative / wrapper / runner / showcase:** Action, Historizer, TableRunner, RubiksCubeApp.
- **Display:** InfoDisplay.

### App + UI

Flask app at `app/`; 19 page seeds in `pages/`; main routes `/portal`, `/qms`, `/workspace`, `/inbox`, `/manual`, `/learn`, `/wiki`, `/components`, `/deepdive`, `/workshop` (sub-pages: page-builder, nesting, component-creation, graph-builder); per-theme CSS for sleek/debug/liquid-glass/paper/chat/task.

### Test surface

- `qms-workflow-engine/tests/test_parity.py` — 86 tests across 9 categories.
- `flow-state/tests/` — **937 passing + 1 skipped** end of Session-2026-05-11-001 (continued 2026-05-12).

---

## 5. Open QMS Documents

| Document | Status | Context |
|----------|--------|---------|
| **CR-116** | **IN_EXECUTION v1.2** | First Exploration CR. EI-1 + EI-2 Pass; EI-3 active. Branch `cr-116-beach-trip-exploration`. 937 passing + 1 skipped. |
| CR-110 | IN_EXECUTION v1.1 | Workflow engine. EI-1-4 Pass. EIs 5-7 need rescoping. Paused for beach trip. |
| CR-107 | DRAFT v0.1 | Unified Document Lifecycle. On hold. |
| CR-106 | DRAFT v0.1 | System Governance. Depends on CR-107. |
| CR-091-ADD-001-VAR-001 | PRE_APPROVED v1.0 | Type 2 VAR. CLI title bug + SOP-004/TEMPLATE-VR alignment gap. |
| CR-001 | IN_EXECUTION v1.0 | Legacy. Cancellation candidate. |
| CR-020 | DRAFT v0.1 | Legacy test document. Cancellation candidate. |
| INV-002 through INV-006 | Various | Legacy investigations. Low priority. |
| CR-036-VAR-002, -004 | IN_EXECUTION v1.0 | Legacy. Low priority. |

---

## 6. Forward Plan

### Immediate (Flow State track — active during beach trip)

1. **CR-116 free-form exploration continues.** EI-3 open through beach trip. Recent landings via Session-2026-05-10-001/002: Sink ProcessObject, Source Properties dialog + flux refactor, slider fixes, per-particle mass, per-substep damping, Molecule Builder (R1-R4), Maxwell-Boltzmann COM velocity (R5), angle springs + 6-molecule palette (R6). Known limitations carrying forward: (a) `AddMoleculeCommand.undo` truncation-based — loses particles added between place and undo; (b) no rotation control in molecule placement UX (right-drag-to-rotate is natural extension; `rotation` field already plumbed); (c) MoleculeBuilderDialog atom dropdown doesn't follow `session.active_material`.

2. **Process-improvement CR for QA-as-sole-assignee auto-close pattern.** Originally surfaced from 3 incidents across CR-113/114. Did NOT trigger in CR-115/116 — may be assign-then-RECOMMEND-ordering-specific. Worth observing through Exploration CR cycles before authoring. If recurs, candidate fixes: (a) hard guard in QA agent against submitting review while sole assignee; (b) CLI prevention of auto-close when assignee count == 1.

3. **First real gameplay/CAD/sim Flow State CR** — Lead picks the first feature. Performance headroom in hand (parallel LJ pair loop, parallel `build_neighbor_list`, PBC available).

4. **`lj_pbc` benchmark scenario.** Trivial — one scenario function + SCENARIOS-registry entry. Useful because PBC removes wall-collision energy loss confounding ns/atom-substep readings.

5. **`_draw_particles` vectorization (FULL_FAST mode).** Session-2026-05-08-001 confirmed renderer is bottleneck at moderate N (physics dominates at very high N). DOTS path's `pygame.surfarray.pixels3d` fancy-indexing is the prototype; a FULL_FAST mode doing same vectorized transform with blitted sprite stamps is natural next step.

6. **Physics LJ pair loop further wins (at high N).** Remaining levers: (a) reduce r_cut 2.5σ → 2.0σ (1.3-1.5× win, modest physics-fidelity tradeoff, needs Lead approval); (b) GPU offload via Numba CUDA (biggest scope); (c) multi-time-stepping RESPA; (d) packed (N,2) position memory layout; (e) auto-select kernel by N. Filed for Lead direction.

7. **Tool-facade architectural follow-up CR** (from CR-112 cycle 4 TU reviews). Three candidate paths: (a) rename `_get_sketch/_get_scene` to first-class facade methods; (b) typed read-only `SketchView` protocol; (c) eliminate Tool subclass `@property` accessors. Non-blocker. Architecture Atlas Part II analyzes all three. Lead's current preference: defer (Path A queued, revisit when forcing function emerges).

8. **Auto-mode-vs-subagent permissions resolution.** Either more specific allow-rule (`Bash(python qms-cli/qms.py --user qa *)`) or migrate QA approval flows to MCP tools. Did NOT bite in CR-114; possibly non-deterministic.

### Razem track (paused — resume after beach trip)

1. **MCP-call primitive (Action variant for MCP tool invocation).** Load-bearing piece. New Action variant invokes MCP tool with form-validated arguments, binds structured response into store keys. Engine speaks MCP; page seeds curate which MCP tools are exposed.
2. **Continue building real QMS workflow pages** (= page seeds for the QMS MCP server). CR review, document lifecycle, inbox actions, route-for-review/approval. cr-create is existing scaffold.
3. **Wire QMS / Workspace / Inbox to the QMS MCP server** rather than placeholder lists.
4. **Triage demo pages.** Decide which seeds in `/portal` are valuable vs gallery cruft.
5. **Framework rename: `qms-workflow-engine` → Razem.** Decided 2026-04-17-003. Scope: GitHub repo rename + remote URL + `.gitmodules` + CLAUDE.md refs + Framing page + README + Lessons + Deep Dive. Effort: one focused session.
6. **Retire `qms_interact` from MCP surface** once Razem-on-MCP renders the equivalent procedural flows.
7. **Long-term migration: documentation-in-the-interface.** Procedural Quality Manual content moves into Razem page seeds; policy content stays as meta-document. CLAUDE.md shrinks to ~200-500 tokens. Session notes eventually move into Portal.

### After workflows are working

- **Merge dev into main.** Dev branch preserved until confirmed working.
- **CR-110 remaining EIs.** Update for rebuilt engine.
- **SDLC-WFE-RS rewrite.** v1 requirements don't apply to rebuilt engine.

### Engine backlog (post-workflow)

| Item | Effort | Source |
|------|--------|--------|
| Concurrency model — last-write-wins, no conflict detection. Fine single-user; broken for collaboration. | Medium | Wiki Limitations §4 |
| Move showcase/runner demos to `engine/_examples/` (RubiksCubeApp, TableRunner). | Small | Deep Dive rec #7 |
| Delete `_migrate_legacy_overrides` with kill-date. | Trivial | Deep Dive rec #8 |
| Promote mutable-structure schematic editor out of `sleek/page.html`. | Medium | Deep Dive §5 #5 |
| Rename `form` class attribute (lowercase inconsistent with PascalCase). | Small | 2026-04-17-002 |
| Rename branch `dev/content-model-unification`. | Trivial | 2026-04-17-002 |
| Component class taxonomy follow-up — verify any stragglers. | Small | MEMORY.md |
| Nesting workshop follow-through. Two candidate engine surfaces: (a) Experiment A drill-down; (b) Experiment D unified Tabs/Sequence motif. Decide which becomes canonical. | Medium | Session-2026-04-25-001, 2026-04-29-001 |
| Graph Builder follow-through (post-rebuild). Align data model with Razem's seed model; compile-to-Razem; unified Page Builder combining Graph + Nesting. | Medium | Session-2026-04-27-001 |

**Correctly parked** (no concrete use case yet): Context primitive; first-class interception for containers; affordance flotation future phases; agent integration testing; perf/stress testing on large pages; error-boundary expansion.

---

## 7. Backlog

### Ready (no blockers)

| Item | Effort | Source |
|------|--------|--------|
| Fix CLI title metadata propagation | Small | CR-091-ADD-001-VAR-001 |
| Align SOP-004 §9C.4 with TEMPLATE-VR | Small | CR-091-ADD-001-VAR-001 |
| Govern checkin.py bug fix (commit `532e630`) via CR | Trivial | INV-012 |
| Delete `.QMS-Docs/` | Trivial | CR-103 |
| Standardize metadata timestamps to UTC ISO 8601 | Small | Session-2026-02-26-001 |

### Bundleable

- **Identity & Access Hardening** (~1 session) — proxy header validation, Git MCP access control.
- **Agent Hub Robustness** (~1-2 sessions) — C3 (root user), H4 (no hub shutdown on GUI exit), M6/M8/M9/M10.
- **GUI Polish** (~1-2 sessions) — H6, M3/M4/M5/M7, L3-L6.

### Deferred

| Item | Rationale |
|------|-----------|
| Remove EFFECTIVE status / rename to APPROVED | High disruption, low value. |
| Metadata injection into viewable rendition | No current pain point. |
| Consolidate SDLC namespaces into system registry | Depends on CR-106. |
| Interactive document write protection (REQ-INT-023) | Pending UI-based interaction design. |
| Remove stdio transport option from MCP servers | Low priority. |
| Propagate Quality Manual cleanup from workshop | Medium effort, not blocking. |
| **Downgrade reviewer agents (qa, bu, tu_*) from Opus to Sonnet via CR** | All 6 reviewer-class agent definitions in `.claude/agents/` set `model: opus`. Non-trivial Opus cost per review round. Each TU does focused-domain reading + commentary, not novel synthesis. Trivial frontmatter edit per file. Validate by spawning one agent per role on a real review task. Connects to §8 token-cost gap. |

---

## 8. Gaps & Risks

- **No MCP-call primitive in Razem.** Every QMS workflow page beyond static authoring needs it. cr-create Submit is honest about being a stub. Load-bearing engine work — see §6 Razem track.
- **MCP servers don't carry HATEOAS.** Catalog-shaped, not response-shaped. Razem's value-add is the application-state-machine layer MCP omits. Implication: page-seed authoring is high-leverage; auto-generation from MCP catalogs gets a starter form, not a workflow.
- **MCP returns prose, not structured shapes.** `qms_status` returns human-readable text; rendering it cleanly in Razem requires per-tool parsers OR structured outputs on QMS MCP server.
- **QMS engine versioning rule (CR-112 lesson):** drafts increment minor (v1.0→v1.1); approvals bump major (v1.1→v2.0). Misreading cost SDLC-FLOW-RS an extra cosmetic cycle.
- **Three engine bugs from cr-create dogfooding:** (a) `Page._do_reset` doesn't fully clear TableForm cell data on Windows; (b) JSON store atomic-write Windows file-lock race (`PermissionError: [WinError 5]`); (c) TableForm auto-seeds `row_0` when `fixed_columns` provided — surprising for authoring tools.
- **Visibility cross-scope limitation.** `depends_on` resolves to same-scope siblings only; conditional sections deep inside containers can't reference page-level fields.
- **SDLC-WFE-RS needs full rewrite** for rebuilt engine.
- **Auto-mode-vs-subagent-permissions friction.** Parent's auto-mode doesn't propagate to subagent tool prompts. Workaround: exit auto mode for QA approval spawns.
- **Legacy QMS debt.** Nine open documents from early iterations; bulk cleanup recommended after workflows ship.
- **`qms-workflow-engine` submodule pointer** must be kept current with pushes.
- **QA-as-sole-assignee auto-close pattern.** Recurring procedural tax — 3+ incidents in CR-113/114. Did NOT trigger CR-115/116. Worth structural fix before more code CRs if recurs.
- **`_draw_particles` renderer bottleneck at moderate N.** Physics improvements no longer user-visible until render path vectorized. See §6.5 above.
- **Token-cost-per-CR out of proportion to change size.** CR-114 shipped ~7 lines net new + 135-line dialog + 145-line deletion, consumed full subagent quota cycle. Sources: drafting errors, CLI duplicate-frontmatter bug, QA auto-close pattern, per-cycle reviewer fan-out. **Reviewer-agent model downgrade (Opus → Sonnet) queued in §7 Deferred** as partial mitigation.
- **CLI duplicate-frontmatter bug.** Some checkin operation prepends empty `---/{}/---` block to workspace file under unpinned conditions. Title parses as N/A. Cost a review cycle in CR-114. Needs qms-cli investigation.
