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
 * Singleton WebSocket connection manager.
 * Lives outside React lifecycle — Zustand store dispatches are called directly.
 */
class HubConnection {
  private ws: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectDelay = RECONNECT_BASE_MS;
  private terminals = new Map<string, Terminal>();
  private intentionalClose = false;

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
          term.write(base64ToBytes(msg.buffer));
        }
        break;
      }
      case "output": {
        const term = this.terminals.get(msg.agent_id);
        if (term) {
          term.write(base64ToBytes(msg.data));
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
