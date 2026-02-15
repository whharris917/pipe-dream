# Session 2026-02-14-005: CR-081 tmux Terminal Dimensions

## Summary

Created and partially executed CR-081 to fix tmux default terminal dimensions. Code changes are implemented but manual testing revealed deeper issues with the terminal rendering pipeline that need further investigation.

## What Was Done

### Investigation

Thorough analysis of the terminal dimension pipeline:
- `container.py:279` creates tmux session at 80x24 (no `-x`/`-y` flags)
- GUI's xterm.js measures actual dimensions (often 120-180 cols)
- Resize only propagates after `fitAddon.fit()` on the next animation frame (16-50ms delay)
- Content rendered at 80 columns during that gap appears misaligned

### CR-081 Implementation (3 files modified)

| File | Change |
|------|--------|
| `agent-hub/agent_hub/config.py:50-52` | Added `default_terminal_cols: int = 120` and `default_terminal_rows: int = 30` |
| `agent-hub/agent_hub/container.py:278-292` | `_exec_claude()` passes `-x`/`-y` from config to `tmux new-session` |
| `agent-hub/gui/src/hooks/useHubConnection.ts:137-142` | `subscribed` handler sends `sendResize()` immediately after buffer replay |

### QMS State

- CR-081: IN_EXECUTION v1.1 (EI-1 through EI-3 Pass, EI-4 pending manual verification)
- Pre-reviewed and pre-approved by QA (agent aa0f47f)

## Issues Found During Manual Testing

### Issue 1: Mid-render resize breaks table formatting

The QA agent's TUI table rendered with inconsistent column widths — upper rows at one width, lower rows at a different width. This is caused by the resize arriving mid-render: tmux started at 120 cols, but the GUI window was narrower, so the subscribe-time resize triggered SIGWINCH while Claude Code was still rendering its initial output.

**Root cause:** The timing gap between tmux creation and GUI dimension sync cannot be fully eliminated with the current architecture. The Hub doesn't know GUI dimensions at container creation time.

### Issue 2: Duplicate content on window resize (more impactful)

When the window was maximized, the QA agent's content appeared twice — the old render (at the smaller width) and the new render (at the maximized width) were both visible in the scrollback.

**Root cause:** This is a direct consequence of CR-080's scrollback fix. Claude Code sends ESC[3J (clear scrollback) before every re-render to prevent exactly this duplication. CR-080 strips ESC[3J to preserve scrollback, which means every resize-triggered re-render produces duplicate content.

**This was not visible during CR-080 testing** because the window wasn't resized during those tests.

### Potential Fix Direction (not yet implemented)

Instead of stripping ESC[3J entirely, convert it to ESC[2J (erase visible screen only). This would let Claude Code's re-render replace the visible content without destroying scrollback history. Needs investigation — unclear if this fully solves the problem given how Ink's differential renderer works.

## Open Questions for Next Session

1. Should Issue 2 (duplication) be addressed within CR-081, or should it be a separate CR? It's arguably a regression from CR-080.
2. Is converting ESC[3J → ESC[2J sufficient, or does the Ink renderer need more nuanced handling?
3. Should the default dimensions (120x30) be reduced to something more conservative (e.g., 100x24) to reduce the chance of Issue 1?
4. Is there a way to defer tmux session creation until the GUI sends its dimensions? (Architectural change, probably not worth the complexity.)

## Files Modified (uncommitted)

- `agent-hub/agent_hub/config.py`
- `agent-hub/agent_hub/container.py`
- `agent-hub/gui/src/hooks/useHubConnection.ts`
