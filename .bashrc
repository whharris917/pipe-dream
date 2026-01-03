# Project-level bash configuration
# This file should be sourced by shells working in this project

# Add .claude to PATH for qms command
PROJ_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$PATH:$PROJ_ROOT/.claude"

# Set default QMS user
export QMS_USER="${QMS_USER:-claude}"
