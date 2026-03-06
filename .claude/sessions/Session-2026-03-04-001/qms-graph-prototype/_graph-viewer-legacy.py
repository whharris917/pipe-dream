#!/usr/bin/env python3
"""
QMS Graph Viewer - Interactive graph traversal prototype.

Usage: python graph-viewer.py <graph-directory>

Loads all .yaml files from the given directory, builds a traversable graph,
and lets the user experience the graph as an agent would — responding to
prompts and watching the cursor advance.
"""

import sys
import os
import yaml
from pathlib import Path


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

class Node:
    """A single node in the graph."""

    def __init__(self, data, source_file):
        node = data.get("node", data)
        self.id = node["id"]
        self.prompt = node.get("prompt", "")
        self.context = node.get("context", "")
        self.evidence_schema = node.get("evidence_schema", {})
        self.performer = node.get("performer", "initiator")
        self.condition = node.get("condition", None)
        self.edges = node.get("edges", [])
        self.hooks = node.get("hooks", {})
        self.source_file = source_file

    def __repr__(self):
        return f"Node({self.id})"


class Graph:
    """A collection of nodes loaded from YAML files in a directory."""

    def __init__(self, directory):
        self.nodes: dict[str, Node] = {}
        self.start_node: Node | None = None
        self._load_directory(directory)

    def _load_directory(self, directory):
        path = Path(directory)
        for yaml_file in sorted(path.rglob("*.yaml")):
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data:
                continue
            node = Node(data, str(yaml_file))
            self.nodes[node.id] = node
            if node.id.endswith(".start") or yaml_file.stem == "start":
                if self.start_node is None:
                    self.start_node = node

        if self.start_node is None and self.nodes:
            self.start_node = next(iter(self.nodes.values()))

    def get(self, node_id: str) -> Node | None:
        return self.nodes.get(node_id)


class Ticket:
    """A cursor riding on the graph, collecting responses."""

    def __init__(self, graph: Graph):
        self.graph = graph
        self.cursor: str | None = graph.start_node.id if graph.start_node else None
        self.responses: dict[str, object] = {}
        self.history: list[tuple[str, object, int]] = []  # (node_id, response, visit#)
        self._visit_count: dict[str, int] = {}

    def record(self, node_id: str, response: object):
        count = self._visit_count.get(node_id, 0) + 1
        self._visit_count[node_id] = count

        # On revisit (loop), promote to list
        if count > 1:
            prev = self.responses.get(node_id)
            if prev is not None and not isinstance(prev, list):
                self.responses[node_id] = [prev]
            self.responses.setdefault(node_id, [])
            self.responses[node_id].append(response)
        else:
            self.responses[node_id] = response

        self.history.append((node_id, response, count))


# ---------------------------------------------------------------------------
# Expression evaluator (safe, minimal)
# ---------------------------------------------------------------------------

class Evaluator:
    """Evaluate simple condition expressions against ticket state."""

    def __init__(self, ticket: Ticket):
        self.ticket = ticket

    def evaluate(self, expression: str) -> bool:
        if not expression:
            return True

        ns = dict(self.ticket.responses)

        # Make the most recent response available as `response`
        if self.ticket.history:
            _, last_resp, _ = self.ticket.history[-1]
            if isinstance(last_resp, dict):
                ns["response"] = last_resp
            else:
                ns["response"] = last_resp

        # Also expose a flat view: response.field -> value
        # by putting all response dicts' keys at top level under 'r'
        ns["r"] = {}
        for nid, resp in self.ticket.responses.items():
            if isinstance(resp, dict):
                for k, v in resp.items():
                    ns["r"][f"{nid}.{k}"] = v

        try:
            return bool(eval(expression, {"__builtins__": {}}, ns))
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
WHITE = "\033[37m"


def _summarize(response: object, max_len: int = 65) -> str:
    if isinstance(response, dict):
        parts = []
        for k, v in response.items():
            if k.startswith("_"):
                continue
            parts.append(f"{k}: {v}")
        s = ", ".join(parts)
    else:
        s = str(response)
    return (s[:max_len - 3] + "...") if len(s) > max_len else s


def render(ticket: Ticket, graph: Graph) -> str:
    node = graph.get(ticket.cursor)
    if not node:
        return f"  ERROR: cursor at unknown node '{ticket.cursor}'"

    lines: list[str] = []
    w = 64

    lines.append("")
    lines.append(f"{BOLD}{'=' * w}")
    lines.append(f"  Template Builder")
    lines.append(f"  Cursor: {node.id}")
    lines.append(f"{'=' * w}{RESET}")
    lines.append("")

    # --- completed steps ---
    for nid, resp, visit in ticket.history:
        n = graph.get(nid)
        label = n.prompt[:48] if n else nid
        visit_tag = f" (#{visit})" if visit > 1 else ""
        summary = _summarize(resp)
        lines.append(f"  {GREEN}[done]{RESET} {DIM}{label}{visit_tag}{RESET}")
        lines.append(f"         {DIM}{summary}{RESET}")
        lines.append("")

    # --- active node ---
    lines.append(f"  {YELLOW}{BOLD}> [active]  {node.prompt}{RESET}")
    if node.context:
        lines.append(f"  {CYAN}            {node.context}{RESET}")
    lines.append("")

    # --- evidence schema ---
    if node.evidence_schema:
        lines.append(f"  {WHITE}Evidence needed:{RESET}")
        for fname, fschema in node.evidence_schema.items():
            ftype = fschema.get("type", "text")
            req = " (required)" if fschema.get("required") else " (optional)"
            vals = fschema.get("values", [])
            hint = fschema.get("hint", "")
            if vals:
                type_label = f"[{' | '.join(str(v) for v in vals)}]"
            else:
                type_label = f"[{ftype}]"
            line = f"    {BOLD}{fname}{RESET} {type_label}{req}"
            if hint:
                line += f"  {DIM}— {hint}{RESET}"
            lines.append(line)
        lines.append("")

    # --- peek at next ---
    if len(node.edges) == 1 and not node.edges[0].get("condition"):
        nxt = graph.get(node.edges[0]["to"])
        if nxt:
            lines.append(f"  {DIM}[next]    {nxt.prompt[:50]}{RESET}")
            lines.append("")

    # --- hooks ---
    for hook_phase, hook_list in node.hooks.items():
        for h in hook_list:
            cmd = h.get("command", "")
            if cmd:
                fail = h.get("on_failure", "")
                tag = f" (on_failure: {fail})" if fail else ""
                lines.append(f"  {DIM}Hook ({hook_phase}): {cmd}{tag}{RESET}")
        lines.append("")

    lines.append(f"{'-' * w}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Input collection
# ---------------------------------------------------------------------------

def collect(node: Node) -> dict | None:
    """Prompt the user for each field in the evidence schema. Returns None on cancel."""
    schema = node.evidence_schema
    if not schema:
        try:
            input(f"  {DIM}Press Enter to continue...{RESET}")
        except (EOFError, KeyboardInterrupt):
            return None
        return {"_ack": True}

    response: dict = {}
    for fname, fschema in schema.items():
        ftype = fschema.get("type", "text")
        required = fschema.get("required", False)
        values = fschema.get("values", [])

        while True:
            if values:
                prompt_text = f"  {BOLD}{fname}{RESET} [{' / '.join(str(v) for v in values)}]: "
            else:
                prompt_text = f"  {BOLD}{fname}{RESET}: "

            try:
                raw = input(prompt_text).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return None

            if not raw and not required:
                break
            if not raw:
                print(f"    {DIM}(required){RESET}")
                continue

            # --- validation ---
            if ftype == "enum" and values:
                if raw not in [str(v) for v in values]:
                    print(f"    Must be one of: {', '.join(str(v) for v in values)}")
                    continue
                response[fname] = raw
                break
            elif ftype == "bool":
                if raw.lower() in ("yes", "true", "y", "1"):
                    response[fname] = True
                    break
                elif raw.lower() in ("no", "false", "n", "0"):
                    response[fname] = False
                    break
                else:
                    print("    Enter yes or no")
                    continue
            elif ftype == "integer":
                try:
                    response[fname] = int(raw)
                    break
                except ValueError:
                    print("    Must be a number")
                    continue
            else:
                response[fname] = raw
                break

    return response


# ---------------------------------------------------------------------------
# Edge resolution
# ---------------------------------------------------------------------------

def next_node(node: Node, response: object, evaluator: Evaluator) -> str | None:
    """Pick the outgoing edge to follow."""
    edges = node.edges
    if not edges:
        return None

    # Single unconditional edge — fast path
    if len(edges) == 1 and not edges[0].get("condition"):
        return edges[0].get("to")

    # Try conditional edges first
    for edge in edges:
        cond = edge.get("condition", "")
        if cond and evaluator.evaluate(cond):
            return edge.get("to")

    # Fall through to unconditional default
    for edge in edges:
        if not edge.get("condition"):
            return edge.get("to")

    return edges[0].get("to") if edges else None


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run(directory: str):
    graph = Graph(directory)
    if not graph.start_node:
        print(f"Error: no start node found in {directory}")
        sys.exit(1)

    print(f"\n  Loaded {BOLD}{len(graph.nodes)}{RESET} nodes from {directory}")
    print(f"  Start:  {graph.start_node.id}\n")

    ticket = Ticket(graph)
    evaluator = Evaluator(ticket)

    while ticket.cursor:
        node = graph.get(ticket.cursor)
        if not node:
            print(f"\n  Error: unknown node '{ticket.cursor}'")
            break

        # Conditional skip
        if node.condition and not evaluator.evaluate(node.condition):
            ticket.cursor = next_node(node, None, evaluator)
            continue

        # Render
        print(render(ticket, graph))

        # Collect
        response = collect(node)
        if response is None:
            print("\n  Traversal cancelled.")
            break

        ticket.record(node.id, response)

        # Advance
        nxt = next_node(node, response, evaluator)
        if not nxt:
            # Terminal
            print(f"\n{BOLD}{'=' * 64}")
            print(f"  TRAVERSAL COMPLETE")
            print(f"{'=' * 64}{RESET}\n")
            print(f"  Collected responses:\n")
            for nid, resp, visit in ticket.history:
                tag = f" (#{visit})" if visit > 1 else ""
                print(f"    {BOLD}{nid}{tag}:{RESET} {_summarize(resp, 80)}")
            print()
            break

        ticket.cursor = nxt


def main():
    if len(sys.argv) < 2:
        print("Usage: python graph-viewer.py <graph-directory>")
        print("Example: python graph-viewer.py ./build-template/")
        sys.exit(1)

    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a directory")
        sys.exit(1)

    try:
        run(directory)
    except KeyboardInterrupt:
        print("\n\nExiting.")


if __name__ == "__main__":
    main()
