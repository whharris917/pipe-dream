# Session-2026-02-19-003 Summary

## Focus
Incremental document building — concrete design work on the prompt/response data model.

## What Happened

### Incremental Document Building Design

Studied the vision document from Session-002 and worked through concrete examples of what the uncompiled prompt/response sequence would look like for a VR (using CR-090-VR-001 as the reference case).

**Key design decisions made through iteration:**

1. **Self-contained data model.** The stored JSON includes both prompts and responses — not just responses. A reviewer or the system itself after context loss can read the file and understand what was asked and what was answered without cross-referencing the template.

2. **Interleaved steps, not separated sections.** The Lead identified that the current template's separation of procedure (Section 4) and observations (Section 5) doesn't reflect how testing actually works. The atomic unit of a VR is one action and its result, not "all actions" then "all results." The data model pairs each step's action, detail, and observation together.

3. **`repeating_group` type.** Interleaving requires a prompt type where a group of fields repeats N times, with N determined at runtime. The author records action → detail → observed for step 1, then starts step 2 or signals `--done`. This enforces contemporaneous recording by construction — you cannot record step 2's action until you've recorded step 1's observation. Backfilling is structurally impossible.

4. **Typed responses.** Not everything is free text. Types include `text`, `text_block`, `date`, `enum`, `key_value_list`, `verification_table`, `signature`, `repeating_group`. Typed responses enable structural validation, consistent rendering, and programmatic extraction.

5. **Auto-fill for known values.** `parent_doc_id`, `today`, `current_user` can be pre-populated, reducing interactive prompts.

6. **Timestamps per response.** Each response carries `responded_at`, providing ALCOA+ contemporaneous recording evidence for free.

### Observations Surfaced

- The compiled markdown output would look essentially identical to current VRs — the difference is the path to that document (sequential prompts vs free-form editing of a 300-line template)
- The `--file` escape hatch is necessary for multi-line responses (procedure commands, observation output)
- The checkout/checkin cycle may be unnecessary for incrementally-built documents — responses are captured atomically via CLI, no workspace copy needed
- Validation hints embedded in prompts address the exact failure mode from CR-090-VR-001 (abbreviated commands, paraphrased output)

## Open Questions (carried forward + new)

- **Schema format in template:** The JSON example works for the response store, but how does the schema get defined in TEMPLATE-VR (a controlled markdown document)? YAML frontmatter? Embedded JSON block? Separate sidecar?
- **Storage location:** `.meta/` sidecar proposed but not finalized
- **Compile timing:** Preview at any point (proposed), not finalized
- **Validation enforcement:** Advisory-first with `--strict` option (proposed), not finalized
- **Reviewer view:** Both compiled and raw (proposed), not finalized
