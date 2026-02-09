import AgentList from "./AgentList";
import McpHealth from "./McpHealth";
import QmsStatus from "./QmsStatus";

export default function Sidebar() {
  return (
    <div className="sidebar">
      <AgentList />
      <McpHealth />
      <QmsStatus />
    </div>
  );
}
