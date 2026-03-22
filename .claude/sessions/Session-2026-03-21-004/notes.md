# Session-2026-03-21-004

## Current State (last updated: builder alignment complete)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Blocking on:** Nothing
- **Next:** Continue LNARF renderer rollout to remaining pages

## Progress Log

### Session Start
- Read previous session notes (Session-2026-03-21-003)
- Previous session: LNARF portal renderer + audit, observer simplification, interactive affordances, error rendering, Faithful Projection design document
- Read Session-2026-03-21-002 notes (user had file open)

### Faithful Projection — Create Execution Table Workflow
**LNARF audit of existing renderer identified 3 violations:**
1. **Silent affordance drops** — Affordances with `body.value` that don't match a field label (e.g., "Set cell", "Set sequential execution") were classified as field affordances but never rendered
2. **Parametric affordances lose parameters** — Table operations (add_column, set_cell, set_rule, etc.) rendered as plain buttons without parameter input controls
3. **Execution cell actions detached** — Cell actions (fill, sign, amend) rendered in a flat action bar, not inline with the cells they target

**Three fixes applied to `simple-shared.js` and `simple.js`:**

1. **Fixed affordance classification** (`_expDPage`): Now matches field affordances by label pattern (`Set {FieldLabel} (current:`) against actual displayed field names, not by `body.value` presence. Prevents silent drops.

2. **Parametric affordance rendering** (new `wfRenderParamAff`): Affordances with `parameters` render as forms with labeled inputs — text fields or dropdowns per parameter, plus Submit button. Table operations (add_column, set_cell, rename_column, etc.) now have interactive controls for all their parameters.

3. **Faithful execution table** (new `wfRenderExecTableFaithful`): Indexes cell affordances by `(row, col)` from the affordance body. Renders controls inline with cells:
   - fill/amend → text input or dropdown (if choices) + Fill/Amend button
   - sign/re-sign → Sign button
   - mark_na → N/A button
   - initiate_issue → dropdown (VAR/ER) + Issue button

**Binding extensions** (`_wfBindAffordances`): Added handlers for parametric form submit, execution cell submit, and execution cell action buttons. All construct the correct POST body from form inputs + body template.

**CSS additions** (`simple.js`): Structural + light-theme colors for `.wf-param-*` forms and `.wf-exec-*` inline controls.

**Automated audit** confirmed: all affordance types projected, no silent drops, correct classification, complete binding coverage, zero LNARF violations.

### Builder Flowchart Bug Fix
- **Bug:** `_summary()` in `engine/builder.py` copied proceed entries without resolving implicit sequential targets. `definitionToSpine()` relies on `proceed.target` to walk the chain — null target stops the walk. Result: only the first node card rendered in the detailed flowchart.
- **Fix:** Added implicit target resolution in `_summary()` — if `proceed` has no explicit target and there's a next sequential node, set `target` to that node's ID. Same logic already existed in `_serialize_definition_topology()`.

### Demo: Equipment Calibration Record Workflow
- Built a 6-node workflow via the Create Workflow builder to demo for Aaron:
  - **intake** — 6 fields (equipment ID, name, location, trigger, criticality, last cal date), proceed gate
  - **scheduling** — 5 fields (reference standard, cert validity, technician, date, procedure ref), proceed gate with boolean check
  - **execution** — 6 fields (env conditions, as-found/as-left readings, result, signature), proceed gate
  - **router_result** — Router node: Pass/Adjusted → complete, Out of Tolerance → oot_investigation
  - **oot_investigation** — 7 fields (impact, root cause, affected products, corrective/preventive action, disposition, QA review), proceed gate
  - **complete** — 2 fields (next cal due, cert ref), show_all_fields, restart action
- Published via `/publish` endpoint (not `/proceed` — learned that proceed just advances without writing YAML)
- Zombie server process on port 5000 caused confusion — workflow was discoverable but old process served stale state

### Builder Proceed Bypass Fix
- Preview node had an implicit proceed gate allowing `/proceed` to advance to "published" without writing the YAML
- Removed implicit proceed injection for the preview node
- Added explicit guard in proceed handler: returns error "Use 'publish' to advance from Preview."

### Builder Alignment to Runtime Field Convention
- **Problem:** Builder affordances had the right label pattern (`Set {Label} (current: ...)`) but `render_node()` didn't emit `state.fields`, so the Human renderer couldn't match them inline — they fell through to parametric forms with "Submit" buttons instead of "Set"
- **Fix:** Added `state["fields"]` to builder's `render_node()`:
  - Metadata node: Workflow ID, Workflow Title, Workflow Description
  - Node builder (focused): Show All Fields, Pause, Execution, Node Mode
- Normalized affordance labels — dropped node-scoped `for '{node_id}'` suffixes
- Changed Node Mode affordance body from `{mode: "<mode>"}` to `{value: "<value>"}` to match `FieldSource` convention; updated handler to accept both
