# Container Architecture Primer for Pipe Dream

## Chapter 1: What is a Docker Container?

### 1.1 The Problem Containers Solve

Imagine you want to run a program that requires Python 3.11, specific libraries, and particular system tools. On your Windows machine, you might have Python 3.9 and different libraries. Installing everything could break your existing setup.

A **container** is like a lightweight, isolated computer running inside your computer. It has its own:
- Filesystem (directories, files)
- Installed programs
- Environment variables
- Network identity

But unlike a full virtual machine, containers share your computer's core (the kernel), making them fast and lightweight.

### 1.2 Key Container Concepts

**Image**: A snapshot/template of a container's filesystem. Think of it like a "frozen" computer state. Our image is called `docker-claude-agent` and contains Linux, Python, Node.js, Claude Code CLI, and our tools.

**Container**: A running instance of an image. You can run multiple containers from the same image. Each container is isolated from others.

**Container Name**: Each running container has a unique name. Examples: `agent-claude`, `agent-qa`, `docker-claude-agent-1`.

### 1.3 Container Lifecycle

```
Image (frozen template)
    │
    ▼ "docker run" creates a container from the image
Container (running instance)
    │
    ▼ Container runs until the main process exits
Stopped Container (can be restarted or removed)
    │
    ▼ "docker rm" deletes it
Gone
```

**Critical Point**: When a container is removed, everything inside it is deleted UNLESS you explicitly save it somewhere (like a mounted volume - explained next).

---

## Chapter 2: Volumes and Mounts - Connecting Host and Container

### 2.1 The Isolation Problem

By default, a container cannot see your files, and you cannot see the container's files. They're completely separate filesystems.

```
┌─────────────────────┐     ┌─────────────────────┐
│   Your Computer     │     │     Container       │
│   (Host)            │     │                     │
│                     │     │                     │
│ C:\Users\wilha\     │  ✗  │ /home/             │
│ projects\pipe-dream │ ──► │ (cannot see host)  │
│                     │     │                     │
└─────────────────────┘     └─────────────────────┘
```

### 2.2 Volume Mounts: Creating Windows Between Worlds

A **volume mount** creates a "window" between the host and container. A directory on your computer appears inside the container.

```
┌─────────────────────┐     ┌─────────────────────┐
│   Your Computer     │     │     Container       │
│                     │     │                     │
│ C:\Users\wilha\     │     │                     │
│ projects\pipe-dream │◄───►│ /pipe-dream        │
│                     │ mount│ (same files!)      │
│                     │     │                     │
└─────────────────────┘     └─────────────────────┘
```

The mount is specified like: `-v "C:\path\on\host:/path/in/container"`

### 2.3 Read-Only vs Read-Write Mounts

- **Read-Only (`:ro`)**: Container can see files but cannot modify them.
  Example: `-v "C:\project:/pipe-dream:ro"` - Protects your code from accidental changes.

- **Read-Write (`:rw`)**: Container can read AND write files. Changes persist on your host.
  Example: `-v "C:\config:/claude-config:rw"` - Container can save settings.

### 2.4 Our Mount Strategy

```
Host Path                                    Container Path         Mode
─────────────────────────────────────────────────────────────────────────
pipe-dream/                              →   /pipe-dream            ro (protect code)
pipe-dream/.claude/users/qa/workspace/   →   /pipe-dream/.claude/users/qa/workspace  rw
pipe-dream/.claude/users/qa/container/   →   /claude-config         rw (Claude's config)
pipe-dream/docker/.mcp.json              →   /pipe-dream/.mcp.json  ro (MCP config)
```

**Why this matters**: The `/claude-config` mount is where Claude Code stores its settings. If we mount the same host directory for two containers, they share settings. If we mount different directories, they have separate settings.

---

## Chapter 3: The Entrypoint - What Happens When a Container Starts

### 3.1 What is an Entrypoint?

When you start a container, Docker runs a specific program called the **entrypoint**. It's like the container's "startup script."

Our entrypoint (`docker/entrypoint.sh`) does this:

```
Container Starts
      │
      ▼
┌─────────────────────────────────────┐
│ 1. Wait for MCP servers to be      │
│    reachable (up to 30 seconds)    │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│ 2. Check: Does marker file exist?  │──── Yes ──► Skip configuration
│    (.mcp-configured)               │
└─────────────────────────────────────┘
      │ No
      ▼
┌─────────────────────────────────────┐
│ 3. Run "claude mcp add" to         │
│    register MCP servers            │
│ 4. Create marker file              │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│ 5. "exec claude" - Replace this    │
│    process with Claude Code        │
└─────────────────────────────────────┘
```

### 3.2 What are Marker Files?

A **marker file** is an empty file that says "I already did this task."

Location: `/claude-config/.mcp-configured` (which maps to `.claude/users/{agent}/container/.mcp-configured` on your host)

**Purpose**: The entrypoint checks if this file exists. If it does, it skips MCP configuration (assuming it was already done).

**Problem**: If you mount the same config directory across multiple container runs, the marker file persists. A new container sees "oh, MCP is already configured" and skips configuration, even though this container has never configured MCP.

### 3.3 The "exec" Command

The last line of our entrypoint is `exec claude "$@"`.

`exec` is special: it **replaces** the current process with Claude Code. The entrypoint script stops existing, and Claude Code becomes the container's main process.

When Claude Code exits (you type `exit`), the container's main process ends, so the container stops.

---

## Chapter 4: Claude Code Configuration Scopes

### 4.1 Where Does Claude Code Store Settings?

Claude Code has multiple configuration locations, checked in order:

```
Priority (highest to lowest):
─────────────────────────────────────────────────────────
1. User Config     $CLAUDE_CONFIG_DIR/.claude.json
                   (We set this to /claude-config)

2. Project Config  /pipe-dream/.claude/settings.local.json
                   /pipe-dream/.mcp.json

3. Built-in        Defaults compiled into Claude Code
```

### 4.2 MCP Server Configuration

MCP servers can be configured at two levels:

**User Scope** (`claude mcp add --scope user`):
- Stored in: `$CLAUDE_CONFIG_DIR/.claude.json`
- Persists across sessions for this user
- Our entrypoint uses this

**Project Scope** (`.mcp.json` file):
- Stored in: `/pipe-dream/.mcp.json`
- Applies to anyone working in this project
- We also mount this file

**The Conflict**: If MCP is configured at BOTH levels, Claude Code might get confused about which to use. Our architecture uses both, which may cause issues.

### 4.3 What "MCP Failed" Means

When Claude Code starts, it tries to connect to each configured MCP server:

```
Claude Code Starts
      │
      ▼
Read MCP config from .claude.json and .mcp.json
      │
      ▼
For each server (qms, git):
      │
      ▼
Try to connect to http://host.docker.internal:8000/mcp
      │
      ├── Success → Show "✓ connected"
      │
      └── Failure → Show "✗ failed"
```

"Failed" could mean:
1. Server isn't running
2. Server is unreachable (network issue)
3. Authentication rejected
4. Configuration is malformed
5. Timeout during connection

---

## Chapter 5: MCP Servers - The Bridge Between Worlds

### 5.1 What is MCP?

MCP (Model Context Protocol) lets Claude Code call functions on external servers. It's how Claude can run `qms_inbox()` or `git_exec()`.

```
┌──────────────┐                    ┌──────────────┐
│ Claude Code  │ ─── HTTP call ───► │ MCP Server   │
│ (Container)  │ ◄── Response ───── │ (Host)       │
└──────────────┘                    └──────────────┘
```

### 5.2 Our MCP Architecture

We run TWO MCP servers on your host computer:

```
Your Computer (Host)
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  ┌─────────────────┐      ┌─────────────────┐          │
│  │ QMS MCP Server  │      │ Git MCP Server  │          │
│  │ Port 8000       │      │ Port 8001       │          │
│  │                 │      │                 │          │
│  │ Reads/writes    │      │ Runs git        │          │
│  │ QMS documents   │      │ commands        │          │
│  └────────▲────────┘      └────────▲────────┘          │
│           │                        │                    │
│           │   host.docker.internal │                    │
│           │   (special hostname)   │                    │
└───────────┼────────────────────────┼────────────────────┘
            │                        │
┌───────────┼────────────────────────┼────────────────────┐
│ Container │                        │                    │
│           │                        │                    │
│  ┌────────┴────────────────────────┴────────┐          │
│  │              Claude Code                  │          │
│  │  Calls qms_inbox(), git_exec(), etc.     │          │
│  └───────────────────────────────────────────┘          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**host.docker.internal**: A special hostname that, from inside a container, points to your host computer. This is how the container reaches the MCP servers.

### 5.3 MCP Configuration Requirements

For MCP to work, Claude Code needs:

1. **Server must be running** on host (ports 8000, 8001)
2. **Network path** from container to host (`--add-host=host.docker.internal:host-gateway`)
3. **Configuration** telling Claude where servers are (via `claude mcp add` or `.mcp.json`)
4. **Authentication** (we use headers: `X-API-Key`, `Authorization`)

If ANY of these is missing or wrong, MCP fails.

---

## Chapter 6: Multi-Agent Complexity

### 6.1 One Container, One Agent

Originally, we had one container (`docker-claude-agent-1`) for one agent (`claude`). Simple.

### 6.2 The Multi-Agent Challenge

For multiple agents (claude, qa, tu_ui, etc.), we need:

1. **Separate containers** - So they don't interfere with each other
2. **Separate config directories** - So their Claude Code settings don't conflict
3. **Separate identities** - So qa knows it's qa, not claude

### 6.3 What Can Go Wrong

**Shared Config Directory Problem**:
```
Container 1 (claude)                 Container 2 (qa)
       │                                    │
       ▼                                    ▼
┌──────────────────────────────────────────────────────┐
│        .claude/users/claude/container/               │
│        (SAME directory mounted in both!)             │
│                                                      │
│  .mcp-configured  ← Created by Container 1           │
│  .claude.json     ← Modified by both, conflicts!     │
└──────────────────────────────────────────────────────┘
```

If both containers share the same config directory:
- Marker files from one affect the other
- Settings from one overwrite the other
- Chaos ensues

**Stale Container Problem**:
```
Test 1: Run container, MCP works, exit
        Container still exists (stopped but not removed)

Test 2: Run script again
        Old container conflicts with new one
        OR old container is reused with stale state
```

### 6.4 Our Intended Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Host Computer                             │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐                           │
│  │ QMS MCP     │  │ Git MCP     │  (Shared by all agents)   │
│  │ Port 8000   │  │ Port 8001   │                           │
│  └──────┬──────┘  └──────┬──────┘                           │
│         │                │                                   │
│  ┌──────┴────────────────┴──────┐                           │
│  │      host.docker.internal    │                           │
│  └──────────────────────────────┘                           │
│         │                │                                   │
│  ┌──────┴──────┐  ┌──────┴──────┐                           │
│  │ Container:  │  │ Container:  │                           │
│  │ agent-claude│  │ agent-qa    │                           │
│  │             │  │             │                           │
│  │ Config:     │  │ Config:     │                           │
│  │ .claude/    │  │ .claude/    │                           │
│  │ users/      │  │ users/      │                           │
│  │ claude/     │  │ qa/         │  (SEPARATE directories)   │
│  │ container/  │  │ container/  │                           │
│  │             │  │             │                           │
│  │ CLAUDE.md:  │  │ CLAUDE.md:  │                           │
│  │ (default)   │  │ qa.md       │  (DIFFERENT identity)     │
│  └─────────────┘  └─────────────┘                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Chapter 7: Why Things Keep Breaking

### 7.1 The Working Pattern (docker-compose)

The original working script uses `docker-compose`:

```bash
docker-compose up -d --build claude-agent  # Start detached
docker-compose exec claude-agent claude    # Attach interactively
```

What happens:
1. `up -d` starts container, entrypoint runs
2. Entrypoint configures MCP, then `exec claude` (Claude runs in background)
3. `docker-compose exec` runs ANOTHER Claude process
4. User interacts with second Claude, which can see MCP config from first

**This works but is weird**: Two Claude processes in one container.

### 7.2 The Broken Pattern (docker run with --entrypoint override)

Our multi-agent script used:

```bash
docker run -d --entrypoint /bin/bash ... -c "sleep infinity"  # Bypass entrypoint
docker exec -it container claude                               # Run claude manually
```

What happens:
1. Container starts with `sleep infinity` (not entrypoint)
2. Entrypoint NEVER RUNS - MCP is never configured
3. We try to configure MCP manually with `claude mcp add`
4. Manual configuration is inconsistent/buggy

**Why we did this**: To keep container running so we could attach/detach multiple times.

### 7.3 The Current Attempt (docker run preserving entrypoint)

```bash
docker run -d ...  # Start detached, entrypoint runs
docker exec -it container claude  # Run second claude
```

This should work like docker-compose, but something's still wrong. Possibly:
- Entrypoint crashing before configuring MCP
- Race condition between entrypoint and our exec
- Configuration conflict between user and project scope MCP

---

## Chapter 8: Diagnostic Checklist

When MCP fails, check these in order:

### 8.1 Are MCP Servers Running?

```bash
curl http://localhost:8000/mcp  # Should return something (even error)
curl http://localhost:8001/mcp  # Should return something
```

### 8.2 Can Container Reach Servers?

```bash
docker exec agent-qa curl http://host.docker.internal:8000/mcp
docker exec agent-qa curl http://host.docker.internal:8001/mcp
```

### 8.3 Is MCP Configured?

```bash
# Check marker files
ls -la .claude/users/qa/container/.mcp-configured
ls -la .claude/users/qa/container/.git-mcp-configured

# Check config content
cat .claude/users/qa/container/.claude.json | grep -A 10 mcpServers
```

### 8.4 Are There Stale Containers?

```bash
docker ps -a  # List all containers including stopped ones
docker rm -f agent-claude agent-qa  # Remove old containers
```

### 8.5 Clean Slate Reset

```bash
# Stop MCP servers
kill $(cat .qms-mcp-server.pid) $(cat .git-mcp-server.pid)

# Remove all agent containers
docker rm -f agent-claude agent-qa

# Clear marker files
rm -f .claude/users/*/container/.mcp-configured
rm -f .claude/users/*/container/.git-mcp-configured

# Now start fresh
./claude-session.sh
```

---

## Summary: The Key Insights

1. **Containers are isolated** - They can't see host files unless you mount them
2. **Mounts create connections** - Changes in mounted directories affect both host and container
3. **Entrypoint is the startup script** - It configures MCP; bypassing it breaks MCP
4. **Marker files prevent re-configuration** - But can cause issues across container restarts
5. **MCP needs: running servers + network path + configuration** - All three must work
6. **Multi-agent needs: separate containers + separate configs** - Sharing causes conflicts
7. **Stale state causes confusion** - Always clean up old containers and marker files before testing
