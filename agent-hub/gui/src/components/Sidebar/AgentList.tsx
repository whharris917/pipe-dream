import { useAgentStore } from "../../hooks/useAgentStore";
import { AGENT_ORDER } from "../../constants";
import AgentItem from "./AgentItem";

export default function AgentList() {
  const agents = useAgentStore((s) => s.agents);

  // Display agents in canonical order
  const sorted = AGENT_ORDER.map((id) => agents[id]).filter(Boolean);

  return (
    <div className="sidebar-section">
      <div className="sidebar-section-title">Agents</div>
      {sorted.map((agent) => (
        <AgentItem key={agent.id} agent={agent} />
      ))}
      {sorted.length === 0 && (
        <div className="placeholder">No agents loaded</div>
      )}
    </div>
  );
}
