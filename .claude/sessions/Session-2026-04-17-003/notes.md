# Session-2026-04-17-003

## Current State (last updated: class taxonomy rename queued)
- **Active document:** None
- **Current EI:** N/A
- **Blocking on:** Nothing
- **Next:** Awaiting Lead direction. Two rename refactors now queued in PROJECT_STATE §5 ("Before First QMS Workflow Ships"): (4) Razem framework rename — Wiki landed, rest still TBD; (5) class taxonomy rename — entire scope captured, not executed. Plus (6) Navigation-split as post-workflow refactor.

## Context carried from Session-2026-04-17-002
- Eigenform → Component rename landed and pushed (submodule + root).
- Learning Portal live at `/learn` with 8 lessons (5 fundamentals + 3 deep dives).
- Wikipedia-style `/wiki` page live.
- Branch `dev/content-model-unification` is where all recent work is happening (submodule `qms-workflow-engine`).
- Parity tests green: 72/72.
- CR-110 IN_EXECUTION (v1.1). EI-1-4 Pass. Remaining EIs (5-7) need re-scoping.

## Known follow-ons (from prior session, not yet picked up)
1. `form` attribute — lowercase `form = "text"` class attribute (registry type identifier) is inconsistent with `Component` base. Candidates: `type`, `component_type`, or leave.
2. `dev/content-model-unification` branch name — no longer accurate; rename at next major checkpoint.
3. Callable-preservation diagnostic — planned Pass 2 follow-on; still silent today.
4. Action-dispatch-as-reducer — 88 branches across 20 files. `ActionRegistry` with named dispatch would formalize the pattern.

## Progress Log

### Session opened
- Initialized Session-2026-04-17-003 directory and updated CURRENT_SESSION.
- Read prior session notes (2026-04-17-002), SELF.md, PROJECT_STATE.md (first 200 lines).
- Read QMS-Policy, START_HERE, QMS-Glossary.

### Doc review: Wiki, Lessons 1-8, Deep Dive, README, Framing
- Read all five docs end-to-end. Vocabulary is consistent post-rename (no stray "eigenform" outside the Pass 4 historical paragraph). Cross-referencing is clean; Lesson → Framing → README → Wiki pointers all resolve.
- Surfaced three classes of findings:
  1. **Convergent unscheduled items** flagged in 3+ docs but not in the active backlog: action-dispatch registry (88 `if action == ...` branches), callable-preservation diagnostic (silent None fallback), concurrency model.
  2. **Deep Dive recommendations not cross-referenced elsewhere**: move RubiksCube/TableRunner to `engine/_examples/` (README still lists as production), delete `_migrate_legacy_overrides` with kill-date, split megafiles (Page/Table/Nav), promote mutable-structure editor out of sleek theme coupling.
  3. **Rename nits from last session**: `form` class attribute lowercase, `dev/content-model-unification` branch name.
- Parked correctly (do not action): Context primitive.

### PROJECT_STATE.md engine backlog expanded
- Replaced the sparse "Engine Backlog (lower priority)" stub with structured "Engine Backlog (post-workflow cleanup)" organized into: convergent unscheduled items, Deep Dive findings, rename nits, correctly parked, pre-existing items.
- Each item has effort sizing and source attribution (which doc(s) flagged it).
- `Last updated` bumped to Session-2026-04-17-003.

### Framework naming discussion → **Razem**
- Lead observed that the Wiki (and docs generally) conflate the framework with its first intended application: the general-purpose component/affordance framework is named "QMS Workflow Engine," but the QMS workflows don't actually exist yet. This is like naming React after Facebook.
- Canvassed candidates across multiple semantic axes: dual-audience/faithful-projection (Duet, Parity, Facet, Amphora), HATEOAS/self-describing (Herald, Cairn, Beacon, Nanori, Blazon, Gnomon), composition (Weave, Motif), Pipe Dream metaphor extension (Cascade, Conduit), biology/chemistry/physics for genomically-identical-but-differently-rendered pairs (Isoform, Homolog, Allotrope, Tautomer, Entangle, Chromatid, Syzygy), Japanese/foreign-language twin/pair (Futago, Tsui, Omote), Polish "together" register (Razem), self-evident/open-book (Jimei, Jasne, Codex, Patent), self-describing (Nanori, Blazon, Gnomon, Colophon, Autological).
- **Lead's choice: Razem** — easy to pronounce, memorable, unique. Semantically leans into "together" — humans and agents together reading the same self-describing page.
- Recorded in PROJECT_STATE §1 (Where We Are Now) and §5 (Forward Plan — new "Before First QMS Workflow Ships" subsection) with full rename scope list.
- Rename NOT executed this session — queued to land before the first QMS workflow ships so the framework/application boundary is clean from the start.

### Wiki rewritten as if rename had already occurred
Lead asked for the Wiki (`app/templates/wiki.html`) to be rewritten as if the rename had landed. Targeted edits:
- **Title/subtitle:** "QMS Workflow Engine" → "Razem"; subtitle updated to "Razem framework."
- **Lead paragraphs:** Rewrote opening to foreground "Razem (Polish: together)" and added a new paragraph explicitly distinguishing the framework from the QMS Workflow Engine application (so a reader arriving cold understands the two aren't the same thing).
- **History section:** Added a new paragraph (after the four-framing-passes paragraph) explaining the framework-vs-application rename as a historical event, dated April 2026, citing the React/Facebook-JS analogy.
- **Architecture / Features:** Swapped the most prominent "the engine" → "Razem" instances (core loop intro, component catalog intro, faithful projection, design philosophy). Left natural-language "the engine" references in place where they read as generic description rather than a named entity.
- **Comparison table:** Column header "QMS Engine" → "Razem"; narrative below table ("Unlike LiveView, the QMS engine...") → "Unlike LiveView, Razem..."
- **See also / References / External links:** "Engine README" → "Razem README"; ref-1's "QMS Workflow Engine, §1" → "Razem, §1"; added new ref-13 pointing at PROJECT_STATE for the naming decision; external link retitled "Razem repository" with new hypothetical GitHub URL `github.com/whharris917/razem`.
- **Infobox:** Title → "Razem"; added two new rows: **Name origin** ("Polish: together") and **Former names** (Eigenform March 2026; QMS Workflow Engine March-April 2026). "as Eigenform engine" → "as Eigenform." Repository URL updated.
- **Retrieved footer:** Last updated bumped to Session-2026-04-17-003.
- Verified via grep: remaining "QMS Workflow Engine" / "qms-workflow-engine" occurrences are all intentional (distinction paragraph, history rename paragraph, ref-13, Former-names row); no stale references.

### Class taxonomy rename decided (not executed)
Lead provided a sketch (`prompt.txt`) proposing role-specific suffixes instead of the flat `*Component`. Refined into a coherent taxonomy across a back-and-forth:

**Categories:** Forms (produce State), Containers (unsuffixed), Derivations (unsuffixed standalone nouns; produce Derived), Displays (read-only), Imperatives, Wrappers, Runners, Apps.

**Key discussions:**
- **Orchestrator** for NavigationComponent — rejected; overclaims (systems-orchestration connotation). Options considered: Flow (taken by sibling app name conversationally), Conductor (musical, warm), Navigator (personified, odd), Navigation (literal, safe). Lead chose **Navigation** for now.
- **Derivation** as category — Lead liked this. Maps cleanly to the existing Props/State/Derived data triad in Framing §3 / Lesson 3. Classes become standalone nouns: Computation, Score, Validation.
- **Navigation split into four subtypes** — Lead flagged as separate future refactor. Split into tabs/chain/sequence/accordion as first-class classes with more descriptive names (candidates: Tabs, Wizard, Stepper, Disclosure — not final).

**Captured in PROJECT_STATE:**
- §5 item 5 — full class-rename mapping (28 classes → role-suffixed names) with scope list (class names, module filenames, templates, registry aliases, CSS, docs).
- §5 item 6 — Navigation-split as future refactor, quoting Deep Dive §6 as the source finding.
- `Action` vs `ActionButton` and `HistoryWrapper` vs keep — flagged as TBD in the rename item; final picks deferred to execution.
- Also saved a project memory (`project_class_taxonomy.md`) anchoring the category system for future sessions.

### Lesson URL IDs fixed (counter-based → 8-char hex)
Lead flagged that Lesson 1's `/pages/hello-1` used a counter-based pattern, but instance IDs are actually 8-char hex UUIDs (`uuid.uuid4().hex[:8]` — verified at `app/registry.py:67`). Root cause: PROJECT_STATE line 138 still said "Sequential IDs per type (`{type}-{n}`)" — stale from before the Apr 13 cleanup that migrated to UUIDs (line 262 correctly records the cleanup but the mechanism-description bullet wasn't updated).

- **Fixed PROJECT_STATE line 138**: "Sequential IDs per type (`{type}-{n}`)" → "8-character hex UUIDs (`uuid.uuid4().hex[:8]`) — counter-based IDs were replaced on Apr 13."
- **Added a one-sentence intro in Lesson 1**: "The URL will be something like `/pages/a3f9c2d1` — each spawned instance gets its own 8-character hex identifier" — so later uses read as examples rather than magic strings.
- **Fixed all lesson references**: substituted consistent hex IDs across lesson narratives — `a3f9c2d1` for hello (Lessons 1, 2, 3, 5), `7e4b81cf` for survey (Lessons 4, 5, 7), `4c8e9d12` for page (Lesson 6 compound-affordance targets example). Preserved `{instance_id}` / `{instance}` placeholders in Tip callouts (Lessons 1, 8) — those remain correct as template placeholders.
- Verified via grep: no `hello-1`, `survey-1`, or `page-1` strings remain in the submodule.
