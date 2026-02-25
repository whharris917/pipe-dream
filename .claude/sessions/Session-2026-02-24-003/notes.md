# Session-2026-02-24-003

## Current State (last updated: end of session)
- **Active document:** None (workshop edits, no QMS document)
- **Blocking on:** Nothing
- **Next:** Workshop edits ready for Lead review. CR needed to propagate changes to controlled submodules.

## Progress Log

### Session Start
- Continued from Session-2026-02-24-002 (CR-105 closed, all SDLC docs effective)
- Project state: 687 tests, RS v22.0, RTM v27.0, CQ-RS v2.0, CQ-RTM v2.0
- Quality-Manual submodule established in both claude-qms and pipe-dream

### .QMS-Docs vs Quality-Manual Comparison
- Confirmed `.QMS-Docs/` and `Quality-Manual/` are identical (38 files, same content)
- `.QMS-Docs/` is a legacy regular directory; `Quality-Manual/` is the canonical submodule
- Added backlog item: delete `.QMS-Docs/` in a future CR

### Platform Issues (Claude Code v2.1.53)
- Bash EINVAL regression: stdio handling changed from pipes to file descriptors, breaks Git Bash/MSYS2 on Windows (GitHub #26545)
- Attempted npm downgrade to v2.1.44 — temporarily fixed Bash, but auto-updater overrode to v2.1.53
- CLAUDE_PROJECT_DIR env var empty on Windows — known bug (#6023)
- Write guard hook errors but doesn't block (non-fatal)
- Decision: persevere without Bash, use Read/Write/Edit/Glob/Grep tools only

### Workshop Setup
- Copied Quality-Manual (39 files) into `.claude/workshop/Quality-Manual/`
- Copied qms-cli/docs (7 files) into `.claude/workshop/qms-cli/docs/`
- Relative links: from types/ and guides/ → `../../qms-cli/docs/cli-reference.md`

### Quality Manual Cleanup (all in workshop sandbox)
- **Audited** entire Quality Manual: 108 SOP reference hits across 17 files, 150+ CLI syntax hits across 20 files

#### Task 1: QMS-Glossary.md (DONE)
- Dropped Source column from term table
- Replaced inline SOP references in definitions with generic QMS references

#### Task 2: README.md (DONE)
- Dropped Source SOPs column
- Removed 12-CLI-Reference.md row
- Updated CLI docs link

#### Task 3: Type docs — 12 files (DONE)
- CR.md, INV.md, ER.md, VAR.md: Replaced SOP refs, stripped CLI Creation/Enforcement sections, removed Config/Metadata/Regex
- VR.md: Replaced CLI Commands + CLI Creation sections, removed Config, simplified checkin/checkout/cascade close
- ADD.md: Replaced CLI Creation/Enforcement, simplified Cascade Close
- TP.md: Fixed SOP refs, replaced CLI Creation/Enforcement, removed Validation Patterns
- SOP.md: Replaced CLI Creation/Enforcement, removed Config/Metadata, fixed See Also link
- TC.md: Replaced SOP-004 ref, simplified CLI Behavior section
- TEMPLATE.md: Replaced SOP-005 ref, replaced CLI Creation section, removed Initial Metadata, replaced CLI Commands, simplified Python code snippets
- RS.md, RTM.md: Removed regex, replaced CLI creation, simplified namespace system, removed Doc Type Resolution, replaced CLI Commands

#### Task 4: Main chapters 01-12 (DONE)
- 12-CLI-Reference.md: Replaced 390-line CLI reference with slim redirect to `../qms-cli/docs/cli-reference.md`
- All 11 numbered chapters: Redirected `12-CLI-Reference.md` links to `../qms-cli/docs/cli-reference.md`
- 03-Workflows.md: Genericized SOP-003/SOP-001 command examples to `{DOC_ID}`

#### Task 5: Guides (DONE)
- routing-quickref.md: Fixed CLI Reference link
- evidence-writing-guide.md: SOP-002 references are illustrative examples — kept as-is

#### Task 6: START_HERE.md and FAQ.md (DONE)
- Both: Redirected CLI Reference links

### Final Verification
- Zero `per SOP-` / `SOP-NNN §` / `SOP-NNN Section` references remaining
- Zero `12-CLI-Reference` links remaining
- Zero Python code blocks remaining
- Zero `re.compile` / `qms_config.py` / `qms_schema.py` / `create.py` references remaining (except legitimate illustrative examples)

### Continuation (2026-02-25)
- Bash EINVAL bug still present at start of continuation
- Investigated: native installer at `C:\Users\wilha\.local\bin\claude.exe` running v2.1.53; VS Code extension already updated to v2.1.56
- Updated native installer via PowerShell to v2.1.56 — Bash restored
- Committed workshop cleanup (eb24504) and pushed (user ran manual git commands while Bash was broken)
- Added compaction navigation guardrails to CLAUDE.md:
  - New "Compaction Log Files" section documenting `compaction-log.txt` format and use
  - Warning that compaction summaries are AI-generated and not authoritative
  - Fresh compaction log as conclusive proof of session continuation
- Committed and pushed (f99bc5d)
