/** Agent state machine — mirrors agent_hub/models.py AgentState enum */
export type AgentState = "stopped" | "starting" | "running" | "stopping" | "error";

export type LaunchPolicy = "manual" | "auto_on_task" | "always_on";
export type ShutdownPolicy = "manual" | "on_inbox_empty" | "idle_timeout";

export interface AgentPolicy {
  launch: LaunchPolicy;
  shutdown: ShutdownPolicy;
  idle_timeout_minutes: number;
}

export interface Agent {
  id: string;
  state: AgentState;
  policy: AgentPolicy;
  container_id: string | null;
  started_at: string | null;
  last_activity: string | null;
  inbox_count: number;
  pty_attached: boolean;
}

export interface AgentSummary {
  id: string;
  state: AgentState;
  inbox_count: number;
  launch_policy: LaunchPolicy;
}

export interface HubStatus {
  agents: AgentSummary[];
  uptime_seconds: number;
}

/** WebSocket messages: Server -> Client */
export type ServerMessage =
  | { type: "subscribed"; agent_id: string; buffer: string }
  | { type: "unsubscribed"; agent_id: string }
  | { type: "output"; agent_id: string; data: string }
  | { type: "agent_state_changed"; agent_id: string; state: AgentState; agent: Agent }
  | { type: "inbox_changed"; agent_id: string; count: number }
  | { type: "error"; message: string };

/** WebSocket messages: Client -> Server */
export type ClientMessage =
  | { type: "subscribe"; agent_id: string }
  | { type: "unsubscribe"; agent_id: string }
  | { type: "input"; agent_id: string; data: string }
  | { type: "resize"; agent_id: string; cols: number; rows: number };

export type ConnectionStatus = "connecting" | "connected" | "disconnected" | "error";
