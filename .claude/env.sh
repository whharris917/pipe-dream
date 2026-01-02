# QMS Environment Setup
# Source this file to enable qms commands: source .claude/env.sh

# Add .claude to PATH for qms command
export PATH="$PATH:$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# QMS_USER must be set explicitly - no default allowed
if [ -z "$QMS_USER" ]; then
    echo "Warning: QMS_USER not set. Set your identity with: export QMS_USER=<username>"
else
    echo "QMS environment loaded. User: $QMS_USER"
fi
