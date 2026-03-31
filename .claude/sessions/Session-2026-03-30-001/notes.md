# Session-2026-03-30-001

## Current State (last updated: end of session)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current work:** Complete — theory, dependency visibility, HistoryForm, Control Flow Gallery
- **Blocking on:** Nothing
- **Next:** First-class interception mechanism for PageForm routing (needed for AuditForm-style wrappers that gate child mutations)

## Progress Log

### Session Start
- Initialized session, read previous session notes (Session-2026-03-29-004)
- Read QMS documentation (QMS-Policy, START_HERE, QMS-Glossary)
- Previous session delivered: typed columns, SequenceForm, edit mode, TableRunner, Workflow Builder (32 eigenform types, 17 pages)

### Theoretical Analysis: What Is an Eigenform?
- Examined whether TableRunner is categorically different from other eigenforms
- Found: the original "eigen" meaning (self-contained data ownership) eroded gradually — ScoreForm, ComputedForm, VisibilityForm, DynamicChoiceForm, SwitchForm, TableRunner each moved further from self-containment
- Identified the actual invariant across all 32 types: **HATEOAS-complete interaction node** — self-describing state, self-describing actions, handler, completion signal
- The real "eigen" is self-*describing*, not self-*containing*. From the agent's perspective, every eigenform carries enough context to interact with it without external documentation.
- Identified a spectrum of sibling coupling: Pure → Dependent → Observer → Gate → Projection (runner)
- TableRunner introduces a model/view split not present before: TableForm is data authority, TableRunner is alternative interaction surface over the same data
- **Decision: keep the name "eigenform"** with revised meaning — "eigen" as in eigenvector (identity-preserving under transformation): serialize, render, handle, recompose — the form remains coherent. This reading is more accurate than the original "self-contained" intent.
- Considered alternatives: holon (whole-and-part), actor (message-passing), locus (interaction point), pragma (unit of action)
- Further refinement: "a function made visible" → but affordances are functions exposed BY the eigenform, so eigenform is not itself a function → eigenform is a **program** (state + instruction set + halt condition). Agent is the runtime. Affordances are the instruction set. Store is memory. is_complete is the halt condition. Runners reframe cleanly: a program that interprets another program.

### Dependency Visibility
- Identified that `depends_on` creates a shadow graph of data dependencies invisible in the UI
- The containment tree captures parent-child; `depends_on` captures sibling coupling — but only the tree is visible
- Lead's word for it: "loose" — coupling without containment
- **Decision:** dependent eigenforms now render "Depends on: /path/to/sibling" with full URL paths
- Implemented `render_dependency_line()` helper in `eigenform.py`
- Updated 6 types: SwitchForm, DynamicChoiceForm, ComputedForm, ValidationForm (per-rule), ActionForm (also added depends_on to serialization), ScoreForm (derives depends_on from answer_key keys)
- Skipped VisibilityForm (transparent wrapper — renders child directly)
- All 17 pages verified rendering cleanly

### HistoryForm (new eigenform type)
- Wraps any eigenform with append-only change history
- Lazy change detection: compares child state on serialize(), appends timestamped snapshot if different
- Timeline bar with version dots, "View History" button, Older/Newer/Back to Current navigation
- Historical view: purple-bordered read-only card showing snapshot data
- `_clear_data()` clears child + viewing state but NEVER the history
- Registered as type "history" (33 types total)
- Added to Eigenform Gallery (Conditional & Dynamic tab) and Control Flow Gallery page

### Control Flow Gallery (new page)
- New page at /pages/control-flow-gallery (18 pages total)
- Currently contains HistoryForm demo
- Intended as a home for control flow eigenforms

### AuditForm — Created and Deleted
- Built AuditForm: like HistoryForm but requiring a "reason" field with every mutation
- Required monkey-patching the child's handle() during bind to intercept and gate mutations
- This was the **first time any eigenform modified another eigenform's behavior** — a violation of the property that an eigenform's behavior is determined by its class
- Lead and I agreed this was architecturally wrong. Deleted entirely.
- **Open question for next session:** the architecture needs a first-class interception mechanism in the routing layer (e.g., `handle_child_action(child, body)` on containers) so wrappers can gate child mutations without monkey-patching

### Commits
- ae09cdf: Render sibling dependency paths on dependent eigenforms
- Pending: HistoryForm, Control Flow Gallery, AuditForm removal, session notes
