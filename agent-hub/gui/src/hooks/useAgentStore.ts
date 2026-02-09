import { create } from "zustand";
import type { Agent, AgentState, ConnectionStatus } from "../types";

interface AgentStore {
  /** Agent states keyed by agent ID */
  agents: Record<string, Agent>;

  /** WebSocket connection status */
  connectionStatus: ConnectionStatus;

  /** Open terminal tab agent IDs (in tab order) */
  openTabs: string[];

  /** Currently visible tab agent ID */
  activeTab: string | null;

  /** Hub uptime in seconds */
  hubUptimeSeconds: number;

  // --- Actions ---

  /** Replace all agents (from initial REST load) */
  setAgents(agents: Agent[]): void;

  /** Update a single agent's state from WebSocket event */
  updateAgentState(agentId: string, state: AgentState, agent: Agent): void;

  /** Update inbox count from WebSocket event */
  updateInboxCount(agentId: string, count: number): void;

  /** Set WebSocket connection status */
  setConnectionStatus(status: ConnectionStatus): void;

  /** Set hub uptime */
  setHubUptime(seconds: number): void;

  /** Open a new tab for an agent (no-op if already open) */
  openTab(agentId: string): void;

  /** Close a tab */
  closeTab(agentId: string): void;

  /** Switch to a tab */
  setActiveTab(agentId: string): void;
}

export const useAgentStore = create<AgentStore>((set, get) => ({
  agents: {},
  connectionStatus: "disconnected",
  openTabs: [],
  activeTab: null,
  hubUptimeSeconds: 0,

  setAgents(agents) {
    const map: Record<string, Agent> = {};
    for (const a of agents) {
      map[a.id] = a;
    }
    set({ agents: map });
  },

  updateAgentState(agentId, _state, agent) {
    set((s) => ({
      agents: { ...s.agents, [agentId]: agent },
    }));
  },

  updateInboxCount(agentId, count) {
    set((s) => {
      const existing = s.agents[agentId];
      if (!existing) return s;
      return {
        agents: { ...s.agents, [agentId]: { ...existing, inbox_count: count } },
      };
    });
  },

  setConnectionStatus(status) {
    set({ connectionStatus: status });
  },

  setHubUptime(seconds) {
    set({ hubUptimeSeconds: seconds });
  },

  openTab(agentId) {
    const { openTabs } = get();
    if (openTabs.includes(agentId)) {
      set({ activeTab: agentId });
      return;
    }
    set({
      openTabs: [...openTabs, agentId],
      activeTab: agentId,
    });
  },

  closeTab(agentId) {
    set((s) => {
      const openTabs = s.openTabs.filter((id) => id !== agentId);
      let activeTab = s.activeTab;
      if (activeTab === agentId) {
        // Switch to adjacent tab or null
        const oldIndex = s.openTabs.indexOf(agentId);
        activeTab = openTabs[Math.min(oldIndex, openTabs.length - 1)] ?? null;
      }
      return { openTabs, activeTab };
    });
  },

  setActiveTab(agentId) {
    set({ activeTab: agentId });
  },
}));
