# Session-2026-03-03-001

## Current State (last updated: 2026-03-03 CR-108 drafted)
- **Active documents:** CR-107 (DRAFT v0.1, content v1.0), CR-106 (DRAFT v0.1, content v0.4), CR-108 (DRAFT v0.1)
- **Current task:** Session complete — CR-108 ready to route next session
- **Blocking on:** Nothing
- **Next session:** Route CR-108, begin sandbox setup and informal RS

## Progress Log

### Session Start
- Previous session: Session-2026-03-02-001 — Interaction architecture design explored (provisional, no decisions made)
- Lead clarified: ALL design work since CR-107 reached current form is provisional. Lead is indecisive and wants to reach final decisions today.
- Reviewed PROJECT_STATE.md, previous session notes, QMS docs, all design artifacts from sessions 2026-02-22-004, 2026-02-27-001, 2026-03-02-001
- Read CR-107 draft in full

### Design Decisions Made (interaction-design-plan.md)
1. **CR-107 scope expands** to include interactive document redesign
2. **Two-template separation:** TEMPLATE-{TYPE} defines workflow graph + final rendition; TEMPLATE-INTERACT is a generic interaction renderer
3. **File-based interaction:** Agent responds by editing workspace (inline HTML comment markers), checkin extracts responses
4. **Concise workspace:** Show current prompt only, not previous responses
5. **Placeholder syntax confirmed:** `{{placeholder}}` → `<<placeholder>>`
6. **Non-interactive documents:** No graph in frontmatter → skip interaction layer entirely

### Design Plan Drafted
- Wrote `interaction-design-plan.md` in session folder (8 sections)
- Iterative refinements: eliminated qms interact command, added navigation section, concise workspace

### Zone Model Added
- Lead raised generality concern: design was over-fitted to VRs
- Added `<!-- @interactive: zone_name -->` marker concept
- Created TEMPLATE-INTERACT.j2 and TEMPLATE-CR.j2 in session folder

### Authoring vs. Execution Phases Added
- Same zone needs different workflows at different lifecycle phases
- Added phase-keyed sub-graphs, `each:` directive, phase selection
- Lead noted YAML is straining under complexity → Python graph model may be better

### Paradigm Shift: DocuBuilder (major pivot)
- Lead drew on Kneat eVal (pharma digital validation platform) experience
- **Core insight: the table is the universal interactive primitive.** Every interactive element is a table, from 1x1 (standalone field) to M x N (verification procedure)
- **Column types** — Non-executable: ID, Row Number, Design, Calculated, Prerequisite. Executable: Recorded Value, Signature, Witness, Issue, Choice List
- **Three property namespaces:** System (auto, immutable), User (author-defined, grows organically), Execution (schema defined during authoring, values filled during execution)
- **Composable sections** — importable, carry their own properties and interactive elements
- **Prerequisites as property assertions** — `TARGET = VALUE`, cross-references, aggregator tables
- **Tables auto-sort by prerequisites** — live progress view for free
- **Document dependencies expressed as prerequisites** — VAR status gates parent closure
- **Work Instructions** — disposable guided documents that produce other documents (replaces sequential prompt use case)
- **Context economy** — Calculated columns, section visibility, hide irrelevant content from AI agent context windows
- **The agent interface is just: edit what you see** — checkout gives document, agent edits, checkin processes
- This paradigm supersedes the interaction-design-plan.md approach entirely

### Document Data Model (`document_dna.json` — Lead-authored)
The Lead authored `document_dna.json` as the prototype data structure underlying all DocuBuilder documents. Key design decisions emerged iteratively:

- **Two element types:** `text` (prose blocks with optional Jinja2 placeholders like `{{ user_properties.custom_1 }}`) and `table` (the interactive primitive)
- **Table names for stable references:** Each table has a `name` property (e.g., `"name_of_table"`) used for cross-references and prerequisite paths. Position-based references would break when sections are reordered or imported.
- **`column_order` array:** Columns are defined as a dict (keyed by display name, each with a `type`), but rendering order is controlled by a separate `column_order` array. This separates the column schema from its visual presentation.
- **Sparse row values:** Row `values` are keyed by column name, and only populated columns appear. A row with `{"Instructions": "..."}` has no ID, no Prerequisites — those are either auto-generated (ID) or absent (Prerequisites = no gate). This keeps the data model lean.
- **Prerequisite paths use `::` separator:** e.g., `path::to::prerequisite::table::row`. This provides a stable, hierarchical addressing scheme for cross-references within and across documents.
- **Hierarchical locking:** `locked` flags appear at three levels — section, element, and row. A locked section means the entire section (including all elements) is protected. A locked element (text or table) within an unlocked section means that specific element can't be removed but adjacent content can be edited. A locked row within an unlocked table means the row's design content is frozen but the table can still grow.
- **Three property namespaces at document root:** `system_properties`, `user_properties`, `execution_properties` — matching the conceptual model in the principles document. Execution properties have schema defined during authoring but empty values until execution.
- **Sections as numbered string keys:** Sections use string keys (`"1"`, `"2"`) in a dict rather than an array, allowing stable references even when sections are reordered.

The workspace rendering mockup (`prompt.txt`, also Lead-authored) demonstrates how this JSON structure renders for the agent — menu bar, section navigation, tables with column types shown in headers, `[+ Add Row]` affordances, and a command input region at the bottom.

### Design Artifacts Created
- `authoring-and-executing-controlled-documents.md` — Core principles document (9 sections)
- `document_dna.json` — Document data model prototype (Lead-authored, see above)
- `prompt.txt` — Workspace rendering mockup (in project root, Lead-authored)
- `interaction-design-plan.md` — Superseded by DocuBuilder paradigm but preserved as design history
- `TEMPLATE-INTERACT.j2`, `TEMPLATE-CR.j2` — Superseded but preserved

### CR-108 Created
- DocuBuilder Genesis Sandbox — authorizes exploratory prototyping
- Git-ignored `docu-builder/` directory, entirely outside QMS control
- Exploratory: no required outcomes, closable at any time
- Sole restriction: no changes to existing controlled submodules or anything outside sandbox
- DRAFT v0.1 checked in, ready to route next session
