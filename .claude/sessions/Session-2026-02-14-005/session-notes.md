# Session 2026-02-14-005 (continued 2026-02-15): CR-081 Terminal Dimensions + Control Mode

## Summary

CR-081 (fix tmux default terminal dimensions) and CR-081-VAR-001 (switch PTY manager to tmux control mode) both completed full lifecycles and are CLOSED. Terminal scrollback, input, and resize all work correctly in the Agent Hub monitoring GUI.

## What Was Done

### CR-081: Terminal Dimension Fixes (2026-02-14)

| File | Change |
|------|--------|
| `agent-hub/agent_hub/config.py:50-52` | Added `default_terminal_cols: int = 120` and `default_terminal_rows: int = 30` |
| `agent-hub/agent_hub/container.py:278-292` | `_exec_claude()` passes `-x`/`-y` from config to `tmux new-session` |
| `agent-hub/gui/src/hooks/useHubConnection.ts` | `subscribed` handler sends resize immediately |

EI-1 through EI-3 Pass. EI-4 (manual verification) deferred to Lead, which triggered the VAR.

### CR-081-VAR-001: tmux Control Mode (2026-02-15)

Manual testing of CR-081 revealed that tmux's viewport rendering creates a double-terminal-emulator problem — tmux re-renders Claude Code's output as cursor-positioned viewport updates, destroying scrollback semantics. Multiple workaround approaches failed. The correct solution: tmux control mode (`tmux -CC`), which delivers Claude Code's raw PTY bytes via a line-based protocol.

**pty_manager.py — Major rewrite:**
- `attach()`: `sh -c "stty raw -echo && exec tmux -CC attach -t agent"`
- `_read_loop()`: Line-based parser with `%output` decoding and `%begin/%end` block collection
- `_decode_octal()`: Octal escape → raw bytes (with UTF-8 passthrough for box-drawing chars)
- `_decode_control_output()`: `%output %PANE_ID PAYLOAD` parser
- `_encode_send_keys()`: Bytes → `send-keys -t agent -H XX XX...` hex format
- `resize()`: `refresh-client -C {cols}x{rows}` via control mode socket
- `capture-pane -p -e -t %0` on attach for initial screen content

**useHubConnection.ts — Simplified + duplication fix:**
- Removed: `EXTEND_SCROLL_REGION_RE`, `SCROLL_UP_RE`, `scrollback` parameter, `resizePending` Map, DA response filtering
- Kept: `STRIP_MODES_RE` (mouse tracking), alt-screen stripping
- Added: ESC[3J → ESC[2J conversion (preserve scrollback during normal operation)
- Added: `pendingRerender` tracking — on subscribe, clears viewport before resize; on first output after any resize, `term.clear()` wipes viewport + scrollback so re-render replaces all stale content
- Added: 1.5s ring buffer fallback for when resize doesn't trigger re-render

**test_control_mode.py — 32 unit tests:**
- `TestDecodeOctal`: 14 tests (including Unicode passthrough)
- `TestDecodeControlOutput`: 11 tests
- `TestEncodeSendKeys`: 7 tests

### Debugging Iterations (during EI-4)

1. **CRLF line endings** — Control mode uses `\r\n`; `.rstrip('\r')` on every parsed line
2. **No initial screen content** — Control mode only delivers NEW output; added `capture-pane` with `%begin/%end` block parser
3. **Unicode crash** — `ord(ch)` fails for chars > 255; changed to `ch.encode('utf-8')`
4. **Startup duplication** — Ring buffer + resize-triggered re-render; fixed with screen clear before resize + fallback timer
5. **Resize duplication** — Old content in scrollback + re-render appended; fixed with `term.clear()` on first output after resize

### QMS Lifecycle

| Document | Lifecycle |
|----------|-----------|
| CR-081 | DRAFT → PRE_REVIEWED → PRE_APPROVED → IN_EXECUTION → POST_REVIEWED → POST_APPROVED → **CLOSED** (v2.0) |
| CR-081-VAR-001 | DRAFT → PRE_REVIEWED → PRE_APPROVED → IN_EXECUTION → POST_REVIEWED → POST_APPROVED → **CLOSED** (v2.0) |

QA agent (aed1f2d) handled all reviews/approvals. One post-review rejection (Section 8 closure placeholders) — corrected and re-reviewed.

## Commits

| Hash | Description |
|------|-------------|
| `1d7482c` | CR-081: Fix tmux terminal dimensions and enable scrollback in monitoring GUI |
| `e1d5802` | CR-081-VAR-001: Switch PTY manager to tmux control mode |
| `5ce08da` | CR-081-VAR-001: Fix terminal duplication on subscribe and resize |
| `eb5ddea` | CR-081-VAR-001 closed |
| `32f0465` | CR-081-VAR-001: EI-4 Pass, routed for post-review |
| `7cd222b` | CR-081 closed |
