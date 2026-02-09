import { useAgentStore } from "../../hooks/useAgentStore";
import Tab from "./Tab";

export default function TabBar() {
  const openTabs = useAgentStore((s) => s.openTabs);

  if (openTabs.length === 0) return null;

  return (
    <div className="tab-bar">
      {openTabs.map((agentId) => (
        <Tab key={agentId} agentId={agentId} />
      ))}
    </div>
  );
}
