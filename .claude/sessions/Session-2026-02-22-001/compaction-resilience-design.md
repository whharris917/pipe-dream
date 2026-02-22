# Compaction Resilience Design

**Version:** 2 (updated after community/documentation research)

## Problem Statement

During long-running tasks — particularly when the Lead is away from the desk — conversation compaction can occur without warning, causing post-compaction Claude to lose critical context about in-progress work. This has resulted in session discontinuities, repeated session initialization, and lost execution state.

## Discovery (Session-2026-02-22-001)

### Transcript Investigation

Investigation of Claude Code's conversation transcript format (JSONL files in `~/.claude/projects/`) revealed:

- Transcripts are append-only JSONL files with message types: `user`, `assistant`, `summary`, `system`, `file-history-snapshot`
- `{"type":"summary"}` entries mark compaction events with a short title and `leafUuid` pointing to the last pre-compaction message
- The detailed summary content is NOT stored in the JSONL — only a title. The full summary is generated at compaction time and injected into the model's context window
- Some sessions have 50+ compaction events in a single transcript

### Official Documentation Findings

1. **Post-compaction summary is detailed.** The model receives a multi-paragraph summary. The default prompt asks for "state, next steps, learnings." Not just a headline.
2. **No pre-compaction signal exists for the model.** The "N% until compaction" metric is user-facing only. The model receives no warning.
3. **Compact Instructions in CLAUDE.md** can guide the compaction summarizer. Direct lever on summary quality.
4. **Manual compaction** (`/compact [focus]`) allows user-triggered compaction with a specific focus.
5. **Auto-compaction triggers at ~83.5% of context** (200K window = ~167K tokens). A fixed ~33K token buffer is reserved.

### Hook System (Game-Changer)

Claude Code has a comprehensive hook system with lifecycle events that directly address our problem:

**PreCompact hook** (shipped, real):
- Fires BEFORE compaction occurs
- Receives: `trigger` ("manual" or "auto"), `custom_instructions`, `transcript_path`, `session_id`
- Has access to the full conversation transcript via `transcript_path`
- Cannot block compaction (no decision control) — used for side effects like state capture
- Only supports `type: "command"` hooks
- `async: true` available to avoid blocking the compaction process

**SessionStart hook** with `compact` matcher:
- Fires AFTER compaction completes, when the session resumes
- Can inject `additionalContext` into the model's context
- Any stdout text is added as context Claude can see and act on
- This is how we can feed recovered state back to post-compaction Claude

**StatusLine** (user-facing, runs every turn):
- Receives JSON payload with `context_window.remaining_percentage`
- Can trigger threshold-based backups (e.g., at 30%, 15%, 5% remaining)
- Not directly visible to the model, but can trigger side effects

### Community Patterns

- **Three-file architecture**: StatusLine monitor + PreCompact backup + threshold-based captures
- **Token-based triggers**: Backups starting at 50K tokens, then every 10K tokens
- **Percentage-based safety net**: 30%, 15%, 5% remaining thresholds
- **ContextStream project**: Automated session preservation via hooks
- **Recovery workflow**: After compaction, read backup file to restore context

Sources:
- [Claude Code Best Practices](https://code.claude.com/docs/en/best-practices)
- [Hooks Reference](https://code.claude.com/docs/en/hooks)
- [Compaction - Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/compaction)
- [PreCompact/PostCompact Hook Feature Request - GitHub #17237](https://github.com/anthropics/claude-code/issues/17237)
- [PostCompact Hook Feature Request - GitHub #14258](https://github.com/anthropics/claude-code/issues/14258)
- [Pre-compaction Hook Feature Request - GitHub #15923](https://github.com/anthropics/claude-code/issues/15923)
- [Claude Code Context Backups](https://claudefa.st/blog/tools/hooks/context-recovery-hook)

---

## Design: Defense in Depth

Five layers, from cheapest to most complex:

### Layer 1: Compact Instructions (CLAUDE.md Addition)

Add a `## Compact Instructions` section to CLAUDE.md. This is the highest-leverage, lowest-effort change — it directly shapes what the compaction summarizer preserves.

```markdown
## Compact Instructions

When summarizing this conversation for context compaction, preserve:

1. **Session identity:** The current session ID (from CURRENT_SESSION file)
2. **Active QMS document:** Document ID, status, current execution item number
3. **Work completed this session:** List of EIs completed, commits made, documents routed
4. **Work in progress:** What was actively being done when compaction occurred
5. **Pending decisions:** Any unresolved questions or choices awaiting user input
6. **Agent state:** IDs of any spawned subagents that should be resumed
7. **Key file paths:** Files currently being edited or recently created

Do NOT spend summary space on:
- SOP content (available on disk via `QMS/SOP/`)
- CLAUDE.md content (re-injected automatically)
- Historical project context (available in `.claude/PROJECT_STATE.md`)
- Full code snippets (available via file reads)
- Tool output contents (available via re-reading files)
```

### Layer 2: Incremental Session Notes (Behavioral Change)

Instead of writing session notes only at session end, write them incrementally as work progresses. This creates a durable record on disk that survives compaction.

**Trigger points for session note updates:**
- After completing each execution item (EI)
- After any QMS routing event (review, approval, etc.)
- After any commit
- After any significant decision or discovery
- Before starting a long autonomous sequence

**Session notes format:**

```markdown
# Session-YYYY-MM-DD-NNN

## Current State (last updated: [timestamp])
- **Active document:** CR-096 (IN_EXECUTION)
- **Current EI:** EI-5 (RTM update)
- **Blocking on:** Nothing
- **Next:** EI-6 (merge to main)
- **Subagent IDs:** qa=abc123

## Progress Log

### [HH:MM] EI-3: Tests
- Wrote 14 tests in test_foo.py
- All passing (487/487)
- Commit: abc1234

### [HH:MM] EI-4: RS Update
- Added REQ-FOO-001 through REQ-FOO-003
- RS routed for review
```

**Key principle:** The "Current State" block at the top is the recovery target. It should always reflect where work stands RIGHT NOW. The progress log below provides audit trail.

### Layer 3: PreCompact Hook (Automated State Capture)

A shell script that fires before compaction to capture session state to disk. This is the "last chance" safety net.

**Configuration** (`.claude/settings.json` or `.claude/settings.local.json`):

```json
{
  "hooks": {
    "PreCompact": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pre-compact.sh",
            "async": true
          }
        ]
      }
    ]
  }
}
```

**Hook script** (`.claude/hooks/pre-compact.sh`):

```bash
#!/bin/bash
# Pre-compaction state capture
# Reads session ID from CURRENT_SESSION and copies the current transcript
# to the session folder for post-compaction recovery.

INPUT=$(cat)
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path')
TRIGGER=$(echo "$INPUT" | jq -r '.trigger')
PROJECT_DIR=$(echo "$INPUT" | jq -r '.cwd')

SESSION_FILE="$PROJECT_DIR/.claude/sessions/CURRENT_SESSION"
if [ -f "$SESSION_FILE" ]; then
    SESSION_ID=$(cat "$SESSION_FILE" | tr -d '[:space:]')
    SESSION_DIR="$PROJECT_DIR/.claude/sessions/$SESSION_ID"
    mkdir -p "$SESSION_DIR"

    # Record compaction event
    echo "$(date -Iseconds) | COMPACTION ($TRIGGER) | transcript: $TRANSCRIPT_PATH" \
        >> "$SESSION_DIR/compaction-log.txt"
fi
```

### Layer 4: SessionStart Hook — Post-Compaction Recovery

A hook that fires after compaction completes, injecting session state back into Claude's context.

**Configuration:**

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "compact",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/post-compact-recovery.sh"
          }
        ]
      }
    ]
  }
}
```

**Hook script** (`.claude/hooks/post-compact-recovery.sh`):

```bash
#!/bin/bash
# Post-compaction context recovery
# Reads session notes and injects them as additional context.

INPUT=$(cat)
PROJECT_DIR=$(echo "$INPUT" | jq -r '.cwd')

SESSION_FILE="$PROJECT_DIR/.claude/sessions/CURRENT_SESSION"
if [ -f "$SESSION_FILE" ]; then
    SESSION_ID=$(cat "$SESSION_FILE" | tr -d '[:space:]')
    NOTES_FILE="$PROJECT_DIR/.claude/sessions/$SESSION_ID/notes.md"

    if [ -f "$NOTES_FILE" ]; then
        echo "=== POST-COMPACTION RECOVERY ==="
        echo "Session: $SESSION_ID"
        echo "A context compaction has just occurred. Your session notes from before compaction are below."
        echo "Use these to verify your compaction summary and resume work from the correct point."
        echo ""
        cat "$NOTES_FILE"
        echo ""
        echo "=== END RECOVERY CONTEXT ==="
    else
        echo "=== POST-COMPACTION NOTICE ==="
        echo "Session: $SESSION_ID"
        echo "Context compaction occurred. No session notes found — read .claude/PROJECT_STATE.md for context."
        echo "=== END NOTICE ==="
    fi
fi
```

The stdout of this hook is added to Claude's context, so post-compaction Claude will see the session notes and can verify continuity.

### Layer 5: User Guidance (Documentation)

Add to CLAUDE.md Session Management section:

**For the Lead (before stepping away):**
1. Ask Claude to update session notes
2. Optionally run `/compact focus on [current task description]`
3. This gives the compaction summarizer the best possible input

**For Claude (post-compaction behavioral protocol):**
When detecting a post-compaction resume (via the SessionStart hook injecting recovery context, or via the session start checklist's "continuation after consolidation" path):
1. Read CURRENT_SESSION to confirm session identity
2. Read session notes from the current session folder
3. Compare compaction summary against session notes
4. Announce: "Context compaction occurred. Recovered state from session notes. Resuming [task]."
5. Resume work from where the session notes indicate

---

## Implementation Plan

### Phase 1: Immediate (no hooks, just CLAUDE.md and behavior)
1. Add Compact Instructions section to CLAUDE.md
2. Update session start checklist with post-compaction recovery steps
3. Begin writing incremental session notes (behavioral discipline)

### Phase 2: Hook Infrastructure
4. Create `.claude/hooks/` directory
5. Write and test `pre-compact.sh`
6. Write and test `post-compact-recovery.sh`
7. Add hook configuration to `.claude/settings.local.json`

### Phase 3: Refinement
8. Test with a real compaction event (long session or `/compact`)
9. Tune the Compact Instructions based on what the summary actually captures
10. Consider StatusLine-based threshold monitoring if hooks alone aren't sufficient

---

## Design Decisions

**Why not StatusLine monitoring?** StatusLine provides `remaining_percentage` but only runs a shell command — it can't signal the model. We'd need it to write a file, then the model would need to read that file, which requires the model to know to check. The PreCompact + SessionStart hook combination is simpler and more reliable: the hooks fire automatically at the right moments.

**Why `async: true` on PreCompact?** The backup shouldn't slow down compaction. The hook captures a snapshot timestamp and transcript path — fast operations that complete before compaction finishes summarizing.

**Why trust session notes over the compaction summary?** Session notes were written incrementally from full context by the pre-compaction Claude. The compaction summary is a lossy compression generated by a single model call. When they disagree, the notes are more reliable.

**Why not block compaction?** PreCompact hooks cannot block compaction (by design). This is correct — if context is full, compaction must happen. Our goal is resilience, not prevention.

---

## Open Questions (Resolved)

- ~~Should we formalize the incremental note format?~~ Yes — the "Current State" block at top + progress log format gives structure without rigidity.
- ~~How frequently should notes be updated?~~ After each EI, routing event, commit, or significant decision. The PreCompact hook is the safety net if Claude forgets.
- ~~Should post-compaction Claude announce compaction?~~ Yes — the SessionStart hook injects recovery context, and the behavioral protocol says to announce it.
- ~~Are there other Compact Instructions patterns?~~ Community confirms: "always preserve the full list of modified files and any test commands" is a common pattern. Our version is more specific to QMS workflows.
