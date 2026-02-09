import { useAgentStore } from "../hooks/useAgentStore";

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${Math.floor(seconds)}s`;
  const mins = Math.floor(seconds / 60);
  if (mins < 60) return `${mins}m`;
  const hrs = Math.floor(mins / 60);
  const remainMins = mins % 60;
  return `${hrs}h ${remainMins}m`;
}

export default function StatusBar() {
  const connectionStatus = useAgentStore((s) => s.connectionStatus);
  const uptime = useAgentStore((s) => s.hubUptimeSeconds);

  const label =
    connectionStatus === "connected"
      ? "Connected"
      : connectionStatus === "connecting"
        ? "Connecting..."
        : connectionStatus === "error"
          ? "Connection error"
          : "Disconnected";

  return (
    <div className="status-bar">
      <div className="status-item">
        <div className={`status-dot ${connectionStatus}`} />
        <span>{label}</span>
      </div>
      {connectionStatus === "connected" && uptime > 0 && (
        <span>Hub uptime: {formatUptime(uptime)}</span>
      )}
    </div>
  );
}
