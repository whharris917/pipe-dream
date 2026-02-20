# Session-2026-02-20-001 Summary

## Focus
Incremental document building — continued from Session-2026-02-19-003. Evolved from abstract data model to concrete template restructuring and CLI command design.

## What Happened

### Template Restructuring (TEMPLATE-VR-restructured.md)

Redesigned TEMPLATE-VR as an interactive form with embedded state machine tags. The template is both the interaction script (for the CLI) and the output template (for compilation).

**Tag system designed:**
- `@prompt` — content prompt, captures response into `{{placeholder}}`
- `@gate` — flow-control prompt, routes only, no compiled content
- `@loop` / `@end-loop` — repeating blocks with `{{_n}}` iteration counter
- `@end` — terminal state
- Attributes: `next`, `type: yesno`, `yes`/`no` branches, `default` for auto-fill

**Key design decisions:**
1. All guidance unpacked from comment blocks into visible prompt text — nothing hidden
2. Procedure and observations interleaved per step (carried from Session-003)
3. Each step is a self-contained verification unit: action → expected → detail → observed → outcome
4. Separate Outcome section eliminated — assessment happens per step, Summary section provides overall pass/fail + narrative
5. Section 2 retains high-level objective but expected outcomes moved to per-step level

### Response Model

Responses are timestamped chronological lists, not scalars. Amendments append — never replace or delete. GMP-style correction trail built into the document:
- Superseded entries render with strikethrough
- Active entry (most recent) renders normally
- Every entry carries author + timestamp + amendment reason
- Timestamps shown on all responses, amended or not

### Navigation Model

Two cursor movement primitives:
- `goto` — detour to a completed prompt, amend, return to prior position
- `reopen` — re-enter a closed loop, add iterations, return when gate re-closes
- Amendments don't cascade — corrections are self-contained
- All cursor movements recorded in audit trail

### `qms interact` Command Design (interact-command-design.md)

Single CLI entry point for incrementally-built documents. Bare command emits status + current prompt + available actions. Flags perform actions.

**Flags:** `--respond`, `--respond --file`, `--accept` (defaults), `--progress`, `--goto`, `--reopen`, `--compile`

**Agent workflow:** Stateless loop — call interact to orient, call interact --respond to answer, repeat. 23 commands for a complete 2-step VR.

## Design Principles Established

- **Templates are both script and output.** One file encodes the interaction flow and the compiled document structure.
- **Every invocation is stateless.** Document tracks its own cursor and progress. Context loss is recoverable by calling `interact` bare.
- **Append-only response model.** Nothing is deleted. History is the audit trail.
- **Guidance is the prompt, not a hidden comment.** The author sees exactly what they need at each step.

## Open Questions (carried forward)

- **Schema format in templates:** The tag system is designed; how it gets embedded in controlled markdown templates (TEMPLATE-VR is a QMS-controlled document) needs consideration
- **Storage location:** Where do prompt/response lists live? Sidecar JSON in `.meta/`? Inline in the document?
- **Compile timing:** Preview at any point (proposed), partial compilation for unfilled docs
- **Validation enforcement:** Advisory-first with `--strict` option (proposed from Session-003)
- **Implementation phasing:** VRs first, then evaluate expansion to EI tables and other document types
