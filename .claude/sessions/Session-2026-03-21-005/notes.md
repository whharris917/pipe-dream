# Session-2026-03-21-005

## Current State (last updated: all fixes implemented and verified)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Blocking on:** Nothing
- **Next:** Address findings from agent API evaluation

## Progress Log

### Session Start
- Read previous session notes (Session-2026-03-21-004)
- Previous session: Faithful Projection for execution tables + parametric affordances, builder flowchart bug fix, equipment calibration demo workflow, builder proceed bypass fix, builder alignment to runtime field convention
- Read PROJECT_STATE.md — forward plan: LNARF renderers for remaining pages, sub-workflow embedding, hot reload, SDLC-WFE-RS rewrite, real provider implementation

### Agent API Evaluation — Create Workflow via curl
- Built "Document Review and Approval" workflow (10 nodes, 29 fields, router, fork, computed fields, conditional visibility, navigation) using only curl + JSON
- Published successfully → `document-review-approval.yaml` (398 lines)
- **Key finding: silent failures on malformed POST bodies.** Unrecognized parameters silently ignored in `add_branch` (returned empty success). `set_fork_merge` inconsistently returned error for same category of mistake. 30-minute debugging detour.
- **Key finding: affordance body template IS the schema.** The `body` field specifies the exact JSON keys; I failed to read it and used domain-guessed parameter names instead.
- Full execution log with 34 observations in `execution-log.md`
- Overall verdict: highly agent-friendly API with one critical gap (silent failures)

### Implementation — All Findings Resolved
Implemented all 7 phases from the plan:
1. **Bug 2.1 FIXED:** `_evaluate_computed()` in renderer.py now delegates to unified `evaluate()` — computed fields with AND/OR/field_equals work correctly
2. **Bug 2.2 FIXED:** `check_visibility()` in evaluator.py now detects expression tree format and delegates to `evaluate()` — visible_when conditional fields appear correctly
3. **Bug 2.3 VERIFIED:** Field values persist through branch transitions. Original "data loss" was a curl observation error.
4. **Content negotiation:** `/agent/` routes now default to JSON when no Accept header specified
5. **Parameter validation:** All 44 builder actions have parameter whitelists; unrecognized params return clear error messages
6. **Fork auto-activation:** Runtime auto-activates forks with `pause: false`; builder defaults new fork nodes to `pause: false`
7. **Validation output:** Preview node returns structured `{status, errors, checks}` dict
8. **Expression syntax factoring:** `_EXPR_HINT` moved to response-root `expression_syntax` key; affordance params use short "See expression_syntax." references

**Files changed:**
- `engine/runtime/evaluator.py` — 3-line fix in check_visibility()
- `engine/runtime/renderer.py` — replaced _evaluate_computed() body, added evaluate import
- `engine/runtime/actions.py` — added validate_params() helper, fork auto-activation in _enter_node()
- `engine/builder.py` — parameter whitelist dict, validate_params integration, fork pause default, validation output, expression factoring
- `app/app.py` — _wants_json() helper, replaced 5 content negotiation checks

### Runtime Execution of Published Workflow
- Executed the Major severity path (fork/merge) through to completion
- Runtime log in `runtime-execution-log.md`
- **3 bugs found:**
  1. Computed field evaluates false when expression should be true (cross-node field_equals)
  2. Conditional field visibility (visible_when) not working — fields never appear
  3. Field values lost during branch transitions (2 separate incidents)
- **Findings document:** `agent-api-findings.md` — 6 builder improvement suggestions + 3 runtime bugs
