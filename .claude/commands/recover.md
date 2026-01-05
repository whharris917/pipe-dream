---
description: Recover from a crashed session - creates chronicle for crashed session and sets up current session
allowed-tools: Bash, Read, Glob, Write
---

# Session Crash Recovery Protocol

**CRITICAL CONTEXT:** The previous Claude Code session crashed unexpectedly (e.g., system reboot, power loss, application crash). The SessionEnd hook did not run, so no chronicle was created for that session. You are now in a NEW session that needs to:

1. Recover the crashed session's chronicle
2. Set up properly as the next session

## Your Recovery Tasks

### Step 1: Determine Session Numbers

Read `.claude/chronicles/INDEX.md` to find the last recorded session. The crashed session is N (the one AFTER the last recorded), and you are currently in session N+1.

**Example:** If INDEX.md shows the last entry is `Session-2026-01-05-001`, then:
- Crashed session = `Session-2026-01-05-002`
- Current session (you) = `Session-2026-01-05-003`

**Important:** Check if a session notes folder exists for what would be the crashed session (`.claude/notes/Session-YYYY-MM-DD-NNN/`). If it exists but has no corresponding chronicle file, that confirms the crash scenario.

### Step 2: Create Current Session Notes Folder

Create the notes folder for your ACTUAL session (N+1):
```
.claude/notes/Session-YYYY-MM-DD-NNN/
```

### Step 3: Find the Crashed Session's Transcript

Transcripts are stored in:
```
~/.claude/projects/c--Users-wilha-projects-pipe-dream/
```

List files modified on today's date (or the crash date). Main session transcripts are UUIDs like `442e9e23-5ead-4e8e-a3ba-3370b8ab32f5.jsonl` (not `agent-*.jsonl` which are subagents).

To identify which transcript is the crashed session:
- Check file modification times
- Look at the first few lines of suspect files to see the user's first message
- The crashed session transcript will be the one modified BEFORE the current session started

### Step 4: Run the Recovery Script

Execute the emergency recovery script:
```bash
python .claude/hooks/emergency_chronicle_recovery.py "<transcript_path>" "Session-YYYY-MM-DD-NNN"
```

Where:
- `<transcript_path>` is the full path to the crashed session's transcript file
- `Session-YYYY-MM-DD-NNN` is the crashed session's name (N, not N+1)

This script will:
- Create the chronicle file in `.claude/chronicles/`
- Update INDEX.md with a `*(recovered)*` marker

### Step 5: Read Previous Session Notes

Read all files in the crashed session's notes folder:
```
.claude/notes/{CRASHED_SESSION_ID}/
```

### Step 6: Read CLAUDE.md

**Now** read `CLAUDE.md` in the project root. This file contains critical project context, your identity, and operational guidelines.

**Important:** Do NOT follow the "Session Start Checklist" instructions in CLAUDE.md for creating a session notes folder or determining session ID—you have already done this correctly in the steps above. Only absorb the project context, architecture details, and operational rules.

### Step 7: Complete Normal Session Start

Finish the remaining session start tasks:
- Read all SOPs in `QMS/SOP/`
- Report ready for the user's direction

## Summary

After recovery, you should have:
- [ ] Chronicle for crashed session N created and indexed
- [ ] Notes folder for current session N+1 created
- [ ] Previous session notes read
- [ ] SOPs read
- [ ] Ready to proceed with current session

**Report your findings clearly:** State which session crashed, which session you are, and confirm all recovery steps completed.
