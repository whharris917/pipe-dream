# Session 2026-01-24-004 Summary

## Focus
Designed and drafted CR-036: Add qms-cli initialization and bootstrapping functionality.

## Problem Statement
A developer cloning qms-cli from GitHub cannot use it without extensive manual setup. The tool lacks initialization/bootstrapping code to create QMS/ directories, user workspaces, document templates, and SOPs.

## Key Decisions Made

### 1. Config File Discovery
- Use `qms.config.json` as project root marker
- Walk up from cwd to find it
- Fall back to existing QMS/ directory discovery (backward compatibility)

### 2. `qms init` Command
- Creates all QMS infrastructure in current working directory (one level above qms-cli/)
- `--root` flag for alternate location
- **Safety checks**: Must have completely clear runway (no QMS/, no .claude/users/, no qa.md, no config file)
- Only proceeds if ALL checks pass

### 3. User Management Model
- **Hardcoded users**: `lead` and `claude` are administrators (no agent files needed)
- **Agent-based users**: All others defined via `.claude/agents/{user}.md` with `group:` frontmatter
- **Default shipped**: Only `qa.md` ships with qms-cli
- Groups: `administrator`, `initiator`, `quality`, `reviewer`
- Unknown users get helpful error pointing to agent file creation

### 4. SOP Seeding
- Sanitized copies of SOPs (v1.0, EFFECTIVE, no CR/INV references)
- Document templates included

### 5. Test Environment
- `.test-env/` inside pipe-dream (gitignored)
- Clone qms-cli fresh into test environment
- Development branch: `cr-036-init`
- All testing happens against disposable test QMS

### 6. Qualified State Continuity
- Development happens on branch, main stays qualified
- RS/RTM checked out as drafts in production QMS
- Only after merge + RS/RTM approval does version transition (CLI-1.0 → CLI-2.0)
- Atomic transition maintains continuous qualification

## CR-036 Status
- **Status**: DRAFT, checked in
- **Version**: 0.1
- **Execution Items**: 18 (EI-1 through EI-18)
- **Not yet routed** for pre-review

## pipe-dream Migration Required
When CR-036 is implemented, pipe-dream's agent files need `group:` added:
- qa.md → `group: quality`
- bu.md, tu_ui.md, tu_scene.md, tu_sketch.md, tu_sim.md → `group: reviewer`

(lead and claude are hardcoded, no changes needed)

## Commits
1. `de4430d` - CR-036: Add qms-cli initialization and bootstrapping functionality (draft)
2. `ebf5624` - CR-036: Clarify lead/claude are hardcoded administrators

## Next Steps
1. Route CR-036 for pre-review
2. QA assigns reviewers
3. After pre-approval, begin execution (set up test environment, implement features)
