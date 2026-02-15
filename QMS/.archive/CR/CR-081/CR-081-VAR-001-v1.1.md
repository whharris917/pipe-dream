---
title: Switch PTY Manager to tmux Control Mode for Terminal Scrollback
revision_summary: EI-1 through EI-3 execution results recorded
---

# CR-081-VAR-001: Switch PTY Manager to tmux Control Mode for Terminal Scrollback

## 1. Variance Identification

| Parent Document | Affected Item | VAR Type |
|-----------------|---------------|----------|
| CR-081 | EI-4 (Manual verification) / Scope expansion | Type 1 |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

VAR TYPE:
- Type 1: Full closure required to clear block on parent
- Type 2: Pre-approval sufficient to clear block on parent
-->

---

## 2. Detailed Description

CR-081's pre-approved scope addressed terminal dimension mismatch (80x24 defaults) and immediate resize-on-subscribe. EI-1 through EI-3 executed successfully. However, during execution and manual verification (EI-4), a fundamental problem with terminal scrollback was identified that cannot be solved within the pre-approved scope.

**Expected:** The changes from CR-080 (terminal scrollback support) and CR-081 (dimension fixes) would together produce a working scrollback experience in the Agent Hub monitoring GUI.

**Actual:** Terminal scrollback remains broken. The root cause is that **tmux is a terminal emulator sitting between Claude Code and xterm.js**, creating a double-terminal-emulator problem. tmux re-renders Claude Code's output as cursor-positioned viewport updates (`ESC[row;colH`), destroying scrollback semantics entirely. Multiple workaround approaches were attempted and failed:

1. **Stripping DECSTBM / scroll regions** — Broke cursor positioning because tmux calculates absolute row positions relative to the scroll region boundaries.
2. **Extending scroll regions to full terminal** (`ESC[1;999r`) — Did not produce scrollback because tmux's Scroll Up (SU) operations are viewport-relative, not buffer-relative.
3. **Converting SU to newlines at screen bottom** — Produced partial scrollback but with corrupted content (cursor-positioned overwrites rendered as literal text in scrollback).
4. **Suppressing scrollback during resize re-renders** — Addressed a symptom (duplicate content) but not the root cause.

Each approach was a progressively deeper workaround for the same fundamental problem: tmux's rendered viewport output cannot be converted back into scrollable content. No amount of escape sequence manipulation on the GUI side can recover scrollback from tmux's viewport rendering.

---

## 3. Root Cause

Scope Error — The pre-approved approach assumed that tmux's terminal output could be post-processed to restore scrollback semantics. This assumption was incorrect. tmux in normal attach mode (`tmux attach -t agent`) acts as a full terminal emulator: it interprets Claude Code's raw output, maintains its own screen buffer, and re-renders the visible viewport to the attached client using absolute cursor positioning. This rendering destroys the sequential, append-only stream of bytes that xterm.js needs for scrollback.

The correct approach — discovered through the trial-and-error process documented above — is to bypass tmux's rendering entirely by using **tmux control mode** (`tmux -CC attach -t agent`). In control mode, tmux emits a line-based text protocol where `%output` notifications contain Claude Code's **raw PTY bytes** — the exact output Claude Code wrote, before tmux renders it. xterm.js processes these raw bytes directly and handles scrollback naturally.

---

## 4. Variance Type

Scope Error — The pre-approved scope was designed around an incorrect mental model of how tmux delivers terminal output. The plan to strip/convert escape sequences was a reasonable hypothesis, but empirical testing revealed it cannot work because tmux's viewport rendering is a lossy transformation. The correct solution (control mode) requires a fundamentally different architecture for PTY communication.

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Select one:
- Execution Error: Executor made a mistake or didn't follow instructions
- Scope Error: Plan/scope was written or designed incorrectly
- System Error: The system behaved unexpectedly
- Documentation Error: Error in a document other than the parent
- External Factor: Environmental or external issue
- Other: See Detailed Description
-->

---

## 5. Impact Assessment

**What was accomplished in the parent (before the variance):**
- EI-1: Default terminal dimensions added to HubConfig (120x30) — Pass
- EI-2: Dimensions passed to `tmux new-session -x -y` — Pass
- EI-3: Resize sent on `subscribed` message — Pass
- These changes remain valid and are not affected by this VAR

**What this VAR absorbs:**
- EI-4 (manual verification) cannot pass because scrollback does not work with the current tmux attach approach
- The VAR expands scope to implement tmux control mode, which requires:
  - Major rewrite of `pty_manager.py` (attach, read loop, write, resize)
  - Simplification of `useHubConnection.ts` (remove workaround escape sequence processing)
  - New unit tests for control mode parsing

**Effect on parent objectives:** CR-081's core objective — correct terminal dimensions — is met by EI-1 through EI-3. The control mode switch resolves the deeper scrollback problem that the dimension fix alone cannot address. The parent's objectives are expanded, not reduced.

**No scope items are lost.** EI-1 through EI-3 are complete and their changes persist. The default dimensions configured in EI-1/EI-2 continue to apply to the tmux session that control mode attaches to.

---

## 6. Proposed Resolution

Switch from `tmux attach -t agent` (viewport rendering) to `tmux -CC attach -t agent` (control mode protocol).

### How tmux control mode works

Instead of raw terminal bytes, control mode emits a line-based protocol:

```
%output %0 \033[1mBold text\033[0m\015\012
%output %0 More output here\015\012
%begin TIMESTAMP FLAGS
%end TIMESTAMP FLAGS
```

- `%output %PANE_ID ESCAPED_DATA` — Claude Code's raw PTY output with octal-escaped control characters
- `%begin/%end` — Command response wrappers
- Input sent via `send-keys -t agent -H XX XX ...` (hex-encoded bytes)
- Resize sent via `refresh-client -C WxH`

### Changes required

**`agent-hub/agent_hub/pty_manager.py` (major rewrite):**
- `attach()`: Execute `sh -c "stty raw -echo && exec tmux -CC attach -t agent"` instead of `tmux attach -t agent`
- `_read_loop()`: Line-based parser that extracts `%output` payloads and decodes octal escapes
- `write()`: Convert input bytes to `send-keys -t agent -H XX XX...` format
- `resize()`: Send `refresh-client -C {cols}x{rows}` instead of using Docker exec_resize API
- New methods: `_decode_octal()`, `_decode_control_output()`

**`agent-hub/gui/src/hooks/useHubConnection.ts` (simplification):**
- Remove `EXTEND_SCROLL_REGION_RE` and scroll region extension logic
- Remove `SCROLL_UP_RE` and SU-to-newlines conversion
- Remove `scrollback` parameter from `stripTerminalModes()`
- Remove `resizePending` Map and post-resize scrollback suppression
- Remove DA response filtering in `sendInput()`
- Keep `STRIP_MODES_RE` (mouse tracking) and `STRIP_CLEAR_SCROLLBACK_RE` (ESC[3J)

**`agent-hub/tests/test_control_mode.py` (new):**
- Unit tests for octal decoding, control output parsing, and hex encoding

---

## 7. Resolution Work

<!--
NOTE: Do NOT delete this comment block. It provides guidance for execution.

If the resolution work encounters issues, create a nested VAR.
-->

### Resolution: CR-081

| EI | Task Description | Execution Summary | Task Outcome | Performed By - Date |
|----|------------------|-------------------|--------------|---------------------|
| EI-1 | Rewrite `pty_manager.py` for tmux control mode (attach, read loop, write, resize, octal decoder) | Rewrote `pty_manager.py`. `attach()` now executes `sh -c "stty raw -echo && exec tmux -CC attach -t agent"`. `_read_loop()` replaced with line-based parser that accumulates bytes into a line buffer, splits on `\n`, and extracts `%output` payloads. Added module-level `_decode_octal()` (octal escape to raw bytes), `_decode_control_output()` (%output line parser), and `_encode_send_keys()` (bytes to hex). `write()` converts input to `send-keys -t agent -H XX...` format. `resize()` sends `refresh-client -C {cols}x{rows}`. Removed `_exec_id` field (no longer needed). Non-%output control messages logged at debug level. PTYManager public API unchanged. | Pass | claude - 2026-02-15 |
| EI-2 | Simplify `useHubConnection.ts` — remove workaround escape processing, keep mouse tracking and clear-scrollback stripping | Removed `EXTEND_SCROLL_REGION_RE`, `SCROLL_UP_RE`, `scrollback` parameter on `stripTerminalModes()`, `resizePending` Map and its timeout logic in `sendResize()`/`dispatch()`, and DA response filtering in `sendInput()`. Kept `STRIP_MODES_RE` (mouse tracking) and `STRIP_CLEAR_SCROLLBACK_RE` (ESC[3J/ESC c). `stripTerminalModes()` now takes only `data: Uint8Array` with no conditional logic. `dispatch()` subscribed/output handlers both call `stripTerminalModes()` uniformly. `sendResize()` sends resize message directly with no timer. File reduced from 297 to 236 lines. | Pass | claude - 2026-02-15 |
| EI-3 | Create unit tests for control mode parsing (`test_control_mode.py`) | Created `agent-hub/tests/test_control_mode.py` with 30 unit tests across 3 test classes: `TestDecodeOctal` (12 tests: printable passthrough, empty, ESC, CR/LF, backslash literal, tab, mixed content, consecutive escapes, trailing backslash, non-octal after backslash, null byte, max byte), `TestDecodeControlOutput` (11 tests: simple output, escaped output, %begin/%end/%session-changed/%exit return None, empty line, no payload, different pane, random text, non-output %), `TestEncodeSendKeys` (7 tests: simple text, single byte, enter, ESC, arrow key, ctrl+c, empty). All 30 tests pass. Existing 10 websocket UAT tests also pass (no regressions). | Pass | claude - 2026-02-15 |
| EI-4 | Manual verification: launch agent, verify scrollback works, verify input works, verify resize works | [EXECUTION_SUMMARY] | [Pass/Fail] | [PERFORMER] - [DATE] |

---

### Resolution Comments

| Comment | Performed By - Date |
|---------|---------------------|
| EI-1 through EI-3 complete. All code changes implemented and unit tested (30/30 pass, 10/10 existing UAT pass). EI-4 (manual verification) requires running Docker containers and GUI — deferred to Lead. | claude - 2026-02-15 |

<!--
NOTE: Do NOT delete this comment. It provides guidance during document execution.

Record observations, decisions, or issues encountered during resolution.
Add rows as needed.

This section is the appropriate place to attach nested VARs that do not
apply to any individual resolution item, but apply to the resolution as a whole.
-->

---

## 8. VAR Closure

| Details of Resolution | Outcome | Performed By - Date |
|-----------------------|---------|---------------------|
| [RESOLUTION_DETAILS] | [OUTCOME] | [PERFORMER] - [DATE] |

---

## 9. References

- **SOP-004:** Document Execution
- **CR-081:** Fix tmux default terminal dimensions (parent)
- **CR-080:** Terminal Scrollback Support in Agent GUI (original scrollback CR, CLOSED)
- **SOP-002:** Change Control

---

**END OF VARIANCE REPORT**
