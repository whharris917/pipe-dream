#!/usr/bin/env python3
"""
MCP Stdio-to-HTTP Proxy

Bridges Claude Code's stdio MCP client to a remote HTTP MCP server.
Reads JSON-RPC messages from stdin, forwards via HTTP POST, returns
responses via stdout. Handles connection retries transparently.

Usage:
    python mcp_proxy.py <remote_url> [--retries N] [--timeout MS] [--header KEY=VALUE ...]

Example:
    python mcp_proxy.py http://host.docker.internal:8000/mcp --retries 3 --header X-API-Key=qms-internal
"""

import argparse
import json
import os
import sys
import time
import uuid

import httpx


def log(msg):
    """Log to stderr (stdout is reserved for MCP protocol)."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"{ts} [mcp-proxy] INFO: {msg}", file=sys.stderr, flush=True)


def parse_args():
    parser = argparse.ArgumentParser(description="MCP Stdio-to-HTTP Proxy")
    parser.add_argument("url", help="Remote MCP server URL")
    parser.add_argument(
        "--retries", type=int, default=3,
        help="Number of retry attempts on failure (default: 3)",
    )
    parser.add_argument(
        "--timeout", type=int, default=10000,
        help="Request timeout in milliseconds (default: 10000)",
    )
    parser.add_argument(
        "--header", action="append", default=[],
        help="HTTP header in KEY=VALUE format (repeatable)",
    )
    return parser.parse_args()


def build_headers(header_args, instance_id=""):
    """Build HTTP headers from CLI --header arguments."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    for h in header_args:
        if "=" in h:
            key, value = h.split("=", 1)
            headers[key] = value

    # Inject QMS identity from container environment (REQ-MCP-015)
    qms_user = os.environ.get("QMS_USER")
    if qms_user:
        headers["X-QMS-Identity"] = qms_user

    # Inject instance UUID for collision detection (REQ-MCP-016)
    if instance_id:
        headers["X-QMS-Instance"] = instance_id

    return headers


def parse_response(response):
    """Parse the HTTP response, handling both JSON and SSE formats.

    MCP streamable-http servers may respond with either:
    - application/json: plain JSON body
    - text/event-stream: SSE format (event: message\\ndata: {json}\\n)
    """
    content_type = response.headers.get("content-type", "")

    if "text/event-stream" in content_type:
        # Parse SSE: extract JSON from "data:" lines
        for line in response.text.splitlines():
            if line.startswith("data: "):
                return json.loads(line[6:])
        return None

    # Default: parse as JSON
    return response.json()


def forward_request(client, url, message, headers, retries, timeout):
    """Forward a JSON-RPC message to the remote server with retry logic.

    Returns the parsed JSON response, or None for notifications (202).
    On total failure, returns a JSON-RPC error response.
    """
    last_error = None
    for attempt in range(retries + 1):
        try:
            response = client.post(
                url,
                content=json.dumps(message),
                headers=headers,
                timeout=timeout,
            )
            # 202 = notification accepted, no response body
            if response.status_code == 202:
                return None
            if response.status_code >= 400:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            return parse_response(response)
        except Exception as e:
            last_error = e
            if attempt < retries:
                backoff = min(2 ** attempt, 8)
                log(f"Retry {attempt + 1}/{retries} after error: {e}")
                time.sleep(backoff)

    # All retries exhausted
    log(f"All {retries + 1} attempts failed: {last_error}")
    error_response = {
        "jsonrpc": "2.0",
        "error": {
            "code": -32000,
            "message": f"Remote server unreachable after {retries + 1} attempts: {last_error}",
        },
    }
    if "id" in message:
        error_response["id"] = message["id"]
    return error_response


def main():
    args = parse_args()
    instance_id = str(uuid.uuid4())  # Unique per proxy lifecycle (REQ-MCP-016)
    headers = build_headers(args.header, instance_id)
    timeout = args.timeout / 1000.0  # ms -> seconds

    log(f"Starting: {args.url}")
    log(f"Retries: {args.retries}, Timeout: {args.timeout}ms")
    log(f"Instance: {instance_id[:8]}")
    if "X-QMS-Identity" in headers:
        log(f"Identity: {headers['X-QMS-Identity']} (from QMS_USER)")

    client = httpx.Client()

    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                message = json.loads(line)
            except json.JSONDecodeError as e:
                log(f"Invalid JSON from stdin: {e}")
                continue

            method = message.get("method", "???")
            msg_id = message.get("id", "notification")
            log(f"-> {method} (id={msg_id})")

            response = forward_request(
                client, args.url, message, headers, args.retries, timeout,
            )

            if response is not None:
                response_line = json.dumps(response)
                print(response_line, flush=True)
                log(f"<- response ({len(response_line)} bytes)")
    except KeyboardInterrupt:
        log("Shutting down")
    finally:
        client.close()


if __name__ == "__main__":
    main()
