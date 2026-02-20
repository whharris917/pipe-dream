# Session-2026-02-20-002 Summary

## Focus
Vision document for the interaction system as the canonical QMS interface. Strategic discussion, no implementation.

## What Happened

### Vision Discussion

The Lead framed a significantly expanded scope for the interaction system designed in Sessions 2026-02-19 through 2026-02-20-001. Key progression:

1. **Interact as canonical method.** The interaction system may become the canonical interaction method for the entire QMS, not just VRs.

2. **AI writes only through interact.** AI agents would interact with controlled artifacts exclusively via document interaction workflows. No more freehand markdown editing. This is the Air Gap pattern applied to document authoring.

3. **Fine-grained commits.** The project should commit at evidence boundaries, not just session or CR boundaries. A verifier should be able to reproduce the exact project state at any step in any document.

4. **Engine-managed commits.** The interact engine itself runs the commit — staging all changes, committing with a system-generated message, and recording the commit hash as response metadata. This eliminates the class of errors where authors forget to commit, have unstaged changes, or record wrong hashes.

5. **Primary data attachment.** Heavy use of `--respond --file` to attach raw terminal output, logs, and other primary data sources directly into VRs and other documents. Evidence is raw data, not narrative summaries.

### Vision Document

Wrote `vision-interact-as-canonical-interface.md` synthesizing all design work from Sessions 2026-02-19-002 through 2026-02-20-002. Covers:

- The three-layer architecture (intent decomposition → guided document production → execution dispatch)
- The interaction protocol (tags, responses, navigation, enforcement)
- Atomic commit integration (engine-managed commits, commit hash as response metadata)
- Primary data attachment and the reproducibility chain
- What this gives the QMS (structural conformance by construction, content-level attribution, ALCOA+ properties, templates as procedural controls)
- Architectural implications (response store as source of truth, checkout/checkin semantics, template governance)
- Five-phase implementation path (VR → atomic commits → executable docs → non-executable docs → intent decomposition)
- Open questions (storage location, tag syntax stability, commit scope, SOP evolution, freehand escape hatch)

### Key Insight

The QMS evolves from a system that governs documents to a system that governs interactions — and produces documents as a byproduct.

## Decisions Made

- The interaction system is the strategic direction for AI-QMS interface, not just a VR convenience feature
- Engine-managed commits preferred over author-managed commits
- `commit: true` template attribute controls which prompts trigger commits
- `--respond --file` is the preferred method for attaching evidence (raw data over summaries)

## Open Questions (carried forward from 001 + new)

- Storage location for response lists (sidecar JSON in `.meta/`? new tier? inline?)
- Tag syntax stability review before implementation
- Commit scope policy (`git add -A` vs. scoped staging)
- SOP-004 evolution for fine-grained commit model
- Freehand escape hatch for edge cases
- Concurrent interact session commit interleaving
