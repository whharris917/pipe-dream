# Session 2026-02-14-004: CR-080 Terminal Scrollback Support

## Summary

Diagnosed and fixed terminal scrollback in the Agent Hub GUI. The problem had three independent layers that all needed simultaneous resolution. CR-080 created, executed, and closed in one session.

## What Was Done

### Diagnosis

Scrollback was broken despite xterm.js being configured with `scrollback: 10000`. Research agents investigated Claude Code's rendering architecture, the PTY pipeline, and xterm.js scrollback mechanics. Found three blockers:

1. **Mouse tracking** (ESC[?1000h, ESC[?1006h) — Claude Code enables mouse tracking, causing xterm.js to forward wheel events to the app instead of scrolling the buffer
2. **Alternate screen buffer** (ESC[?1049h) — tmux sends this on attach; alt screen has zero scrollback in xterm.js
3. **ESC[3J (Erase Saved Lines)** — Claude Code's Ink-based differential renderer clears scrollback on every render cycle. This was the primary blocker.

### Fix

Added `stripTerminalModes()` function in `useHubConnection.ts` that filters PTY output before writing to xterm.js. Strips:
- Mouse tracking DECSET/DECRST (modes 1000, 1002, 1003, 1005, 1006, 1015)
- Alternate screen modes (47, 1047, 1049)
- Scrollback clear (ESC[3J) and full reset (ESC c)

Applied to both initial buffer replay and ongoing output streams.

### Iterative Commits

| Commit | Description |
|--------|-------------|
| `1220914` | Wheel event interceptor (didn't work — alt screen has no scrollback) |
| `a6b480a` | Strip mouse tracking + alt screen sequences (partial improvement) |
| `91355af` | Strip ESC[3J — significant improvement |
| `807a69a` | Strip ESC c + debug logging |
| `c6664c8` | Buffer state diagnostics (confirmed fix working) |
| `debb48f` | Remove all temporary debug logging |
| `3c8a70d` | CR-080 closed, PROJECT_STATE updated |

### QMS Workflow

- CR-080 created, pre-reviewed, pre-approved, released for execution
- Post-review caught stale `revision_summary` frontmatter — fixed and re-routed
- Post-approved and closed

### Backlog Item Logged

Observed separate issue: tmux `new-session` in `container.py:279` has no `-x`/`-y` flags, defaults to 80x24. Agent TUI tables render for wrong width until GUI resize arrives. Logged in PROJECT_STATE.md under GUI Polish.

## Files Modified

- `agent-hub/gui/src/hooks/useHubConnection.ts` — `stripTerminalModes()` filter function
- `agent-hub/gui/src/components/Terminal/TerminalView.tsx` — Temporary debug logging (added then removed)
- `.claude/PROJECT_STATE.md` — Backlog item for tmux initial dimensions

## Key Insight

Claude Code uses React + Ink with a custom differential cell-diffing renderer. It deliberately avoids alternate screen buffer but enables mouse tracking and clears scrollback (ESC[3J) on every render cycle. For a monitoring terminal, all three of these behaviors must be neutralized for scrollback to work.
