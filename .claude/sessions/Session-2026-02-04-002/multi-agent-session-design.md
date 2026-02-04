# Multi-Agent Session: The Intermediate Rung

This document captures the architectural vision for the intermediate step between single-container operation and the full Hub.

## The Ladder

```
┌─────────────────────────────────────────────────────────────────┐
│  5. GUI                                                         │
│     Visual interface to Hub                                     │
├─────────────────────────────────────────────────────────────────┤
│  4. Hub                                                         │
│     Programmatic coordination, policies, inbox watching         │
├─────────────────────────────────────────────────────────────────┤
│  3. Multi-Agent Session  ← THIS RUNG                            │
│     Multiple containers + inter-agent communication             │
├─────────────────────────────────────────────────────────────────┤
│  2. Containerized Session                                       │
│     Single container, MCP servers for QMS/Git access            │
├─────────────────────────────────────────────────────────────────┤
│  1. Basic                                                       │
│     Single terminal, sub-agents via Task tool                   │
└─────────────────────────────────────────────────────────────────┘
```

Each rung builds on the previous. The QMS framework is constant—only the execution environment changes.

## The Problem with "Just Running Multiple Containers"

If we simply start multiple containers (claude, qa, tu_ui), they're **deaf to each other**:

```
┌──────────────┐          ┌──────────────┐
│    claude    │          │      qa      │
│              │          │              │
│  Routes doc  │───────── │  Inbox has   │
│  for review  │   QMS    │  a task but  │
│              │  writes  │  doesn't     │
│              │  task    │  know it     │
└──────────────┘          └──────────────┘
                                 ↑
                          No signal reaches
                          the running session
```

Claude Code is request-response. A running session doesn't receive unsolicited messages. Even if qa's container is active and has a task in its inbox, nothing spurs it to action.

## The Missing Piece: Inter-Agent Communication

For multi-agent operation to work, we need a mechanism for one agent to **ping** another:

```
┌──────────────┐          ┌──────────────┐
│    claude    │          │      qa      │
│              │          │              │
│  Routes doc  │───────── │  Inbox has   │
│  for review  │   QMS    │  a task      │
│              │  writes  │              │
│  Pings qa    │───────── │  Receives    │
│              │  signal  │  ping!       │
│              │          │              │
│              │          │  Checks      │
│              │          │  inbox...    │
└──────────────┘          └──────────────┘
```

## Inbox Item Types

Currently, inboxes only contain auto-generated workflow tasks. To enable richer inter-agent communication, we expand the inbox to support multiple item types:

| Type | Prefix | Source | Purpose | Action Required |
|------|--------|--------|---------|-----------------|
| **Task** | `task-` | QMS (auto) | Formal workflow action | Yes - must complete |
| **Message** | `msg-` | Agent (manual) | Direct communication | Yes - should read/respond |
| **Notification** | `notif-` | QMS (auto) | FYI, status update | No - informational only |

### Task (Existing)

Auto-generated when documents are routed for review/approval:

```yaml
# .claude/users/qa/inbox/task-CR-056-pre_review-v0-1.md
---
task_id: task-CR-056-pre_review-v0-1
task_type: REVIEW
workflow_type: PRE_REVIEW
doc_id: CR-056
assigned_by: claude
assigned_date: 2026-02-04
version: 0.1
---

Please review CR-056 for technical accuracy.
```

### Message (New)

Direct agent-to-agent communication via new QMS CLI command:

```bash
# Claude sends a message to QA
qms message qa --subject "Note on CR-056" "CR-056 involves UI changes. Consider assigning TU-UI."
```

Creates:

```yaml
# .claude/users/qa/inbox/msg-claude-2026-02-04-143022.md
---
type: message
from: claude
to: qa
timestamp: 2026-02-04T14:30:22Z
subject: "Note on CR-056"
---

CR-056 involves UI changes. Consider assigning TU-UI to the review team.
```

**Use cases:**
- Context sharing before a review
- Questions between agents
- Coordination on who handles what
- Informal discussion outside formal workflow

### Notification (New)

Auto-generated by QMS for status updates:

```yaml
# .claude/users/claude/inbox/notif-CR-056-approved-2026-02-04.md
---
type: notification
event: APPROVED
doc_id: CR-056
timestamp: 2026-02-04T15:45:00Z
---

CR-056 has been approved by qa.
```

**Generated when:**
- Document you own is approved/rejected
- Document you reviewed moves to next stage
- Child document (VAR, TP) changes state

### QMS CLI Extension

New command for sending messages:

```bash
qms message <recipient> --subject "Subject" "Body text"
qms message <recipient> -s "Subject" -f message.md  # From file
```

### Benefits of Expanded Inbox

1. **Context sharing** - Claude can give QA a heads-up before formal review
2. **Questions** - Agents can ask for clarification within QMS
3. **Coordination** - Negotiate task handling without human intervention
4. **Audit trail** - All inter-agent communication captured and traceable
5. **Notifications** - Agents stay informed of workflow progress

---

## Inbox Archive

Inbox items are never deleted. When processed, they move to a permanent archive.

### Directory Structure

```
.claude/users/{agent}/
├── inbox/           # Active items (pending action)
├── inbox-archive/   # Completed items (permanent record)
├── workspace/       # QMS checkout workspace
└── container/       # Claude Code config (containerized mode)
```

### Archive Organization

Items are archived by date for easy navigation:

```
.claude/users/qa/inbox-archive/
├── 2026-02-04/
│   ├── task-CR-056-pre_review-v0-1.md
│   ├── msg-claude-143022.md
│   └── notif-CR-055-approved.md
├── 2026-02-05/
│   ├── task-CR-057-pre_approval-v0-1.md
│   └── task-CR-056-post_review-v1-1.md
└── ...
```

### Workflow

```
1. Task arrives
   └── .claude/users/qa/inbox/task-CR-056-review.md

2. Agent processes task
   └── qms review CR-056 --recommend

3. QMS archives the task
   └── mv inbox/task-CR-056-review.md inbox-archive/2026-02-04/

4. Inbox is now empty (or has other pending items)
```

### What Gets Archived

| Item Type | Archived When |
|-----------|---------------|
| Task | Agent completes the action (review, approve, reject) |
| Message | Agent explicitly marks as read (`qms inbox --archive <id>`) |
| Notification | Auto-archived after display, or manually (`qms inbox --archive <id>`) |

### Benefits

1. **Audit trail** - Complete history of what each agent processed and when
2. **Debugging** - Review what an agent saw when they took action
3. **Analytics** - Track throughput, response times, workflow patterns
4. **Recovery** - Original task preserved if something goes wrong
5. **Compliance** - Full traceability for QMS governance

### QMS CLI Support

```bash
# View archive
qms inbox --archive                    # List archived items
qms inbox --archive --date 2026-02-04  # List items from specific date

# Manually archive (for messages/notifications)
qms inbox --archive msg-claude-143022  # Archive specific item
qms inbox --archive --notifications    # Archive all notifications
```

---

## Design: The Inbox Watcher

The simplest approach that fits our architecture: a **watcher process** that monitors inboxes and injects notifications into agent terminals.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     multi-agent-session.sh                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    tmux session                          │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │   │
│  │  │   claude    │ │     qa      │ │   tu_ui     │        │   │
│  │  │   (pane 0)  │ │  (pane 1)   │ │  (pane 2)   │        │   │
│  │  └──────▲──────┘ └──────▲──────┘ └──────▲──────┘        │   │
│  └─────────┼───────────────┼───────────────┼───────────────┘   │
│            │               │               │                    │
│            └───────────────┼───────────────┘                    │
│                            │                                    │
│                    ┌───────┴───────┐                           │
│                    │ Inbox Watcher │                           │
│                    │  (background) │                           │
│                    └───────┬───────┘                           │
│                            │ watches                           │
│                            ▼                                    │
│                    .claude/users/*/inbox/                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### How It Works

1. **Startup**: Script launches tmux with one pane per agent
2. **Watcher**: Background process monitors all inbox directories
3. **On task arrival**: Watcher detects new file in `{agent}/inbox/`
4. **Notification**: Watcher injects text into that agent's tmux pane

### The Notification Mechanism

When an item appears in an agent's inbox, the watcher detects the file type by prefix and sends an appropriate notification:

**Task arrives:**
```bash
tmux send-keys -t qms-agents:qa "
╭────────────────────────────────────────╮
│  📋 New task: Review CR-056            │
│  Run: qms inbox                        │
╰────────────────────────────────────────╯
"
```

**Message arrives:**
```bash
tmux send-keys -t qms-agents:qa "
╭────────────────────────────────────────╮
│  💬 Message from claude                │
│  Subject: Note on CR-056               │
│  Run: qms inbox                        │
╰────────────────────────────────────────╯
"
```

**Notification arrives:**
```bash
tmux send-keys -t qms-agents:claude "
╭────────────────────────────────────────╮
│  🔔 CR-056 has been approved           │
│  Run: qms inbox                        │
╰────────────────────────────────────────╯
"
```

This literally types the notification into the terminal. The agent sees it and can respond.

### Agent Response

The agent's CLAUDE.md (or agent definition file) should instruct:

> When you see a notification about new inbox tasks, immediately run `qms inbox` and process pending items.

This creates the loop:
1. Claude routes document → task appears in qa's inbox
2. Watcher detects task → sends notification to qa's pane
3. QA sees notification → checks inbox → processes task
4. QA completes review → document state changes
5. (Optionally) Watcher notifies claude that review is complete

## Implementation Sketch

### multi-agent-session.sh

```bash
#!/bin/bash
# Multi-agent session launcher
# Usage: ./multi-agent-session.sh [agent1] [agent2] ...
# Default: claude qa

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SESSION_NAME="qms-agents"

# Default agents if none specified
if [ $# -eq 0 ]; then
    AGENTS=("claude" "qa")
else
    AGENTS=("$@")
fi

# Validate agents
VALID_AGENTS=("claude" "qa" "tu_ui" "tu_scene" "tu_sketch" "tu_sim" "bu")
for agent in "${AGENTS[@]}"; do
    if [[ ! " ${VALID_AGENTS[@]} " =~ " ${agent} " ]]; then
        echo "Error: Invalid agent '$agent'"
        exit 1
    fi
done

echo "Starting multi-agent session with: ${AGENTS[*]}"

# Step 1: Start MCP servers
echo "[1/4] Starting MCP servers..."
"$SCRIPT_DIR/scripts/start-mcp-server.sh" --background
"$SCRIPT_DIR/scripts/start-git-mcp.sh" --background

# Step 2: Ensure container directories exist
echo "[2/4] Preparing agent directories..."
for agent in "${AGENTS[@]}"; do
    mkdir -p "$PROJECT_ROOT/.claude/users/$agent/container"
done

# Step 3: Create tmux session with panes
echo "[3/4] Creating tmux session..."
tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true
tmux new-session -d -s "$SESSION_NAME" -n agents

# Create a pane for each agent
first=true
for agent in "${AGENTS[@]}"; do
    if [ "$first" = true ]; then
        first=false
    else
        tmux split-window -t "$SESSION_NAME" -h
        tmux select-layout -t "$SESSION_NAME" tiled
    fi
done

# Start containers in each pane
pane_index=0
for agent in "${AGENTS[@]}"; do
    # Build the docker run command
    if [ "$agent" = "claude" ]; then
        CLAUDE_MD_MOUNT=""
    else
        CLAUDE_MD_MOUNT="-v $PROJECT_ROOT/.claude/agents/${agent}.md:/pipe-dream/CLAUDE.md:ro"
    fi

    CMD="docker run -it --rm \
        --name agent-${agent} \
        --hostname ${agent} \
        -e QMS_USER=${agent} \
        -e HOME=/ \
        -e CLAUDE_CONFIG_DIR=/claude-config \
        -e MCP_TIMEOUT=60000 \
        -v ${PROJECT_ROOT}:/pipe-dream:ro \
        -v ${PROJECT_ROOT}/.claude/users/${agent}/workspace:/pipe-dream/.claude/users/${agent}/workspace:rw \
        -v ${PROJECT_ROOT}/.claude/sessions:/pipe-dream/.claude/sessions:rw \
        -v ${PROJECT_ROOT}/.claude/users/${agent}/container:/claude-config:rw \
        -v ${PROJECT_ROOT}/docker/.mcp.json:/pipe-dream/.mcp.json:ro \
        -v ${PROJECT_ROOT}/docker/.claude-settings.json:/pipe-dream/.claude/settings.local.json:ro \
        ${CLAUDE_MD_MOUNT} \
        --add-host=host.docker.internal:host-gateway \
        -w /pipe-dream \
        claude-agent \
        claude"

    tmux send-keys -t "$SESSION_NAME:0.$pane_index" "$CMD" Enter
    ((pane_index++))
done

# Step 4: Start inbox watcher
echo "[4/4] Starting inbox watcher..."
"$SCRIPT_DIR/scripts/inbox-watcher.sh" "$SESSION_NAME" "${AGENTS[@]}" &
WATCHER_PID=$!
echo $WATCHER_PID > "$PROJECT_ROOT/.inbox-watcher.pid"

# Attach to tmux session
echo "Attaching to session. Use Ctrl-B + arrow keys to switch panes."
echo "Ctrl-B + D to detach (containers keep running)."
tmux attach -t "$SESSION_NAME"

# Cleanup on exit
echo "Stopping inbox watcher..."
kill $WATCHER_PID 2>/dev/null
```

### inbox-watcher.sh

```bash
#!/bin/bash
# Watches agent inboxes and sends notifications to tmux panes
# Usage: ./inbox-watcher.sh <session_name> <agent1> <agent2> ...

SESSION_NAME="$1"
shift
AGENTS=("$@")

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Build list of inbox paths to watch
WATCH_PATHS=()
for agent in "${AGENTS[@]}"; do
    WATCH_PATHS+=("$PROJECT_ROOT/.claude/users/$agent/inbox")
done

echo "Inbox watcher started for: ${AGENTS[*]}"

# Function to parse inbox item and generate notification
generate_notification() {
    local file="$1"
    local filepath="$2"

    # Determine type by prefix
    if [[ "$file" == task-* ]]; then
        # Extract doc_id from filename (e.g., task-CR-056-pre_review-v0-1.md)
        doc_id=$(echo "$file" | grep -oP '(?<=task-)[A-Z]+-[0-9]+')
        echo "╭────────────────────────────────────────╮"
        echo "│  📋 New task: Review $doc_id"
        echo "│  Run: qms inbox                        │"
        echo "╰────────────────────────────────────────╯"
    elif [[ "$file" == msg-* ]]; then
        # Extract sender from filename (e.g., msg-claude-2026-02-04-143022.md)
        sender=$(echo "$file" | grep -oP '(?<=msg-)[a-z_]+')
        # Try to extract subject from file
        subject=$(grep -oP '(?<=subject: ")[^"]+' "$filepath" 2>/dev/null || echo "New message")
        echo "╭────────────────────────────────────────╮"
        echo "│  💬 Message from $sender"
        echo "│  Subject: $subject"
        echo "│  Run: qms inbox                        │"
        echo "╰────────────────────────────────────────╯"
    elif [[ "$file" == notif-* ]]; then
        # Extract doc_id and event from filename
        doc_id=$(echo "$file" | grep -oP '[A-Z]+-[0-9]+')
        event=$(grep -oP '(?<=event: )[A-Z_]+' "$filepath" 2>/dev/null || echo "update")
        echo "╭────────────────────────────────────────╮"
        echo "│  🔔 $doc_id: $event"
        echo "│  Run: qms inbox                        │"
        echo "╰────────────────────────────────────────╯"
    else
        # Unknown type, generic notification
        echo "╭────────────────────────────────────────╮"
        echo "│  📬 New inbox item: $file"
        echo "│  Run: qms inbox                        │"
        echo "╰────────────────────────────────────────╯"
    fi
}

# Use inotifywait to watch for new files
inotifywait -m -e create -e moved_to "${WATCH_PATHS[@]}" 2>/dev/null | while read path action file; do
    # Extract agent from path
    agent=$(echo "$path" | grep -oP '(?<=users/)[^/]+')

    if [ -n "$agent" ]; then
        echo "New inbox item detected for $agent: $file"

        # Find pane index for this agent
        pane_index=0
        for a in "${AGENTS[@]}"; do
            if [ "$a" = "$agent" ]; then
                break
            fi
            ((pane_index++))
        done

        # Generate appropriate notification
        filepath="${path}${file}"
        notification=$(generate_notification "$file" "$filepath")

        # Send notification to the agent's pane
        tmux send-keys -t "$SESSION_NAME:0.$pane_index" ""  # Clear any partial input
        tmux send-keys -t "$SESSION_NAME:0.$pane_index" "$notification"
    fi
done
```

## Agent Definition Update

Agent definition files (`.claude/agents/*.md`) should include instruction to respond to inbox notifications:

```markdown
## Inbox Notifications

When you see a notification like:
╭────────────────────────────────────────╮
│  📬 New task in inbox                  │
│  Run: qms inbox                        │
╰────────────────────────────────────────╯

Immediately run `qms inbox` and process pending tasks according to your role.
```

## Comparison: This Rung vs The Hub

| Capability | Multi-Agent Session | Hub |
|------------|---------------------|-----|
| Multiple containers | ✓ | ✓ |
| Inter-agent notification | ✓ (text injection) | ✓ (WebSocket) |
| Auto-launch on task | ✗ | ✓ |
| Auto-stop on idle | ✗ | ✓ |
| Launch policies | ✗ | ✓ |
| Programmatic API | ✗ | ✓ |
| GUI integration | ✗ | ✓ |
| Manual container lifecycle | ✓ | Optional |
| tmux-based interface | ✓ | ✗ (own terminals) |

The multi-agent session is a **manual multiplexer** with notifications. The Hub is an **automated coordinator** with policies.

## What We Learn from This Rung

Building and using the multi-agent session will reveal:

1. **Notification UX**: Is text injection sufficient? Too noisy? Need acknowledgment?
2. **Agent responsiveness**: Do agents reliably respond to notifications?
3. **Workflow patterns**: How do agents actually coordinate in practice?
4. **Pain points**: What manual steps become tedious and should be automated?

These lessons directly inform Hub design.

## Scope Summary

**In scope for this rung:**
- Launch multiple containers via single script
- tmux-based multiplexing
- Inbox watching with file system events
- Text injection notifications (type-aware)
- Manual start/stop of agents
- Inter-agent messaging via `qms message` command
- Notification generation for workflow events

**Out of scope (deferred to Hub):**
- Auto-launch/stop policies
- REST/WebSocket API
- GUI integration
- Idle timeout detection
- Programmatic coordination

## QMS CLI Changes Required

| Command | Description | Priority |
|---------|-------------|----------|
| `qms message <to> --subject "..." "body"` | Send message to agent | High |
| `qms inbox` (update) | Display all item types with icons | High |
| Auto-archive on action | Move task to archive when completed | High |
| `qms inbox --archive` | View archived items | Medium |
| `qms inbox --archive <id>` | Manually archive an item | Medium |
| `qms inbox --archive --date YYYY-MM-DD` | View archive for specific date | Low |

## Next Steps

1. Implement `qms message` command in QMS CLI
2. Update `qms inbox` to display item types distinctly
3. Create `multi-agent-session.sh`
4. Create `inbox-watcher.sh`
5. Update agent definition files with notification handling
6. Test with claude + qa workflow (including messages)
7. Iterate based on learnings
8. Document friction points for Hub requirements
