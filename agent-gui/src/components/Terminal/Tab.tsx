import { useCallback } from "react";
import { AGENT_DISPLAY_NAMES } from "../../constants";
import { useAgentStore } from "../../hooks/useAgentStore";

interface Props {
  agentId: string;
}

export default function Tab({ agentId }: Props) {
  const activeTab = useAgentStore((s) => s.activeTab);
  const agents = useAgentStore((s) => s.agents);
  const setActiveTab = useAgentStore((s) => s.setActiveTab);
  const closeTab = useAgentStore((s) => s.closeTab);

  const isActive = activeTab === agentId;
  const agent = agents[agentId];
  const state = agent?.state ?? "stopped";
  const displayName = AGENT_DISPLAY_NAMES[agentId] ?? agentId;

  const handleClick = useCallback(() => {
    setActiveTab(agentId);
  }, [agentId, setActiveTab]);

  const handleClose = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      closeTab(agentId);
    },
    [agentId, closeTab],
  );

  return (
    <div
      className={`tab${isActive ? " active" : ""}`}
      onClick={handleClick}
    >
      <div className={`tab-dot ${state}`} />
      <span>{displayName}</span>
      <button className="tab-close" onClick={handleClose}>
        &times;
      </button>
    </div>
  );
}
