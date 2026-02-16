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

- Experiment with the concept graph first, independent of the fragment/compiler system
- Design the concept vocabulary and graph structure
- Fragment compilation is a future phase, to be explored after the concept graph proves its value
