export const HUB_URL = "http://localhost:9000";
export const HUB_WS_URL = "ws://localhost:9000/ws";

export const AGENT_DISPLAY_NAMES: Record<string, string> = {
  claude: "Claude",
  qa: "QA",
  tu_ui: "TU-UI",
  tu_scene: "TU-Scene",
  tu_sketch: "TU-Sketch",
  tu_sim: "TU-Sim",
  bu: "BU",
};

/** Agent display order in sidebar */
export const AGENT_ORDER = [
  "claude",
  "qa",
  "tu_ui",
  "tu_scene",
  "tu_sketch",
  "tu_sim",
  "bu",
];

/** WebSocket reconnection config */
export const RECONNECT_BASE_MS = 1000;
export const RECONNECT_MAX_MS = 30000;
