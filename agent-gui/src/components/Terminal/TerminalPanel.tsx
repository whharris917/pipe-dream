import { useAgentStore } from "../../hooks/useAgentStore";
import TabBar from "./TabBar";
import TerminalView from "./TerminalView";

export default function TerminalPanel() {
  const openTabs = useAgentStore((s) => s.openTabs);
  const activeTab = useAgentStore((s) => s.activeTab);

  return (
    <div className="terminal-panel">
      <TabBar />
      <div className="terminal-area">
        {openTabs.length === 0 ? (
          <div className="empty-state">
            Select an agent from the sidebar to open a terminal
          </div>
        ) : (
          openTabs.map((agentId) => (
            <TerminalView
              key={agentId}
              agentId={agentId}
              visible={agentId === activeTab}
            />
          ))
        )}
      </div>
    </div>
  );
}
