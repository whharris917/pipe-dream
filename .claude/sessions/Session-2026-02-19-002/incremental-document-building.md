# Incremental Document Building

## The Problem

The current QMS workflow asks the author to hold a template's structure, evidence standards, and procedural requirements in memory while simultaneously performing work, then produce a compliant document from recall. This is the exact failure mode that GMP process design is built to prevent. Templates encode the correct sequence but don't enforce it — the gap between "here's a template, fill it out" and "here's section 1, respond, now here's section 2" is where compliance failures occur.

Concrete example from Session-2026-02-19-002: CR-090-VR-001 was rejected twice during authoring because (1) a command was abbreviated instead of copy-pasted, and (2) the pre-condition referenced uncommitted code. Both failures stem from the same root cause — the author wrote the entire VR after the fact from memory, rather than being guided through each section contemporaneously.

After 90 CRs, this pattern is well-established: AI agents cannot be reliably expected to internalize large instruction sets and follow them all perfectly. This is not a deficiency — human workers in pharma are always supposed to have the SOP open and consult it each time. The solution is not "better memory" but "better forms."

## The Vision

Documents transition from blank canvases with templates to **interactive forms with sequential prompts**. The document itself becomes the workflow engine — it tells the author what to do next, the author responds, and the response is captured in place, contemporaneously.

This is the enforcement of the sequential nature that is currently only implied by templates. Templates were the primitive form of this concept; incremental building is the mature form.

### Current Flow

```
qms create VR → blank template copied to workspace → author edits freely → checkin
```

### Proposed Flow

```
qms create VR → document exists as a sequence of prompts with stored responses
qms next DOC_ID → displays the next unfilled prompt (with guidance/validation hints)
qms respond DOC_ID "response content" → response stored as part of the document
  ... repeat until all prompts are filled ...
qms compile DOC_ID → renders final document from prompt/response pairs
```

The author can:
- See what prompt comes next (`next`)
- Respond to the current prompt (`respond`)
- Review previous responses (`read` with section targeting)
- Edit a previous response if needed (`edit` with section targeting)
- Compile the final rendered document at any point (`compile`)

## Key Design Principles

**The template becomes a schema.** Instead of markdown with placeholder comments, templates define a structured sequence of prompts — each with an ID, display text, validation hints (e.g., "paste exact command, not paraphrase"), and position in the sequence.

**Responses are the source of truth.** The prompt/response pairs are the primary data. The rendered markdown document is a derived artifact, compiled from the structured data. This inversion — structured data first, rendered document second — enables programmatic validation, extraction, and cross-referencing.

**The document tracks progress.** The schema knows which prompts have been answered and which remain. Context loss (from compaction, session boundaries, or agent restarts) is recoverable — resume from where the document says you left off, not from memory.

**Contemporaneous recording by construction.** The sequential prompt model makes backfilling structurally difficult. You answer each section as you encounter it, which aligns with ALCOA+ principles.

## What This Solves

| Problem | How Incremental Building Addresses It |
|---------|---------------------------------------|
| Evidence quality (abbreviated commands, paraphrased output) | Prompt-level validation hints enforce standards at the point of entry |
| Backfilled documentation (writing after the fact from memory) | Sequential advancement encourages contemporaneous recording |
| Cognitive load (holding entire template structure in memory) | Author only sees one prompt at a time |
| Context loss across compactions/sessions | Document tracks its own progress; resume from document state |
| RTM automation | Structured prompt/response data enables programmatic extraction |
| Completeness validation | Schema defines required fields; unfilled prompts are visible |

## Connections to Other Backlog Items

- **ALCOA+ integration** (to-do 2026-02-16): Incremental building enforces contemporaneous recording by construction, which is the core ALCOA+ requirement.
- **RTM automation** (to-do 2026-02-16): Structured prompt/response data is machine-readable. Traceability entries, VR evidence cross-references, and completeness checks become programmatically derivable.
- **Session heartbeat / context management** (to-do 2026-02-16): Document-tracked progress makes context loss recoverable without relying on session state.
- **Protocol / Attachment taxonomy** (to-do 2026-02-19): Records (VRs) are the natural first candidate for incremental building. The attachment class may eventually define "built incrementally" as a property.

## Scope and Phasing

**Phase 1: VRs only.** VRs are the most structured, most sequential, and smallest document type. They're also where contemporaneous recording matters most. Implement the schema model, `next`/`respond`/`compile` commands, and validate the interaction pattern.

**Phase 2: Evaluate expansion.** After living with VR incremental building, assess whether the model extends to other document types. EI tables in CRs are a natural candidate (structured, sequential, evidence-bearing). Free-form authoring sections (Change Description, Justification) may not benefit.

## Open Questions

- **Schema format:** YAML? JSON? A DSL embedded in the template markdown? The schema needs to be human-readable (it's a controlled document) but machine-parseable.
- **Storage model:** Are prompt/response pairs stored in the existing markdown file (with markers), in a sidecar data file, or in the metadata tier?
- **Compile timing:** Is compilation a one-time terminal step, or can the author compile a preview at any point? Can the compiled output be re-compiled if a response is edited?
- **Validation enforcement:** Are validation hints advisory (displayed to the author) or enforced (response rejected if non-compliant)? Enforcement is more robust but harder to implement well.
- **Review of incremental documents:** Do reviewers see the compiled markdown, the raw prompt/response pairs, or both? The prompt/response format may actually be more auditable.
