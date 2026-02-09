import { HUB_URL } from "./constants";
import type { Agent, AgentPolicy, HubStatus } from "./types";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${HUB_URL}${path}`, init);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Hub API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export function fetchHubStatus(): Promise<HubStatus> {
  return fetchJson("/api/status");
}

export function fetchAgents(): Promise<Agent[]> {
  return fetchJson("/api/agents");
}

export function fetchAgent(agentId: string): Promise<Agent> {
  return fetchJson(`/api/agents/${agentId}`);
}

export function startAgent(agentId: string): Promise<Agent> {
  return fetchJson(`/api/agents/${agentId}/start`, { method: "POST" });
}

export function stopAgent(agentId: string): Promise<Agent> {
  return fetchJson(`/api/agents/${agentId}/stop`, { method: "POST" });
}

export function fetchPolicy(agentId: string): Promise<AgentPolicy> {
  return fetchJson(`/api/agents/${agentId}/policy`);
}

export function setPolicy(agentId: string, policy: Partial<AgentPolicy>): Promise<AgentPolicy> {
  return fetchJson(`/api/agents/${agentId}/policy`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(policy),
  });
}
