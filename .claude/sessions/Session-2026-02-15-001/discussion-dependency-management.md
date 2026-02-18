# Session-2026-02-15-001: Dependency Management Discussion

**Type:** Ghost session (informal discussion, main Claude busy with long-running task)

## Problem Statement

Managing dependencies across a large project's artifact ecosystem — not software dependencies, but dependencies between SOPs, code, RSs, RTMs, tests, session notes, to-do lists, readmes, CLAUDE.md, agent definitions, templates, and so on. A single change (e.g., adding a new document type) ripples across many artifacts, and tracking all affected locations is error-prone and relies on human memory of the full dependency graph.

## Approaches Considered

Three core strategies, each with weaknesses alone:

1. **Centralized registry** — a master mapping of concepts to artifacts. Drifts and becomes its own maintenance burden.
2. **Process discipline** — require impact analysis in every CR. Relies on the analyst knowing the full graph (the problem being solved).
3. **Automated scanning** — grep for references. Catches syntactic but misses semantic dependencies.

## Concept Graph (Selected Direction)

A **central concept graph** that maps a controlled vocabulary of concepts (e.g., `document-types`, `workflow-states`, `user-roles`, `permissions-model`) to the documents and artifacts that depend on them.

- ~15-25 concept terms for this project
- Each document declares which concepts it depends on
- The graph enables deterministic impact analysis: "I'm changing X — here's every artifact that cares"
- Could integrate with CR workflow: auto-generate impact sets, require sign-off on each affected document

### Prototype Delivered

The concept graph prototype was built by reading all 22 documents (7 SOPs, CLAUDE.md, 6 agent definitions, 8 templates) and mapping concept relationships. Result:

- **26 concepts** across SOP-001 (8), SOP-002 (2), SOP-003 (1), SOP-004 (4), SOP-005 (1), SOP-006 (1), SOP-007 (1), CLAUDE.md (8)
- **22 documents** in the reverse index
- Full `depends_on` graph enabling transitive impact analysis
- File: `.claude/sessions/Session-2026-02-15-001/concept-graph.yaml`

### Spot-Check: `execution-mechanics`

Traced `execution-mechanics` (SOP-004 §4-8) through the graph:

- **Direct references:** 9 documents (SOP-002, SOP-003, all 7 execution-related templates)
- **Downstream concepts:** `var-types`, `addendum-mechanics`, `test-protocol`, `post-review-prerequisites`
- **Transitive impact:** adds SOP-001, SOP-006, agent-qa, TEMPLATE-CR (via downstream concepts)

This matches intuition: changing how execution works ripples into VARs, ADDs, test protocols, and post-review gates.

### Edge Type Expansion

The v1.0 prototype uses two undifferentiated edge types (`depends_on`, `references`). Discussion identified that richer verb types would improve impact analysis precision.

**Document-to-concept verbs** (replaces undifferentiated `subscribes_to`/`references`):

| Verb | Meaning | Impact implication |
|------|---------|-------------------|
| **defines** | Authoritative source of this concept | Where changes originate |
| **implements** | Concrete realization (templates) | Needs structural/content update |
| **enforces** | Validates compliance (agents, QA) | Review criteria may need updating |
| **references** | Mentions, depends on, defers to | May need terminology updates |
| **mirrors** | Reproduces verbatim | Needs identical changes (copy maintenance) |

The `mirrors` verb is high-value. Every agent definition has a `Prohibited Behavior` section that's near-verbatim from CLAUDE.md. Without `mirrors`, that looks like 7 documents "referencing" `prohibited-behavior`. With it, you know: change once, paste six times. This is a maintenance smell the graph can surface.

**Concept-to-concept verbs** (replaces undifferentiated `depends_on`):

| Verb | Meaning | Example |
|------|---------|---------|
| **composes** | Combines upstream concepts | `review-approval-workflow` composes `document-states` + `user-roles` + `permissions-model` |
| **specializes** | Narrows for a specific case | `var-types` specializes `execution-mechanics` for the failure path |
| **gates** | Runtime prerequisite | `sdlc-governance` gates code CR closure |
| **extends** | Adds capability on top of base | `mcp-tools` extends `cli-commands` with different transport |

The `specializes` vs `gates` distinction drives different work: if `execution-mechanics` changes, `var-types` (specializes) may need *content* updates, while `post-review-prerequisites` (gates) may need *conditions* re-evaluated.

**Decision:** Validate the flat graph first. Layer in verbs when a concrete use case demands the precision — likely when the graph is used to auto-generate CR impact sets.

## Modular Documentation Fragments (Future Phase)

Rather than synchronizing the same information across multiple documents, maintain a **fragment library** — canonical definitions of shared concepts — and compile documents from source templates that import fragments.

Architecture discussed:
```
QMS/
  src/                          # Source with include directives
    SOP/SOP-001.md
    fragments/
      document-types.md         # Single source of truth
  SOP/                          # Compiled, self-contained output
    SOP-001.md                  # What reviewers see
```

Key decisions reached:
- **Compiled output preferred** over reference-by-pointer (reviewers need self-contained documents)
- **Compiler runs at checkin time** — edits happen on source, build produces final documents
- **Unversioned fragments with build-time snapshots** — fragments are always-latest, determinism comes from committed compiled output

## Next Steps

- [x] Build concept graph prototype (26 concepts, 22 documents)
- [x] Spot-check transitive impact analysis
- [x] Identify expanded edge type vocabulary
- [ ] Validate graph against next real CR — does it catch the full impact set?
- [ ] If validated, promote graph to a permanent location (e.g., `QMS/concept-graph.yaml` via CR)
- [ ] Evaluate whether verb-typed edges are needed based on real usage
- [ ] Fragment compilation is a later phase, after the concept graph proves its value
