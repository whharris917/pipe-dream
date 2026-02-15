import { useEffect, useRef, useCallback } from "react";
import { HUB_WS_URL, RECONNECT_BASE_MS, RECONNECT_MAX_MS } from "../constants";
import { useAgentStore } from "./useAgentStore";
import type { Terminal } from "@xterm/xterm";
import type { ServerMessage, ClientMessage } from "../types";

/**
 * Decodes a base64 string to a Uint8Array.
 * Used for PTY output — xterm.js handles ANSI from raw bytes.
 */
function base64ToBytes(base64: string): Uint8Array {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

/**
 * Strip escape sequences that prevent terminal scrollback from working
 * in the monitoring GUI.
 *
 * 1. Mouse tracking modes (1000, 1002, 1003, 1005, 1006, 1015):
 *    Claude Code enables mouse tracking, which causes xterm.js to forward
 *    wheel events to the application instead of scrolling the buffer.
 *
 * 2. Alternate screen modes (47, 1047, 1049):
 *    Defensive — Claude Code doesn't use alt screen, but tmux might.
 *    Alt screen has zero scrollback in xterm.js.
 *
 * 3. Clear scrollback (ESC[3J) and full reset (ESC c):
 *    Claude Code clears the scrollback buffer on every render cycle as
 *    part of its differential rendering system. ESC c (RIS) also clears
 *    scrollback along with all terminal state.
 */
const STRIP_MODES_RE =
  /\x1b\[\?(?:\d+;)*(1000|1002|1003|1005|1006|1015|47|1047|1049)(?:;\d+)*[hl]/g;
const STRIP_CLEAR_SCROLLBACK_RE = /\x1b\[3J|\x1bc/g;

/**
 * DEBUG: Log escape sequences that might affect scrollback.
 * Looks for any CSI J (erase display) variants and other clearing sequences.
 * Remove this once scrollback investigation is complete.
 */
function debugLogEscapeSequences(str: string): void {
  // Match all CSI ... J sequences (erase in display variants)
  const edMatches = str.match(/\x1b\[\d*J/g);
  if (edMatches) {
    const unique = [...new Set(edMatches)];
    for (const seq of unique) {
      const code = seq.replace("\x1b", "ESC");
      console.log(`[scroll-debug] Erase display sequence: ${code}`);
    }
  }
  // Match full reset
  if (/\x1bc/.test(str)) {
    console.log("[scroll-debug] Full reset (ESC c) detected");
  }
  // Match any CSI ? ... h/l we're NOT already stripping
  const modeMatches = str.match(/\x1b\[\?\d+[hl]/g);
  if (modeMatches) {
    const unique = [...new Set(modeMatches)];
    for (const seq of unique) {
      const code = seq.replace("\x1b", "ESC");
      console.log(`[scroll-debug] Mode set/reset: ${code}`);
    }
  }
}

function stripTerminalModes(data: Uint8Array): Uint8Array {
  const str = new TextDecoder().decode(data);
  debugLogEscapeSequences(str);
  const filtered = str.replace(STRIP_MODES_RE, "").replace(STRIP_CLEAR_SCROLLBACK_RE, "");
  if (filtered.length === str.length) return data;
  return new TextEncoder().encode(filtered);
}

/**
 * Singleton WebSocket connection manager.
 * Lives outside React lifecycle — Zustand store dispatches are called directly.
 */
class HubConnection {
  private ws: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectDelay = RECONNECT_BASE_MS;
  private terminals = new Map<string, Terminal>();
  private muteInput = new Set<string>();
  private intentionalClose = false;
  private _debugThrottle = false;

  connect() {
    this.intentionalClose = false;
    useAgentStore.getState().setConnectionStatus("connecting");

    try {
      this.ws = new WebSocket(HUB_WS_URL);
    } catch {
      useAgentStore.getState().setConnectionStatus("error");
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      useAgentStore.getState().setConnectionStatus("connected");
      this.reconnectDelay = RECONNECT_BASE_MS;
      // Re-subscribe to all open tabs after reconnect
      const { openTabs } = useAgentStore.getState();
      for (const agentId of openTabs) {
        this.send({ type: "subscribe", agent_id: agentId });
      }
    };

    this.ws.onclose = () => {
      if (!this.intentionalClose) {
        useAgentStore.getState().setConnectionStatus("disconnected");
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = () => {
      useAgentStore.getState().setConnectionStatus("error");
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const msg = JSON.parse(event.data as string) as ServerMessage;
        this.dispatch(msg);
      } catch {
        // Ignore malformed messages
      }
    };
  }

  disconnect() {
    this.intentionalClose = true;
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    useAgentStore.getState().setConnectionStatus("disconnected");
  }

  private scheduleReconnect() {
    if (this.reconnectTimer !== null) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, RECONNECT_MAX_MS);
      this.connect();
    }, this.reconnectDelay);
  }

  private dispatch(msg: ServerMessage) {
    const store = useAgentStore.getState();

    switch (msg.type) {
      case "subscribed": {
        const term = this.terminals.get(msg.agent_id);
        if (term && msg.buffer) {
          this.muteInput.add(msg.agent_id);
          term.write(stripTerminalModes(base64ToBytes(msg.buffer)), () => {
            this.muteInput.delete(msg.agent_id);
          });
        }
        break;
      }
      case "output": {
        const term = this.terminals.get(msg.agent_id);
        if (term) {
          const raw = base64ToBytes(msg.data);
          // DEBUG: Sample ongoing output to understand what tmux sends
          const sample = new TextDecoder().decode(raw);
          const csiMatches = sample.match(/\x1b\[[^a-zA-Z]*[a-zA-Z]/g);
          if (csiMatches && !this._debugThrottle) {
            this._debugThrottle = true;
            const unique = [...new Set(csiMatches)].map(s => s.replace("\x1b", "ESC"));
            console.log(`[scroll-debug] output chunk: ${raw.length} bytes, CSI sequences:`, unique.slice(0, 20));
            setTimeout(() => { this._debugThrottle = false; }, 3000);
          }
          term.write(stripTerminalModes(raw));
        }
        break;
      }
      case "agent_state_changed":
        store.updateAgentState(msg.agent_id, msg.state, msg.agent);
        break;
      case "inbox_changed":
        store.updateInboxCount(msg.agent_id, msg.count);
        break;
      case "error":
        console.warn("[Hub WS] Error:", msg.message);
        break;
      case "unsubscribed":
        // No action needed — terminal cleanup handled by tab close
        break;
    }
  }

  send(msg: ClientMessage) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    }
  }

  subscribe(agentId: string) {
    this.send({ type: "subscribe", agent_id: agentId });
  }

  unsubscribe(agentId: string) {
    this.send({ type: "unsubscribe", agent_id: agentId });
  }

  sendInput(agentId: string, data: string) {
    if (this.muteInput.has(agentId)) return;
    // Filter DA (Device Attributes) responses generated by xterm.js when
    // processing scrollback buffers containing DA requests from tmux/bash.
    // Primary DA: ESC[?...c  Secondary DA: ESC[>...c
    // Also filter without ESC prefix in case xterm splits the sequence.
    if (/\x1b\[[\?>][\d;]*c/.test(data) || /^\[[\?>][\d;]*c$/.test(data)) return;
    this.send({ type: "input", agent_id: agentId, data });
  }

  sendResize(agentId: string, cols: number, rows: number) {
    this.send({ type: "resize", agent_id: agentId, cols, rows });
  }

  /** Register a terminal instance for receiving output */
  registerTerminal(agentId: string, terminal: Terminal) {
    this.terminals.set(agentId, terminal);
  }

  /** Unregister a terminal instance */
  unregisterTerminal(agentId: string) {
    this.terminals.delete(agentId);
  }
}

/** Singleton instance */
export const hubConnection = new HubConnection();

/**
 * React hook that manages the WebSocket connection lifecycle.
 * Call once in the root App component.
 */
export function useHubConnection() {
  const connectionRef = useRef(false);

  useEffect(() => {
    if (!connectionRef.current) {
      connectionRef.current = true;
      hubConnection.connect();
    }
    return () => {
      hubConnection.disconnect();
      connectionRef.current = false;
    };
  }, []);

  const subscribe = useCallback((agentId: string) => {
    hubConnection.subscribe(agentId);
  }, []);

  const unsubscribe = useCallback((agentId: string) => {
    hubConnection.unsubscribe(agentId);
  }, []);

  const sendInput = useCallback((agentId: string, data: string) => {
    hubConnection.sendInput(agentId, data);
  }, []);

  const sendResize = useCallback((agentId: string, cols: number, rows: number) => {
    hubConnection.sendResize(agentId, cols, rows);
  }, []);

  return { subscribe, unsubscribe, sendInput, sendResize };
}
