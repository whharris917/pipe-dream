"""
Git MCP Server

Model Context Protocol server for git operations from containers.
Provides a controlled proxy for git commands with submodule and destructive operation protection.

CR-054: Git MCP Server for Container Operations
"""

import argparse
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Configure logging to stderr (CRITICAL: never write to stdout for stdio transport)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("git-mcp")

# Initialize FastMCP server
mcp = FastMCP("git")

# Blocked patterns for submodule protection
BLOCKED_SUBMODULES = [
    r"\bflow-state\b",
    r"\bqms-cli\b",
]

# Blocked patterns for destructive operations
BLOCKED_DESTRUCTIVE = [
    r"push\s+.*--force",
    r"push\s+-[a-zA-Z]*f",
    r"reset\s+--hard",
    r"clean\s+-[a-zA-Z]*f",
    r"checkout\s+\.\s*$",
    r"checkout\s+\.\s*[;&|]",
    r"restore\s+\.\s*$",
    r"restore\s+\.\s*[;&|]",
]


def get_project_root() -> Path | None:
    """
    Determine the project root directory.

    Resolution order:
    1. GIT_MCP_PROJECT_ROOT environment variable
    2. Auto-discovery by walking up from cwd looking for .git directory

    Returns None if not found.
    """
    # Check environment variable first
    env_root = os.environ.get("GIT_MCP_PROJECT_ROOT")
    if env_root:
        path = Path(env_root)
        if (path / ".git").exists():
            logger.info(f"Using project root from GIT_MCP_PROJECT_ROOT: {path}")
            return path
        else:
            logger.warning(
                f"GIT_MCP_PROJECT_ROOT={env_root} does not contain .git directory"
            )

    # Fall back to directory walking
    cwd = Path.cwd()

    # Check current directory and parents for .git
    for parent in [cwd] + list(cwd.parents):
        git_path = parent / ".git"
        if git_path.exists():
            return parent

    return None


def validate_command(command: str) -> None:
    """
    Validate a git command against blocked patterns.

    Raises:
        PermissionError: If command matches a blocked pattern
    """
    # Check for submodule references
    for pattern in BLOCKED_SUBMODULES:
        if re.search(pattern, command, re.IGNORECASE):
            raise PermissionError(
                f"Blocked: command references protected submodule (pattern: {pattern})"
            )

    # Check for destructive operations
    for pattern in BLOCKED_DESTRUCTIVE:
        if re.search(pattern, command, re.IGNORECASE):
            raise PermissionError(
                f"Blocked: destructive operation not permitted (pattern: {pattern})"
            )


@mcp.tool()
def git_exec(command: str) -> str:
    """
    Execute git command(s) on the host repository.

    Supports command chaining with && and ||. Commands referencing submodules
    (flow-state, qms-cli) or using destructive flags are blocked.

    Args:
        command: Git command string (e.g., "status", "add . && commit -m 'msg'")
                 The 'git' prefix is optional.

    Returns:
        Command output (stdout and stderr combined)

    Examples:
        git_exec("status")
        git_exec("log --oneline -10")
        git_exec("add .claude/sessions/ && commit -m 'Session notes' && push")
    """
    project_root = get_project_root()
    if project_root is None:
        return "Error: Could not find project root (no .git directory found)"

    try:
        validate_command(command)
    except PermissionError as e:
        return f"Error: {e}"

    # Ensure command starts with 'git' for each command in chain
    # Handle simple case where single command doesn't start with git
    cmd = command.strip()
    if not cmd.startswith("git ") and not cmd.startswith("git\t"):
        # Check if this is a chained command
        if "&&" in cmd or "||" in cmd or ";" in cmd:
            # For chained commands, prepend git to segments that don't have it
            # This is a simple heuristic - user can always include 'git' explicitly
            pass  # Let shell handle it as-is, user should include git
        else:
            cmd = f"git {cmd}"

    logger.info(f"Executing: {cmd}")

    try:
        # Use shell=True for cross-platform compatibility
        # On Windows: uses cmd.exe (git must be in PATH)
        # On Unix: uses /bin/sh
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=60,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )

        output = result.stdout
        if result.stderr:
            output += "\n" + result.stderr if output else result.stderr

        if result.returncode != 0:
            return f"[Exit code: {result.returncode}]\n{output.strip() if output else '(no output)'}"

        return output.strip() if output else "(no output)"

    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 60 seconds"
    except Exception as e:
        return f"Error executing command: {e}"


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the MCP server."""
    parser = argparse.ArgumentParser(
        description="Git MCP Server - Model Context Protocol server for git operations"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="Transport: stdio (default) or streamable-http (for containers)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address to bind for HTTP transport (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port to bind for HTTP transport (default: 8001)",
    )
    parser.add_argument(
        "--project-root",
        dest="project_root",
        help="Project root directory (default: auto-discover from .git)",
    )
    return parser.parse_args(args)


def main(cli_args: list[str] | None = None):
    """Entry point for the Git MCP server."""
    args = parse_args(cli_args)

    # Set project root in environment if specified via CLI
    if args.project_root:
        os.environ["GIT_MCP_PROJECT_ROOT"] = args.project_root
        logger.info(f"Project root set from --project-root: {args.project_root}")

    logger.info(f"Starting Git MCP Server (transport={args.transport})")

    # Run with selected transport
    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        # Streamable-HTTP transport for container connections
        mcp.settings.host = args.host
        mcp.settings.port = args.port

        # Allow container connections via host.docker.internal
        mcp.settings.transport_security.allowed_hosts.append("host.docker.internal:*")
        mcp.settings.transport_security.allowed_origins.append(
            "http://host.docker.internal:*"
        )

        logger.info(f"Binding to {args.host}:{args.port} (streamable-http)")
        mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
