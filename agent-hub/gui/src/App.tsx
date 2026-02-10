import { useEffect, useCallback, useRef } from "react";
import "./styles/global.css";
import { hubConnection } from "./hooks/useHubConnection";
import { useAgentStore } from "./hooks/useAgentStore";
import { fetchAgents, fetchHubStatus } from "./hub-api";
import { ensureHub } from "./ensureHub";
import Sidebar from "./components/Sidebar/Sidebar";
import TerminalPanel from "./components/Terminal/TerminalPanel";
import StatusBar from "./components/StatusBar";

function App() {
  const bootstrapRef = useRef(false);

  useEffect(() => {
    if (bootstrapRef.current) return;
    bootstrapRef.current = true;

    ensureHub().then(() => {
      hubConnection.connect();
    });

    return () => {
      hubConnection.disconnect();
      bootstrapRef.current = false;
    };
  }, []);

  const setAgents = useAgentStore((s) => s.setAgents);
  const setHubUptime = useAgentStore((s) => s.setHubUptime);
  const connectionStatus = useAgentStore((s) => s.connectionStatus);
  const openTab = useAgentStore((s) => s.openTab);
  const openTabs = useAgentStore((s) => s.openTabs);

  // Load initial agent list and uptime when connected
  useEffect(() => {
    if (connectionStatus !== "connected") return;

    fetchAgents()
      .then(setAgents)
      .catch((err) => console.error("Failed to fetch agents:", err));

    fetchHubStatus()
      .then((status) => setHubUptime(status.uptime_seconds))
      .catch((err) => console.error("Failed to fetch hub status:", err));
  }, [connectionStatus, setAgents, setHubUptime]);

  // Auto-open tabs for running agents when state changes
  const agents = useAgentStore((s) => s.agents);
  useEffect(() => {
    // When an agent transitions to "running" and doesn't have a tab, open one
    // This handles the case where user clicks a stopped agent in sidebar
    for (const agent of Object.values(agents)) {
      if (agent.state === "running" && !openTabs.includes(agent.id)) {
        // Only auto-open if the agent was recently started (started_at within last 5s)
        if (agent.started_at) {
          const startedAt = new Date(agent.started_at).getTime();
          const now = Date.now();
          if (now - startedAt < 5000) {
            openTab(agent.id);
          }
        }
      }
    }
  }, [agents, openTabs, openTab]);

  // Keyboard shortcuts: Ctrl+Tab / Ctrl+Shift+Tab for tab cycling
  const setActiveTab = useAgentStore((s) => s.setActiveTab);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === "Tab") {
        e.preventDefault();
        const tabs = useAgentStore.getState().openTabs;
        const current = useAgentStore.getState().activeTab;
        if (tabs.length < 2 || !current) return;

        const idx = tabs.indexOf(current);
        const next = e.shiftKey
          ? (idx - 1 + tabs.length) % tabs.length
          : (idx + 1) % tabs.length;
        setActiveTab(tabs[next]);
      }
    },
    [setActiveTab],
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  // Periodic uptime refresh
  useEffect(() => {
    if (connectionStatus !== "connected") return;
    const interval = setInterval(() => {
      fetchHubStatus()
        .then((status) => setHubUptime(status.uptime_seconds))
        .catch(() => {});
    }, 30000);
    return () => clearInterval(interval);
  }, [connectionStatus, setHubUptime]);

  return (
    <div className="app">
      <div className="main-layout">
        <Sidebar />
        <TerminalPanel />
      </div>
      <StatusBar />
    </div>
  );
}

export default App;
