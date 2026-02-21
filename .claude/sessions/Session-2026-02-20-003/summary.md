# Session-2026-02-20-003 Summary

## Focus

Consolidated interaction system design. Conceptual framing, VR template refinement, and key architectural decisions.

## What Happened

### Conceptual Framing

Discussed three ways to conceptualize the interaction system:

1. **Documents as UI** — mechanically accurate but undersells what's happening. A form collects; it doesn't teach.
2. **Robotic secretary** — captures functional role but misplaces the intelligence. The engine is rigid; the intelligence is in the template.
3. **Skill/methodology** — the deepest framing. Templates encode cognitive processes, not just document structure. Template authoring is methodology design. Template review is methodology review. Templates evolve under selective pressure from review outcomes.

The skill framing was adopted as the primary conceptual model. Closest real-world analog: structured interview protocols in qualitative research.

### VR Template v3

Refined TEMPLATE-VR through three iterations:

- **v2 -> v3:** Added per-step commit hash (engine-managed via `commit: true`), merged `step_action` and `step_detail` into single `step_instructions` prompt, added `step_type` (positive/negative) label
- **Removed `step_type`:** The Lead determined a separate type field was unnecessary overhead. Positive/negative verification guidance was woven into the `step_expected` prompt coaching instead.
- **Removed `parent_doc_id` prompt:** Parent is already known at creation time from `qms create VR --parent CR-090`. Engine injects it from metadata. Interaction starts at `related_eis`.

Final step tuple: (instructions, expected, actual + commit, outcome).

### Key Architectural Decisions

1. **Source files.** Interactive documents produce `.source.json` — the permanent, authoritative structured data from which compiled markdown is derived. "Source" chosen over "record", "ledger", "transcript" because it generalizes beyond evidence-bearing documents.

2. **Workspace artifacts.** Checkout places a `.interact` session file in the workspace, not an editable markdown file. Authors interact through `qms interact`, not file editing. Freehand edits are not permitted on interactive documents.

3. **`qms read` behavior.** Always works, always returns compiled markdown. Partially filled documents show empty fields. No "this is interactive, use a different command" gate.

4. **File lifecycle.** `.interact` (workspace, during authoring) -> `.source.json` (`.meta/`, permanent after checkin) -> compiled `.md` (QMS directory, derived view).

5. **Child document paths.** VRs live alongside parents: `QMS/CR/CR-090/CR-090-VR-001.md`.

### Consolidated Design Document

Wrote `interaction-system-design.md` — the single reference document for the entire interaction system. Supersedes the scattered design artifacts from Sessions 001 and 002 as the consolidated, current-state design.

## Decisions Made

- Skill/methodology is the primary conceptual framing for the interaction system
- Source files named `.source.json`; workspace sessions named `.interact`
- Checkout does not provide editable markdown for interactive documents
- Freehand editing is not permitted on interactive documents
- `qms read` compiles from source transparently — no special handling
- Positive/negative verification is coaching in prompt guidance, not a structural field
- Parent document ID is metadata, not a prompt — known at creation time

## Open Questions (carried forward)

- Tag syntax stability review before implementation
- Commit scope policy (`git add -A` vs. scoped staging)
- SOP-004 evolution for engine-managed commits
- Hybrid document mechanism for CRs (interactive structured sections + freehand narrative sections)
