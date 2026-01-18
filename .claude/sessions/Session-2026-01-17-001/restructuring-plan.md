# Pipe Dream Restructuring Plan

*Discussion notes — no implementation until explicitly approved*

## Problem Statement

The current pipe-dream repository has several structural problems:

1. **Tight coupling**: qms-cli is hardcoded to pipe-dream's directory structure
2. **Interleaved git history**: Flow State code commits, QMS CLI commits, and QMS document commits all share the same timeline
3. **Testing paradox**: When agents branch to test code changes, the SOPs and inbox tasks move with them — the governance layer shouldn't be subject to the same branching as the governed code

## Current Structure

```
pipe-dream/                     # Single git repo
├── qms-cli/                    # QMS CLI tool code
├── QMS/                        # Controlled documents (SOPs, CRs, etc.)
│   ├── SOP/
│   ├── CR/
│   ├── .meta/
│   ├── .audit/
│   └── SDLC-*/
├── .claude/
│   ├── users/                  # Workspaces and inboxes
│   └── agents/                 # Agent definition files
├── core/                       # Flow State game code
├── engine/
├── model/
├── ui/
└── main.py
```

## Proposed Structure

```
pipe-dream/                     # Git repo (preserves existing history)
├── .gitmodules                 # Submodule references
├── qms-cli/                    # Git submodule → own repo
├── flow-state/                 # Git submodule → own repo
├── QMS/                        # Stays in pipe-dream (QMS Project)
└── .claude/                    # Stays in pipe-dream (QMS Project)
    ├── users/
    └── agents/
```

After restructuring:
- **pipe-dream**: QMS Project (documents, users, agents) + submodule pointers
- **qms-cli**: Standalone git repo (the tool)
- **flow-state**: Standalone git repo (the game)

## Git History Implications

### pipe-dream History

```
commits 1-N: (all existing history preserved intact)
commit N+1:  "CR-XXX: Restructure into submodules"
             - Removes code directories from direct tracking
             - Adds .gitmodules
commit N+2+: QMS document changes, submodule pointer updates
```

### qms-cli History (new repo)

- Contains only commits that touched qms-cli files
- Paths rewritten (qms-cli/qms.py → qms.py)
- Different commit hashes than originals (due to path rewriting)
- Original commits still exist in pipe-dream

### flow-state History (new repo)

- Contains only commits that touched flow-state files
- Paths rewritten (core/, engine/, etc. → root level)
- Different commit hashes than originals
- Original commits still exist in pipe-dream

## Key Decisions

### No History Loss

All history is preserved:
- pipe-dream retains complete original history
- Extracted repos have copies with rewritten paths
- Any historical state can be reconstructed by checking out old pipe-dream commits

### Commit Hash Discontinuity

- Old CRs reference commits in pipe-dream (e.g., `abc123`)
- New CRs will reference commits in flow-state or qms-cli
- This is a navigation inconvenience, not information loss
- The transition CR should document this discontinuity

### Extraction Method

Use `git subtree split` or `git filter-repo` to extract subdirectories:

```bash
# Example: Extract qms-cli with its history
git subtree split --prefix=qms-cli -b qms-cli-history
# Push to new repo
git push git@github.com:user/qms-cli.git qms-cli-history:main
```

## Benefits

1. **Agents can branch flow-state for testing** without affecting QMS documents, SOPs, or inbox state

2. **qms-cli becomes portable** — can be used in other projects (see `qms-cli-reusability-vision.md`)

3. **Cleaner separation of concerns** — code changes and governance changes have separate commit streams

4. **Independent release cycles** — flow-state can be versioned/tagged independently of qms-cli

## Migration Checklist (Draft)

- [ ] Create CR authorizing the restructuring
- [ ] Create new empty repos for qms-cli and flow-state
- [ ] Extract qms-cli history using git subtree split or filter-repo
- [ ] Extract flow-state history
- [ ] Push extracted histories to new repos
- [ ] Update pipe-dream to use submodules
- [ ] Update qms-cli to support external configuration
- [ ] Update any hardcoded paths in qms-cli
- [ ] Document the transition point and commit hash mapping
- [ ] Update CLAUDE.md with new project structure

## Open Questions

1. **Submodule update strategy**: When flow-state is updated, how/when do we update the submodule pointer in pipe-dream?

2. **CI/CD implications**: How do we test qms-cli against flow-state if they're separate repos?

3. **Clone instructions**: New contributors need to know to use `--recurse-submodules`

4. **SDLC-QMS location**: Does it stay in pipe-dream (governing qms-cli externally) or move into qms-cli (self-governance)?

---

*Captured: Session-2026-01-17-001*
