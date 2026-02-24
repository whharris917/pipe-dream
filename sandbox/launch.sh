#!/usr/bin/env bash
# ============================================================================
# QMS Sandbox — End-User Testing Environment
#
# Simulates the intended end-user setup:
#   ~/projects/my-project/
#   ├── qms-cli/          (submodule)
#   ├── QMS/              (created by qms init)
#   ├── .claude/          (created by qms init)
#   └── CLAUDE.md         (created by qms init)
#
# Launches a fresh Docker container with qms-cli and Claude Code installed.
# No connection to the real QMS. Safe to experiment freely.
#
# Usage:
#   ./sandbox/launch.sh              # default: python:3.11-slim
#   ./sandbox/launch.sh 3.12         # specify Python version
#
# Authentication (pick one):
#   - Existing credentials: mounts ~/.claude/.credentials.json from host (auto-detected)
#   - API key: ANTHROPIC_API_KEY=sk-... ./sandbox/launch.sh
#   - Manual: run 'claude login' inside the container
# ============================================================================

set -euo pipefail

PYTHON_VERSION="${1:-3.11}"
IMAGE="python:${PYTHON_VERSION}-slim"
CONTAINER_NAME="qms-sandbox"
REPO_URL="https://github.com/whharris917/qms-cli.git"

echo "=== QMS Sandbox ==="
echo "Image:  ${IMAGE}"
echo ""

# Kill any previous sandbox container
docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true

# Build docker run arguments
DOCKER_ARGS=(
  run -it
  --name "${CONTAINER_NAME}"
)

# --- Authentication ---
# Option 1: Pass through API key if set
if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  DOCKER_ARGS+=(-e "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}")
  echo "Auth:   API key (from environment)"
# Option 2: Mount just the credentials file from host (not the full profile)
elif [ -f "${HOME}/.claude/.credentials.json" ]; then
  DOCKER_ARGS+=(-v "${HOME}/.claude/.credentials.json:/root/.claude-host-credentials.json:ro")
  echo "Auth:   Mounting ~/.claude/.credentials.json from host"
else
  echo "Auth:   None (run 'claude login' inside container)"
fi

echo ""

docker "${DOCKER_ARGS[@]}" "${IMAGE}" bash -c "
  set -e

  echo '--- Installing system dependencies ---'
  apt-get update -qq && apt-get install -y -qq git nodejs npm > /dev/null 2>&1

  echo '--- Installing Claude Code ---'
  npm install -g --silent @anthropic-ai/claude-code 2>&1 | tail -1

  # Set up project directory (mirrors intended end-user layout)
  mkdir -p /root/projects/my-project && cd /root/projects/my-project
  git init -q
  git config user.email 'sandbox@example.com'
  git config user.name 'Sandbox User'

  echo '--- Adding qms-cli as submodule ---'
  git submodule add -q ${REPO_URL} qms-cli

  echo '--- Installing Python dependencies ---'
  pip install -q --root-user-action=ignore --no-warn-script-location -r qms-cli/requirements.txt 2>&1 | grep -v '^\[notice\]'

  # Put qms on PATH via a wrapper
  cat > /usr/local/bin/qms << 'WRAPPER'
#!/usr/bin/env bash
exec python ~/projects/my-project/qms-cli/qms.py \"\$@\"
WRAPPER
  chmod +x /usr/local/bin/qms

  echo '--- Bootstrapping project ---'
  python qms-cli/qms.py init

  # Initial commit so auto-commits during execution have a base
  git add -A && git commit -q -m 'Initial QMS project'

  # --- Claude Code auth setup ---
  # If host credentials file was mounted, copy it into a fresh .claude config dir
  if [ -f /root/.claude-host-credentials.json ]; then
    mkdir -p /root/.claude
    cp /root/.claude-host-credentials.json /root/.claude/.credentials.json
    echo 'Copied credentials from host (auth only, no history/settings/memory).'
  fi

  echo ''
  echo '============================================'
  echo '  QMS Sandbox ready!'
  echo ''
  echo '  Project: ~/projects/my-project'
  echo '  QMS CLI: qms --help'
  echo '  Claude:  claude'
  echo '  Docs:    qms-cli/manual/'
  echo ''
  echo '  Try:  qms --user lead create CR --title \"My first change\"'
  echo '============================================'
  echo ''

  exec bash
"
