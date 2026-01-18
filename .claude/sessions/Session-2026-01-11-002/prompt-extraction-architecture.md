# Architectural Decision: Prompt Extraction

## Context

After CR-026 (QMS CLI Extensibility Refactoring), we examined what remains hard-coded in qms-cli that distinguishes document types:

1. **Workflow transitions** (`workflow.py`) — Two state machines selected by `is_executable` boolean (not per-doc-type)
2. **Task prompts** (`prompts.py`) — Optional per-doc-type checklist customization

Templates were previously absorbed into `QMS/TEMPLATE/` as controlled documents. The question: should prompts follow the same pattern?

## Initial Proposal (Rejected)

Extract prompts to `QMS/PROMPT/` as QMS-controlled documents.

**Rationale:** Prompts must align with SOPs; putting them in QMS exposes them to impact assessments.

**Problem:** This clutters the QMS with implementation artifacts rather than keeping it focused on behavior-oriented procedural controls.

## Refined Proposal (Accepted)

Maintain separation between behavioral requirements (SOPs), system requirements (RS), and implementation:

| Layer | Location | Content | Governance |
|-------|----------|---------|------------|
| **Procedures** | `QMS/SOP/` | Behavioral requirements (what to do) | QMS-controlled |
| **System Requirements** | `QMS/SDLC-QMS/` | Functional requirements (what the tool must do) | QMS-controlled |
| **Implementation** | `qms-cli/prompts/` | Technical details (how the tool does it) | Git-controlled, traced via RTM |

## Traceability Chain

1. **SOP-001** says "documents must have frontmatter with title and revision_summary"
2. **SDLC-QMS-RS** says "REQ-QMS-xxx: Review prompts shall verify frontmatter fields per SOP-001"
3. **`qms-cli/prompts/review.yaml`** implements that requirement
4. **SDLC-QMS-RTM** traces REQ-QMS-xxx → `prompts/review.yaml`

## Impact Assessment Flow

A CR updating SOP-001:
1. Includes SDLC-QMS-RS in impact assessment (because RS references SOP-001)
2. RS update identifies affected requirements
3. Implementation updates flow through normal development workflow
4. RTM maintains traceability

## Key Insight

SOPs define *behavior* (procedures). RS documents define *system requirements*. Implementation artifacts (prompt files, config files) belong in the codebase, traced via RTM — not in the QMS itself.

## Known Inconsistency: Templates

`QMS/TEMPLATE/` currently contains document templates as QMS-controlled documents. Per the architectural thinking above, these are implementation artifacts and should eventually migrate to `qms-cli/templates/`.

**Decision:** Accept this inconsistency for now. The current approach is working well, and migration would introduce churn with no immediate benefit. Revisit when there's a compelling reason to change.

## Next Steps

1. Extract prompts from `prompts.py` to separate files in `qms-cli/prompts/`
2. Create `SDLC-QMS-RS` with requirements derived from SOPs
3. Create `SDLC-QMS-RTM` tracing requirements to implementation
4. (Future) Consider migrating `QMS/TEMPLATE/` to `qms-cli/templates/`

---

*Discussed: Session-2026-01-11-002*
