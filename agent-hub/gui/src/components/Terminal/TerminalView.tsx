import { useEffect, useRef } from "react";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { WebLinksAddon } from "@xterm/addon-web-links";
import { hubConnection } from "../../hooks/useHubConnection";
import { useAgentStore } from "../../hooks/useAgentStore";
import "@xterm/xterm/css/xterm.css";

interface Props {
  agentId: string;
  visible: boolean;
}

export default function TerminalView({ agentId, visible }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const terminalRef = useRef<Terminal | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const initializedRef = useRef(false);
  const agent = useAgentStore((s) => s.agents[agentId]);
  const connectionStatus = useAgentStore((s) => s.connectionStatus);

  // Create terminal and subscribe on mount
  useEffect(() => {
    if (initializedRef.current || !containerRef.current) return;
    initializedRef.current = true;

    const terminal = new Terminal({
      cursorBlink: true,
      cursorStyle: "block",
      fontSize: 14,
      fontFamily: "'JetBrains Mono', 'Cascadia Code', 'Fira Code', 'Consolas', monospace",
      theme: {
        background: "#1e1e2e",
        foreground: "#cdd6f4",
        cursor: "#f5e0dc",
        selectionBackground: "#45475a",
        black: "#45475a",
        red: "#f38ba8",
        green: "#a6e3a1",
        yellow: "#f9e2af",
        blue: "#89b4fa",
        magenta: "#f5c2e7",
        cyan: "#94e2d5",
        white: "#bac2de",
        brightBlack: "#585b70",
        brightRed: "#f38ba8",
        brightGreen: "#a6e3a1",
        brightYellow: "#f9e2af",
        brightBlue: "#89b4fa",
        brightMagenta: "#f5c2e7",
        brightCyan: "#94e2d5",
        brightWhite: "#a6adc8",
      },
      scrollback: 10000,
      convertEol: true,
    });

    const fitAddon = new FitAddon();
    const webLinksAddon = new WebLinksAddon();

    terminal.loadAddon(fitAddon);
    terminal.loadAddon(webLinksAddon);
    terminal.open(containerRef.current);

    // Fit after a frame to let the DOM settle
    requestAnimationFrame(() => {
      fitAddon.fit();
    });

    terminalRef.current = terminal;
    fitAddonRef.current = fitAddon;

    // Register with hub connection for receiving output
    hubConnection.registerTerminal(agentId, terminal);

    // Subscribe to agent PTY stream
    hubConnection.subscribe(agentId);

    // Wire input: keystrokes → WebSocket
    const dataDisposable = terminal.onData((data) => {
      hubConnection.sendInput(agentId, data);
    });

    // Wire resize: terminal resize → WebSocket
    const resizeDisposable = terminal.onResize(({ cols, rows }) => {
      hubConnection.sendResize(agentId, cols, rows);
    });

    // ResizeObserver for container size changes
    const observer = new ResizeObserver(() => {
      fitAddon.fit();
    });
    observer.observe(containerRef.current);

    // DEBUG: Log xterm.js buffer state every 5 seconds
    const debugInterval = setInterval(() => {
      const buf = terminal.buffer.active;
      console.log(
        `[scroll-debug] buffer: length=${buf.length} baseY=${buf.baseY} ` +
        `cursorY=${buf.cursorY} viewportRows=${terminal.rows} ` +
        `scrollback=${buf.baseY} type=${buf.type}`
      );
    }, 5000);

    return () => {
      clearInterval(debugInterval);
      observer.disconnect();
      dataDisposable.dispose();
      resizeDisposable.dispose();
      hubConnection.unregisterTerminal(agentId);
      hubConnection.unsubscribe(agentId);
      terminal.dispose();
      terminalRef.current = null;
      fitAddonRef.current = null;
      initializedRef.current = false;
    };
  }, [agentId]);

  // Re-fit when visibility changes (tab switch)
  useEffect(() => {
    if (visible && fitAddonRef.current) {
      requestAnimationFrame(() => {
        fitAddonRef.current?.fit();
      });
    }
  }, [visible]);

  const isStopped = agent?.state === "stopped" || agent?.state === "error";
  const isDisconnected = connectionStatus !== "connected";

  return (
    <div className={`terminal-container${visible ? "" : " hidden"}`}>
      <div ref={containerRef} style={{ width: "100%", height: "100%" }} />

      {isStopped && !isDisconnected && (
        <div className="terminal-overlay">Agent stopped</div>
      )}

      {isDisconnected && (
        <div className="disconnected-overlay">
          <div className="status-dot" />
          <span style={{ color: "var(--text-muted)" }}>Disconnected from Hub</span>
        </div>
      )}
    </div>
  );
}
