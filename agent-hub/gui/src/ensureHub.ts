import { invoke } from "@tauri-apps/api/core";
import { HUB_URL } from "./constants";
import { useAgentStore } from "./hooks/useAgentStore";

const POLL_INTERVAL_MS = 1000;
const POLL_TIMEOUT_MS = 30000;

/** Check if the Hub is reachable. */
async function isHubAlive(): Promise<boolean> {
  try {
    const res = await fetch(`${HUB_URL}/api/health`, { signal: AbortSignal.timeout(2000) });
    return res.ok;
  } catch {
    return false;
  }
}

/**
 * Ensure the Hub is running before the GUI connects.
 *
 * Fast path: Hub already up -> returns true immediately.
 * Slow path: spawns `agent-hub start` as a detached process via Tauri
 * invoke, polls /api/health with 1s interval up to 30s timeout.
 *
 * The Hub's own startup cascades to MCP servers (EI-1), so the GUI
 * only needs to ensure the Hub layer.
 */
export async function ensureHub(): Promise<boolean> {
  if (await isHubAlive()) return true;

  useAgentStore.getState().setConnectionStatus("bootstrapping");

  try {
    await invoke("spawn_hub");
  } catch (err) {
    console.warn("[ensureHub] Failed to spawn agent-hub start:", err);
    return false;
  }

  const deadline = Date.now() + POLL_TIMEOUT_MS;
  while (Date.now() < deadline) {
    await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
    if (await isHubAlive()) return true;
  }

  console.warn("[ensureHub] Timed out waiting for Hub");
  return false;
}
