# QMS CLI Reusability Vision

*Long-term architectural goal — not for immediate implementation*

## Summary

Transform qms-cli from a project-specific tool tightly coupled to pipe-dream into a **reusable framework** that can bootstrap and manage QMS projects for any software development effort.

## Current State (Problems)

- qms-cli is hardcoded to expect `.claude/users/`, `.claude/agents/`
- User identities and group memberships are hardcoded in `qms_config.py`
- Document types and paths are hardcoded
- Cannot be used in another project without significant modification

## Desired End State

### qms-cli as Standalone Tool

```
qms-cli/                        # Standalone git repo, potentially pip-installable
├── qms.py                      # CLI entry point
├── commands/
├── ...
├── templates/                  # Shipped boilerplate
│   ├── SOPs/                   # Universal procedural docs (SOP-001 through SOP-007)
│   └── TEMPLATES/              # Document templates (CR, SOP, INV, etc.)
└── setup/                      # Init/bootstrap logic
```

### New User Experience

```bash
# Install qms-cli
pip install qms-cli  # or clone locally

# Initialize a QMS project for their codebase
qms init --project ~/code/my-app --name "My App"

# Result: A new QMS project structure
my-app-qms/
├── QMS/
│   ├── SOP/                    # Copied from qms-cli templates
│   ├── TEMPLATE/
│   ├── CR/                     # Empty, ready for use
│   ├── INV/                    # Empty
│   └── SDLC-MY-APP/            # Boilerplate RS, RTM for their project
├── users/
├── agents/
└── qms.config.yaml             # Configuration pointing to ~/code/my-app
```

### What Ships with qms-cli

| Content | Description |
|---------|-------------|
| SOPs | Universal procedural documents (Document Control, Change Control, etc.) |
| Templates | Boilerplate for CRs, INVs, TPs, etc. |
| Agent definitions | Default QA, TU, BU agent prompts |
| Setup commands | `qms init`, `qms add-user`, `qms configure` |

### What Is Project-Specific (Created by User)

| Content | Description |
|---------|-------------|
| CRs, INVs | Change records and investigations for their project |
| SDLC-{PROJECT} | RS and RTM specific to their codebase |
| User configuration | Which users exist, their group memberships |
| Project path | Where the governed codebase lives |

## The pipe-dream QMS Project Is Special

The current pipe-dream QMS is unique because:

1. **Source of truth for SOPs**: The SOPs in pipe-dream's QMS are the *source* that would be shipped with qms-cli, not copies
2. **Contains SDLC-QMS**: Qualification documents for qms-cli itself (recursive governance)
3. **Contains SDLC-FLOW**: Qualification documents for Flow State
4. **Governs two codebases**: Both flow-state and qms-cli

Most users would have a simpler setup governing a single codebase.

## Open Questions

1. **SOP versioning**: When users `qms init`, do they get a *copy* of SOPs (that they own and can modify) or a *reference* (always uses qms-cli's shipped version)?

2. **Where does SDLC-QMS live?**: It qualifies qms-cli. Does qms-cli have its own embedded QMS project for self-governance? Or does it remain in pipe-dream's QMS?

3. **Configuration schema**: What does `qms.config.yaml` look like? What's required vs. optional?

4. **Agent definitions**: Are these copied or referenced? Can users customize them?

## Relationship to Restructuring

This vision depends on the pipe-dream restructuring (see `restructuring-plan.md`):
- qms-cli must be extracted into its own repo before it can be made portable
- The QMS Project (QMS/, users/, agents/) must be separable from the governed code

---

*Captured: Session-2026-01-17-001*
