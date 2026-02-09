import { useState, useCallback } from "react";
import { AGENT_DISPLAY_NAMES } from "../../constants";
import { useAgentStore } from "../../hooks/useAgentStore";
import { startAgent, stopAgent } from "../../hub-api";
import type { Agent } from "../../types";

interface Props {
  agent: Agent;
}

interface MenuPos {
  x: number;
  y: number;
}

export default function AgentItem({ agent }: Props) {
  const activeTab = useAgentStore((s) => s.activeTab);
  const openTab = useAgentStore((s) => s.openTab);
  const [menu, setMenu] = useState<MenuPos | null>(null);

  const isActive = activeTab === agent.id;
  const displayName = AGENT_DISPLAY_NAMES[agent.id] ?? agent.id;

  const handleClick = useCallback(() => {
    if (agent.state === "starting" || agent.state === "stopping") return;
    if (agent.state === "stopped") {
      // Start the agent — tab will open when state changes to running
      startAgent(agent.id).catch((err) =>
        console.error("Failed to start agent:", err),
      );
    } else {
      openTab(agent.id);
    }
  }, [agent.id, agent.state, openTab]);

  const handleContextMenu = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      setMenu({ x: e.clientX, y: e.clientY });
    },
    [],
  );

  const handleStart = useCallback(() => {
    setMenu(null);
    startAgent(agent.id).catch((err) =>
      console.error("Failed to start agent:", err),
    );
  }, [agent.id]);

  const handleStop = useCallback(() => {
    setMenu(null);
    stopAgent(agent.id).catch((err) =>
      console.error("Failed to stop agent:", err),
    );
  }, [agent.id]);

  return (
    <>
      <div
        className={`agent-item${isActive ? " active" : ""}`}
        onClick={handleClick}
        onContextMenu={handleContextMenu}
      >
        <div className={`agent-state-dot ${agent.state}`} />
        <span className="agent-name">{displayName}</span>
        {agent.inbox_count > 0 && (
          <span className="agent-inbox-badge">{agent.inbox_count}</span>
        )}
      </div>

      {menu && (
        <>
          <div
            className="context-menu-backdrop"
            onClick={() => setMenu(null)}
          />
          <div
            className="context-menu"
            style={{ left: menu.x, top: menu.y }}
          >
            {agent.state === "stopped" ? (
              <div className="context-menu-item" onClick={handleStart}>
                Start
              </div>
            ) : agent.state === "running" ? (
              <div className="context-menu-item" onClick={handleStop}>
                Stop
              </div>
            ) : (
              <div className="context-menu-item disabled">
                {agent.state === "starting" ? "Starting..." : "Stopping..."}
              </div>
            )}
          </div>
        </>
      )}
    </>
  );
}
