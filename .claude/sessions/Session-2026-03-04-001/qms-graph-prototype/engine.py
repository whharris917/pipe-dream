#!/usr/bin/env python3
"""
QMS Graph Engine - Core graph traversal engine with subgraph support.

This is the upgraded engine that supports:
- Multi-directory graph loading (subgraphs)
- Subgraph references (edges can point into other subgraphs)
- Performer switching (initiator, quality, reviewer, system)
- Gate conditions with blocking
- Automated test mode (non-interactive traversal)
- Ticket serialization to JSON
- Hook execution (simulated)
- Wait nodes (system-triggered transitions)
- Delegation (spawning child tickets for review/approval)
"""

import sys
import os
import json
import yaml
import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class NodeSchema:
    """Schema for a single evidence field."""
    type: str = "text"
    required: bool = False
    values: list = field(default_factory=list)
    hint: str = ""
    default: str = ""


class Node:
    """A single node in the graph."""

    def __init__(self, data, source_file, subgraph_id=""):
        node = data.get("node", data)
        raw_id = node["id"]
        self.id = raw_id
        self.subgraph = subgraph_id
        self.prompt = node.get("prompt", "")
        self.context = node.get("context", "")
        self.evidence_schema = node.get("evidence_schema", {}) or {}
        self.performer = node.get("performer", "initiator")
        self.condition = node.get("condition", None)
        self.edges = node.get("edges", []) or []
        self.hooks = node.get("hooks", {}) or {}
        self.wait = node.get("wait", None)  # For system-triggered nodes
        self.gate = node.get("gate", None)  # Pre-entry gate condition
        self.terminal = node.get("terminal", False)
        self.source_file = source_file

    def __repr__(self):
        return f"Node({self.id})"


class GraphMetadata:
    """Metadata from _graph.yaml files."""

    def __init__(self, data: dict = None):
        g = (data or {}).get("graph", data or {})
        self.id = g.get("id", "")
        self.name = g.get("name", "")
        self.version = g.get("version", "")
        self.entry_point = g.get("entry_point", "")
        self.description = g.get("description", "")
        self.invoked_by = g.get("invoked_by", [])
        self.invokes = g.get("invokes", [])
        self.performer_map = g.get("performer_map", {})
        self.reviewer_assignment_guide = g.get("reviewer_assignment_guide", {})


class Graph:
    """A collection of nodes loaded from one or more directories."""

    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self.subgraphs: dict[str, list[str]] = {}  # subgraph_id -> [node_ids]
        self.start_node: Optional[Node] = None
        self._primary_subgraph: str = ""
        self.metadata: Optional[GraphMetadata] = None

    def load_directory(self, directory: str, subgraph_id: str = ""):
        """Load all YAML files from a directory as a subgraph."""
        path = Path(directory)
        if not path.exists():
            raise FileNotFoundError(f"Graph directory not found: {directory}")

        # Load _graph.yaml metadata if present
        meta_file = path / "_graph.yaml"
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                meta_data = yaml.safe_load(f)
            meta = GraphMetadata(meta_data)
            if not self.metadata:
                self.metadata = meta

        node_ids = []
        for yaml_file in sorted(path.rglob("*.yaml")):
            if yaml_file.stem.startswith("_"):
                continue  # Skip metadata files
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data:
                continue
            node = Node(data, str(yaml_file), subgraph_id)
            if node.id in self.nodes:
                raise ValueError(f"Duplicate node ID: {node.id} (from {yaml_file})")
            self.nodes[node.id] = node
            node_ids.append(node.id)

            # Auto-detect start node
            if not subgraph_id or subgraph_id == self._primary_subgraph:
                if node.id.endswith(".start") or yaml_file.stem == "start":
                    if self.start_node is None:
                        self.start_node = node

        self.subgraphs[subgraph_id or "root"] = node_ids

        if not self._primary_subgraph:
            self._primary_subgraph = subgraph_id or "root"

        if self.start_node is None and self.nodes:
            self.start_node = next(iter(self.nodes.values()))

        return node_ids

    def get(self, node_id: str) -> Optional[Node]:
        return self.nodes.get(node_id)

    def get_subgraph_nodes(self, subgraph_id: str) -> list[Node]:
        ids = self.subgraphs.get(subgraph_id, [])
        return [self.nodes[nid] for nid in ids if nid in self.nodes]

    def validate(self) -> list[str]:
        """Validate graph integrity. Returns list of errors."""
        errors = []
        for nid, node in self.nodes.items():
            for edge in node.edges:
                target = edge.get("to", "")
                if target and target not in self.nodes:
                    errors.append(f"Node {nid}: edge points to unknown node '{target}'")
        if not self.start_node:
            errors.append("No start node found")
        # Check for unreachable nodes
        reachable = set()
        if self.start_node:
            self._walk(self.start_node.id, reachable)
        unreachable = set(self.nodes.keys()) - reachable
        for nid in unreachable:
            errors.append(f"Node {nid} is unreachable from start")
        return errors

    def _walk(self, node_id: str, visited: set):
        if node_id in visited:
            return
        visited.add(node_id)
        node = self.get(node_id)
        if node:
            for edge in node.edges:
                target = edge.get("to", "")
                if target:
                    self._walk(target, visited)


class Ticket:
    """A cursor riding on the graph, collecting responses."""

    def __init__(self, ticket_id: str, graph: Graph, start_node: str = ""):
        self.id = ticket_id
        self.graph = graph
        self.cursor: Optional[str] = start_node or (graph.start_node.id if graph.start_node else None)
        self.responses: dict[str, object] = {}
        self.history: list[dict] = []  # list of {node_id, response, visit, timestamp, performer}
        self._visit_count: dict[str, int] = {}
        self.state: str = "active"  # active, waiting, blocked, complete, cancelled
        self.blocked_reason: str = ""
        self.performer_log: list[dict] = []  # track who did what
        self.children: list[str] = []  # child ticket IDs
        self.parent: Optional[str] = None
        self.metadata: dict = {}
        self.created_at: str = time.strftime("%Y-%m-%dT%H:%M:%SZ")

    def record(self, node_id: str, response: object, performer: str = "initiator"):
        count = self._visit_count.get(node_id, 0) + 1
        self._visit_count[node_id] = count

        if count > 1:
            prev = self.responses.get(node_id)
            if prev is not None and not isinstance(prev, list):
                self.responses[node_id] = [prev]
            self.responses.setdefault(node_id, [])
            self.responses[node_id].append(response)
        else:
            self.responses[node_id] = response

        self.history.append({
            "node_id": node_id,
            "response": response,
            "visit": count,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "performer": performer,
        })

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "cursor": self.cursor,
            "state": self.state,
            "responses": self.responses,
            "history": self.history,
            "metadata": self.metadata,
            "children": self.children,
            "parent": self.parent,
            "created_at": self.created_at,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


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
        ns["ticket"] = self.ticket.metadata

        if self.ticket.history:
            last_resp = self.ticket.history[-1]["response"]
            ns["response"] = last_resp if isinstance(last_resp, dict) else last_resp

        ns["r"] = {}
        for nid, resp in self.ticket.responses.items():
            if isinstance(resp, dict):
                for k, v in resp.items():
                    ns["r"][f"{nid}.{k}"] = v

        # Expose visit counts for count-driven loops
        ns["visits"] = dict(self.ticket._visit_count)

        # Helper: count visits to target_node since the last visit to since_node
        def visits_since(target_node, since_node):
            count = 0
            for entry in reversed(self.ticket.history):
                if entry["node_id"] == since_node:
                    break
                if entry["node_id"] == target_node:
                    count += 1
            return count
        ns["visits_since"] = visits_since

        # Helper: get the most recent response for a node
        def last_response(node_id):
            resp = self.ticket.responses.get(node_id)
            if isinstance(resp, list):
                return resp[-1] if resp else {}
            return resp if resp is not None else {}
        ns["last_response"] = last_response

        # Safe builtins for conditions
        ns["int"] = int
        ns["str"] = str
        ns["len"] = len
        ns["bool"] = bool

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
RED = "\033[31m"
MAGENTA = "\033[35m"


def _summarize(response: object, max_len: int = 65) -> str:
    if isinstance(response, dict):
        parts = [f"{k}: {v}" for k, v in response.items() if not str(k).startswith("_")]
        s = ", ".join(parts)
    elif isinstance(response, list):
        s = f"[{len(response)} entries]"
    else:
        s = str(response)
    return (s[:max_len - 3] + "...") if len(s) > max_len else s


def render(ticket: Ticket, graph: Graph, title: str = "QMS Graph") -> str:
    node = graph.get(ticket.cursor)
    if not node:
        return f"  ERROR: cursor at unknown node '{ticket.cursor}'"

    lines: list[str] = []
    w = 72

    # Header
    lines.append("")
    lines.append(f"{BOLD}{'=' * w}")
    lines.append(f"  {title}")
    lines.append(f"  Ticket: {ticket.id}  |  Cursor: {node.id}  |  State: {ticket.state}")
    if node.performer != "initiator":
        lines.append(f"  Performer: {MAGENTA}{node.performer}{RESET}{BOLD}")
    lines.append(f"{'=' * w}{RESET}")
    lines.append("")

    # Completed steps (show last 8 to avoid scroll)
    visible_history = ticket.history[-8:] if len(ticket.history) > 8 else ticket.history
    if len(ticket.history) > 8:
        lines.append(f"  {DIM}... ({len(ticket.history) - 8} earlier steps){RESET}")
        lines.append("")
    for entry in visible_history:
        nid = entry["node_id"]
        resp = entry["response"]
        visit = entry["visit"]
        perf = entry.get("performer", "")
        n = graph.get(nid)
        label = n.prompt[:44] if n else nid
        visit_tag = f" (#{visit})" if visit > 1 else ""
        perf_tag = f" [{perf}]" if perf and perf != "initiator" else ""
        summary = _summarize(resp)
        lines.append(f"  {GREEN}[done]{RESET} {DIM}{label}{visit_tag}{perf_tag}{RESET}")
        lines.append(f"         {DIM}{summary}{RESET}")
        lines.append("")

    # Blocked indicator
    if ticket.state == "blocked":
        lines.append(f"  {RED}{BOLD}BLOCKED: {ticket.blocked_reason}{RESET}")
        lines.append("")

    # Active node
    lines.append(f"  {YELLOW}{BOLD}> [active]  {node.prompt}{RESET}")
    if node.context:
        # Wrap long context
        ctx_lines = _wrap(node.context, w - 16)
        for cl in ctx_lines:
            lines.append(f"  {CYAN}            {cl}{RESET}")
    lines.append("")

    # Gate (if any)
    if node.gate:
        lines.append(f"  {RED}Gate: {node.gate}{RESET}")
        lines.append("")

    # Evidence schema
    if node.evidence_schema:
        lines.append(f"  {WHITE}Evidence needed:{RESET}")
        for fname, fschema in node.evidence_schema.items():
            if isinstance(fschema, str):
                fschema = {"type": fschema}
            ftype = fschema.get("type", "text")
            req = " (required)" if fschema.get("required") else " (optional)"
            vals = fschema.get("values", [])
            hint = fschema.get("hint", "")
            default = fschema.get("default", "")
            if vals:
                type_label = f"[{' | '.join(str(v) for v in vals)}]"
            else:
                type_label = f"[{ftype}]"
            line = f"    {BOLD}{fname}{RESET} {type_label}{req}"
            if default:
                line += f"  {DIM}default={default}{RESET}"
            if hint:
                line += f"  {DIM}— {hint}{RESET}"
            lines.append(line)
        lines.append("")

    # Peek at next (only for simple linear paths)
    if len(node.edges) == 1 and not node.edges[0].get("condition"):
        nxt = graph.get(node.edges[0]["to"])
        if nxt:
            lines.append(f"  {DIM}[next]    {nxt.prompt[:50]}{RESET}")
            lines.append("")
    elif len(node.edges) > 1:
        cond_count = sum(1 for e in node.edges if e.get("condition"))
        if cond_count > 0:
            lines.append(f"  {DIM}[branches] {len(node.edges)} possible paths{RESET}")
            lines.append("")

    # Hooks
    for hook_phase, hook_data in node.hooks.items():
        hook_list = hook_data if isinstance(hook_data, list) else [hook_data]
        for h in hook_list:
            if isinstance(h, str):
                lines.append(f"  {DIM}Hook ({hook_phase}): {h}{RESET}")
            else:
                cmd = h.get("command", "")
                if cmd:
                    fail = h.get("on_failure", "")
                    tag = f" (on_failure: {fail})" if fail else ""
                    lines.append(f"  {DIM}Hook ({hook_phase}): {cmd}{tag}{RESET}")
        lines.append("")

    lines.append(f"{'-' * w}")
    return "\n".join(lines)


def _wrap(text: str, width: int) -> list[str]:
    """Simple word-wrap."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if current and len(current) + 1 + len(word) > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}" if current else word
    if current:
        lines.append(current)
    return lines


# ---------------------------------------------------------------------------
# Input collection
# ---------------------------------------------------------------------------

def collect(node: Node) -> Optional[dict]:
    """Prompt the user for each field in the evidence schema."""
    schema = node.evidence_schema
    if not schema:
        try:
            input(f"  {DIM}Press Enter to continue...{RESET}")
        except (EOFError, KeyboardInterrupt):
            return None
        return {"_ack": True}

    response: dict = {}
    for fname, fschema in schema.items():
        if isinstance(fschema, str):
            fschema = {"type": fschema}
        ftype = fschema.get("type", "text")
        required = fschema.get("required", False)
        required_when = fschema.get("required_when", "")
        values = fschema.get("values", [])
        default = fschema.get("default", "")

        # Evaluate conditional required against already-collected fields
        if required_when and not required:
            try:
                required = bool(eval(required_when, {"__builtins__": {}}, response))
            except Exception:
                pass

        while True:
            if values:
                prompt_text = f"  {BOLD}{fname}{RESET} [{' / '.join(str(v) for v in values)}]: "
            elif default:
                prompt_text = f"  {BOLD}{fname}{RESET} [{default}]: "
            else:
                prompt_text = f"  {BOLD}{fname}{RESET}: "

            try:
                raw = input(prompt_text).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return None

            if not raw and default:
                raw = default
            if not raw and not required:
                break
            if not raw:
                print(f"    {DIM}(required){RESET}")
                continue

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
            elif ftype == "doc_id":
                response[fname] = raw
                break
            else:
                response[fname] = raw
                break

    return response


# ---------------------------------------------------------------------------
# Edge resolution
# ---------------------------------------------------------------------------

def next_node(node: Node, response: object, evaluator: Evaluator) -> Optional[str]:
    """Pick the outgoing edge to follow."""
    edges = node.edges
    if not edges:
        return None

    if len(edges) == 1 and not edges[0].get("condition"):
        return edges[0].get("to")

    for edge in edges:
        cond = edge.get("condition", "")
        if cond and evaluator.evaluate(cond):
            return edge.get("to")

    for edge in edges:
        if not edge.get("condition"):
            return edge.get("to")

    return edges[0].get("to") if edges else None


# ---------------------------------------------------------------------------
# Automated test runner
# ---------------------------------------------------------------------------

class AutoRunner:
    """Runs through a graph automatically with scripted responses."""

    def __init__(self, graph: Graph, responses: list[dict], ticket_id: str = "auto-001",
                 skip_gates: bool = True):
        self.graph = graph
        self.scripted = list(responses)  # copy
        self.ticket = Ticket(ticket_id, graph)
        self.evaluator = Evaluator(self.ticket)
        self.log: list[str] = []
        self.errors: list[str] = []
        self.skip_gates = skip_gates  # Gates check external state; skip in test mode

    def run(self) -> dict:
        """Execute the graph with scripted responses. Returns result dict."""
        step = 0
        max_steps = 200  # safety limit

        while self.ticket.cursor and step < max_steps:
            step += 1
            node = self.graph.get(self.ticket.cursor)
            if not node:
                self.errors.append(f"Step {step}: unknown node '{self.ticket.cursor}'")
                break

            # Gate check (skipped in test mode — gates verify external system state)
            if node.gate and not self.skip_gates:
                if not self.evaluator.evaluate(node.gate):
                    self.errors.append(f"Step {step}: gate blocked at {node.id}: {node.gate}")
                    self.ticket.state = "blocked"
                    self.ticket.blocked_reason = node.gate
                    break

            # Conditional skip
            if node.condition and not self.evaluator.evaluate(node.condition):
                self.ticket.cursor = next_node(node, None, self.evaluator)
                continue

            # Get scripted response
            if node.evidence_schema:
                if not self.scripted:
                    self.errors.append(f"Step {step}: ran out of scripted responses at {node.id}")
                    break
                response = self.scripted.pop(0)
            else:
                response = {"_ack": True}

            # Validate response against schema
            schema_errors = self._validate(node, response)
            if schema_errors:
                self.errors.extend([f"Step {step} ({node.id}): {e}" for e in schema_errors])

            self.log.append(f"[{step}] {node.id} ({node.performer}): {_summarize(response)}")
            self.ticket.record(node.id, response, node.performer)

            # Advance
            nxt = next_node(node, response, self.evaluator)
            if not nxt:
                self.ticket.state = "complete"
                break
            self.ticket.cursor = nxt

        if step >= max_steps:
            self.errors.append(f"Hit max step limit ({max_steps})")

        return {
            "steps": step,
            "state": self.ticket.state,
            "errors": self.errors,
            "log": self.log,
            "responses": self.ticket.responses,
            "ticket": self.ticket.to_dict(),
        }

    def _validate(self, node: Node, response: dict) -> list[str]:
        """Validate a response against the node's evidence schema."""
        errors = []
        for fname, fschema in node.evidence_schema.items():
            if isinstance(fschema, str):
                fschema = {"type": fschema}
            required = fschema.get("required", False)
            required_when = fschema.get("required_when", "")
            ftype = fschema.get("type", "text")
            values = fschema.get("values", [])

            # Evaluate conditional required
            is_required = required
            if required_when and not required:
                is_required = self._eval_required_when(required_when, response)

            if is_required and fname not in response:
                errors.append(f"Missing required field '{fname}'")
                continue

            if fname in response:
                val = response[fname]
                if ftype == "enum" and values:
                    if str(val) not in [str(v) for v in values]:
                        errors.append(f"Field '{fname}': '{val}' not in {values}")
                elif ftype == "bool":
                    if not isinstance(val, bool):
                        errors.append(f"Field '{fname}': expected bool, got {type(val).__name__}")
                elif ftype == "integer":
                    if not isinstance(val, int):
                        errors.append(f"Field '{fname}': expected int, got {type(val).__name__}")
        return errors

    def _eval_required_when(self, expression: str, response: dict) -> bool:
        """Evaluate a required_when condition against the current response."""
        try:
            return bool(eval(expression, {"__builtins__": {}}, response))
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Graph loader helper
# ---------------------------------------------------------------------------

def load_graph(*directories: str) -> Graph:
    """Load a graph from one or more directories."""
    graph = Graph()
    for i, d in enumerate(directories):
        subgraph_id = Path(d).stem if i > 0 else ""
        graph.load_directory(d, subgraph_id)
    return graph


# ---------------------------------------------------------------------------
# Graph map visualization
# ---------------------------------------------------------------------------

def render_map(graph: Graph, ticket: Ticket = None, use_color: bool = True) -> str:
    """Render a visual map of the graph showing topology and cursor position.

    Uses DFS to lay out nodes, showing:
    - Completed nodes (green checkmark)
    - Current cursor position (yellow arrow)
    - Upcoming nodes (dim)
    - Branch points with conditions
    - Loop-back edges
    - Hooks, gates, waits, performer switches
    """
    if not use_color:
        c_reset = c_bold = c_dim = c_green = c_yellow = c_cyan = c_red = c_magenta = ""
    else:
        c_reset, c_bold, c_dim = RESET, BOLD, DIM
        c_green, c_yellow, c_cyan = GREEN, YELLOW, CYAN
        c_red, c_magenta = RED, MAGENTA

    visited_nodes = set()
    if ticket:
        for entry in ticket.history:
            visited_nodes.add(entry["node_id"])

    cursor = ticket.cursor if ticket else None
    lines = []
    seen = set()
    back_edges = []  # (from_id, to_id, condition) for loops

    def _node_label(node: Node) -> str:
        """Short label: just the last part of the dotted ID."""
        parts = node.id.split(".")
        return parts[-1] if len(parts) > 1 else node.id

    def _status_marker(node: Node) -> str:
        if node.id == cursor:
            return f"{c_yellow}{c_bold}>>>{c_reset}"
        elif node.id in visited_nodes:
            return f"{c_green} + {c_reset}"
        else:
            return f"{c_dim} . {c_reset}"

    def _annotations(node: Node) -> list[str]:
        """Small inline annotations for special node properties."""
        tags = []
        if node.performer not in ("initiator",):
            tags.append(f"[{node.performer}]")
        if node.hooks:
            phases = list(node.hooks.keys())
            tags.append(f"hooks:{','.join(phases)}")
        if node.wait:
            tags.append("WAIT")
        if node.gate:
            tags.append("GATE")
        if node.terminal:
            tags.append("END")
        return tags

    def _walk(node_id: str, indent: int, branch_prefix: str = ""):
        if node_id not in graph.nodes:
            lines.append(f"{'  ' * indent}  {c_red}??? {node_id} (missing){c_reset}")
            return
        if node_id in seen:
            # Back-edge: this is a loop
            lines.append(f"{'  ' * indent}  {c_cyan}^ loop back to {node_id}{c_reset}")
            return

        seen.add(node_id)
        node = graph.nodes[node_id]
        marker = _status_marker(node)
        label = _node_label(node)
        prompt_short = node.prompt[:52]
        annot = _annotations(node)
        annot_str = f"  {c_dim}{' '.join(annot)}{c_reset}" if annot else ""

        # Color the label based on state
        if node.id == cursor:
            label_str = f"{c_yellow}{c_bold}{label}{c_reset}"
            prompt_str = f"{c_yellow}{prompt_short}{c_reset}"
        elif node.id in visited_nodes:
            label_str = f"{c_green}{label}{c_reset}"
            prompt_str = f"{c_dim}{prompt_short}{c_reset}"
        else:
            label_str = f"{c_bold}{label}{c_reset}"
            prompt_str = f"{c_dim}{prompt_short}{c_reset}"

        pad = "  " * indent
        bp = branch_prefix
        lines.append(f"{pad}{bp}{marker} {label_str}  {prompt_str}{annot_str}")

        edges = node.edges
        if not edges:
            return

        # Single unconditional edge: continue linear
        if len(edges) == 1 and not edges[0].get("condition"):
            target = edges[0].get("to", "")
            connector = f"{'  ' * indent}  {c_dim}|{c_reset}"
            lines.append(connector)
            _walk(target, indent)
            return

        # Multiple edges: show branch
        lines.append(f"{'  ' * indent}  {c_dim}|{c_reset}")
        for i, edge in enumerate(edges):
            target = edge.get("to", "")
            cond = edge.get("condition", "")
            is_last = (i == len(edges) - 1)
            branch_char = "`--" if is_last else "|--"

            if cond:
                cond_short = cond
                # Shorten common patterns
                cond_short = cond_short.replace("response.get(", "").replace(")", "").replace("'", "")
                lines.append(f"{'  ' * indent}  {c_dim}{branch_char} {c_cyan}if {cond_short}{c_reset}")
            else:
                lines.append(f"{'  ' * indent}  {c_dim}{branch_char} (default){c_reset}")

            # Check if target is a back-edge before recursing
            if target in seen:
                lines.append(f"{'  ' * (indent + 1)}  {c_cyan}^ loop back to {target}{c_reset}")
            else:
                _walk(target, indent + 1)

            if not is_last:
                lines.append(f"{'  ' * indent}  {c_dim}|{c_reset}")

    # Header
    w = 72
    title = graph.metadata.name if graph.metadata and graph.metadata.name else "Graph Map"
    lines.append("")
    lines.append(f"{c_bold}{'=' * w}")
    lines.append(f"  {title}")
    if ticket:
        progress = len(visited_nodes)
        total = len(graph.nodes)
        pct = int(progress / total * 100) if total else 0
        state_str = ticket.state
        lines.append(f"  Ticket: {ticket.id}  |  Progress: {progress}/{total} ({pct}%)  |  State: {state_str}")
    lines.append(f"{'=' * w}{c_reset}")
    lines.append("")

    # Legend
    lines.append(f"  {c_green} + {c_reset} completed    {c_yellow}{c_bold}>>>{c_reset} you are here    {c_dim} . {c_reset} upcoming")
    lines.append("")

    # Walk from start
    if graph.start_node:
        _walk(graph.start_node.id, 1)
    else:
        lines.append(f"  {c_red}No start node found{c_reset}")

    lines.append("")
    return "\n".join(lines)


def _graph_to_json(graph: Graph, ticket: Ticket = None) -> dict:
    """Machine-readable graph structure for programmatic consumption."""
    visited = set()
    if ticket:
        for entry in ticket.history:
            visited.add(entry["node_id"])

    nodes = {}
    for nid, node in graph.nodes.items():
        status = "current" if (ticket and nid == ticket.cursor) else \
                 "completed" if nid in visited else "pending"
        nodes[nid] = {
            "id": nid,
            "prompt": node.prompt,
            "performer": node.performer,
            "terminal": node.terminal,
            "status": status,
            "has_hooks": bool(node.hooks),
            "has_gate": bool(node.gate),
            "has_wait": bool(node.wait),
            "edges": [{"to": e.get("to", ""), "condition": e.get("condition", "")} for e in node.edges],
        }

    result = {
        "name": graph.metadata.name if graph.metadata else "",
        "total_nodes": len(graph.nodes),
        "start_node": graph.start_node.id if graph.start_node else None,
        "nodes": nodes,
    }
    if ticket:
        result["ticket_id"] = ticket.id
        result["cursor"] = ticket.cursor
        result["state"] = ticket.state
        result["completed"] = len(visited)
        result["progress_pct"] = int(len(visited) / len(graph.nodes) * 100) if graph.nodes else 0

    return result


# ---------------------------------------------------------------------------
# Step-at-a-time API (for AI agents)
# ---------------------------------------------------------------------------

class StepEngine:
    """Non-interactive engine for AI agent consumption.

    Each method call is stateless from the caller's perspective.
    All state lives in the Ticket, which is persisted to disk between calls.
    """

    def __init__(self, graph: Graph, ticket: Ticket):
        self.graph = graph
        self.ticket = ticket
        self.evaluator = Evaluator(ticket)

    # -- Queries --

    def status(self) -> dict:
        """Return the current node as structured data, plus lookahead."""
        if self.ticket.state in ("complete", "cancelled"):
            return {
                "state": self.ticket.state,
                "cursor": self.ticket.cursor,
                "steps_completed": len(self.ticket.history),
                "node": None,
                "lookahead": [],
            }

        node = self.graph.get(self.ticket.cursor)
        if not node:
            return {"error": f"Unknown node '{self.ticket.cursor}'", "state": "error"}

        return {
            "state": self.ticket.state,
            "cursor": node.id,
            "steps_completed": len(self.ticket.history),
            "node": self._node_to_dict(node),
            "lookahead": self._lookahead(node),
        }

    def _node_to_dict(self, node: Node) -> dict:
        """Serialize a node for agent consumption."""
        d = {
            "id": node.id,
            "prompt": node.prompt,
            "context": node.context,
            "performer": node.performer,
            "terminal": node.terminal,
        }
        if node.evidence_schema:
            d["evidence_schema"] = node.evidence_schema
        if node.gate:
            d["gate"] = node.gate
        if node.wait:
            d["wait"] = node.wait
        if node.hooks:
            d["hooks"] = node.hooks
        if node.edges:
            d["edges"] = [
                {"to": e.get("to", ""), "condition": e.get("condition", "")}
                for e in node.edges
            ]
        return d

    def _is_batchable(self, node: Node) -> bool:
        """Can this node be included in a batch submission?

        A node is batchable if:
        - No hooks (hooks have side effects that need sequential execution)
        - No wait (system-triggered pause)
        - No gate (external condition check)
        - No conditional edges (decisions that depend on this node's response)
        - Not a performer switch (different agent needed)
        """
        if node.hooks:
            return False
        if node.wait:
            return False
        if node.gate:
            return False
        if node.terminal:
            return False
        # Check for conditional edges (decision points)
        if len(node.edges) > 1:
            has_conditions = any(e.get("condition") for e in node.edges)
            if has_conditions:
                return False
        # Performer switches break the batch
        current = self.graph.get(self.ticket.cursor)
        if current and node.performer != current.performer:
            return False
        return True

    def _lookahead(self, from_node: Node) -> list[dict]:
        """Return the linear sequence of batchable nodes after from_node."""
        ahead = []
        seen = set()
        cursor = from_node

        while True:
            # Follow the single unconditional edge
            if len(cursor.edges) != 1:
                break
            if cursor.edges[0].get("condition"):
                break

            next_id = cursor.edges[0].get("to", "")
            if not next_id or next_id in seen:
                break
            seen.add(next_id)

            nxt = self.graph.get(next_id)
            if not nxt:
                break
            if not self._is_batchable(nxt):
                # Include it in lookahead for visibility but mark it non-batchable
                ahead.append({**self._node_to_dict(nxt), "batchable": False})
                break

            ahead.append({**self._node_to_dict(nxt), "batchable": True})
            cursor = nxt

        return ahead

    # -- Mutations --

    def respond(self, responses: "dict | list[dict]") -> dict:
        """Submit response(s) and advance the cursor.

        Args:
            responses: A single response dict for the current node,
                       or a list of response dicts for batch submission.
                       For batch: responses are consumed in order, one per node.

        Returns:
            Dict with: advanced (list of nodes traversed), status (current state),
                       errors (any validation errors), stopped_reason (why batch stopped)
        """
        if isinstance(responses, dict):
            responses = [responses]

        advanced = []
        errors = []
        stopped_reason = None

        for i, response in enumerate(responses):
            node = self.graph.get(self.ticket.cursor)
            if not node:
                errors.append(f"Unknown node '{self.ticket.cursor}'")
                stopped_reason = "unknown_node"
                break

            # Gate check
            if node.gate:
                if not self.evaluator.evaluate(node.gate):
                    self.ticket.state = "blocked"
                    self.ticket.blocked_reason = node.gate
                    stopped_reason = "gate_blocked"
                    break

            # Wait node
            if node.wait:
                stopped_reason = "wait_node"
                # Allow the response to satisfy the wait
                if not response.get("_wait_satisfied") and not node.evidence_schema:
                    break

            # Validate response against schema
            schema_errors = self._validate(node, response)
            if schema_errors:
                errors.extend(schema_errors)
                stopped_reason = "validation_error"
                break

            # Execute hooks (on_enter already happened, run on_exit)
            hook_results = self._run_hooks(node, "on_exit", response)
            if hook_results.get("blocked"):
                errors.append(f"Hook blocked at {node.id}: {hook_results['error']}")
                stopped_reason = "hook_blocked"
                break

            # Record and advance
            self.ticket.record(node.id, response, node.performer)
            advanced.append({"node_id": node.id, "response": response})

            nxt = next_node(node, response, self.evaluator)
            if not nxt:
                self.ticket.state = "complete"
                stopped_reason = "complete"
                break
            self.ticket.cursor = nxt

            # For batch: check if next node is batchable before consuming next response
            if i < len(responses) - 1:
                next_n = self.graph.get(nxt)
                if next_n and not self._is_batchable(next_n):
                    stopped_reason = "not_batchable"
                    break

        return {
            "advanced": advanced,
            "status": self.status(),
            "errors": errors,
            "stopped_reason": stopped_reason,
        }

    def _validate(self, node: Node, response: dict) -> list[str]:
        """Validate response against node schema."""
        errors = []
        for fname, fschema in node.evidence_schema.items():
            if isinstance(fschema, str):
                fschema = {"type": fschema}
            required = fschema.get("required", False)
            required_when = fschema.get("required_when", "")
            ftype = fschema.get("type", "text")
            values = fschema.get("values", [])

            is_required = required
            if required_when and not required:
                try:
                    is_required = bool(eval(required_when, {"__builtins__": {}}, response))
                except Exception:
                    pass

            if is_required and fname not in response:
                errors.append(f"Missing required field '{fname}'")
                continue

            if fname in response:
                val = response[fname]
                if ftype == "enum" and values:
                    if str(val) not in [str(v) for v in values]:
                        errors.append(f"Field '{fname}': '{val}' not in {values}")
                elif ftype == "bool":
                    if not isinstance(val, bool):
                        errors.append(f"Field '{fname}': expected bool, got {type(val).__name__}")
                elif ftype == "integer":
                    if not isinstance(val, int):
                        errors.append(f"Field '{fname}': expected int, got {type(val).__name__}")
        return errors

    def _run_hooks(self, node: Node, phase: str, response: dict) -> dict:
        """Simulate hook execution. Returns {blocked: bool, error: str}."""
        hooks = node.hooks.get(phase, [])
        if not hooks:
            return {"blocked": False}
        if not isinstance(hooks, list):
            hooks = [hooks]
        for h in hooks:
            if isinstance(h, dict) and h.get("on_failure") == "block":
                # In real engine, this would execute the command.
                # For now, hooks always succeed in prototype.
                pass
        return {"blocked": False}


# -- Ticket persistence --

def save_ticket(ticket: Ticket, path: str):
    """Save ticket state to a JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ticket.to_dict(), f, indent=2, default=str)


def load_ticket(path: str, graph: Graph) -> Ticket:
    """Load ticket state from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    ticket = Ticket(data["id"], graph, data.get("cursor", ""))
    ticket.responses = data.get("responses", {})
    ticket.history = data.get("history", [])
    ticket.state = data.get("state", "active")
    ticket.metadata = data.get("metadata", {})
    ticket.children = data.get("children", [])
    ticket.parent = data.get("parent")
    ticket.created_at = data.get("created_at", "")
    # Rebuild visit counts from history
    for entry in ticket.history:
        nid = entry["node_id"]
        ticket._visit_count[nid] = ticket._visit_count.get(nid, 0) + 1
    return ticket


# ---------------------------------------------------------------------------
# Interactive runner
# ---------------------------------------------------------------------------

def run_interactive(graph: Graph, title: str = "QMS Graph", ticket_id: str = "ticket-001"):
    """Run interactive traversal."""
    ticket = Ticket(ticket_id, graph)
    evaluator = Evaluator(ticket)

    while ticket.cursor:
        node = graph.get(ticket.cursor)
        if not node:
            print(f"\n  Error: unknown node '{ticket.cursor}'")
            break

        # Gate check
        if node.gate:
            if not evaluator.evaluate(node.gate):
                print(f"\n  {RED}{BOLD}GATE BLOCKED:{RESET} {node.gate}")
                print(f"  Cannot proceed until gate condition is satisfied.")
                ticket.state = "blocked"
                ticket.blocked_reason = node.gate
                break

        # Conditional skip
        if node.condition and not evaluator.evaluate(node.condition):
            ticket.cursor = next_node(node, None, evaluator)
            continue

        # Render
        print(render(ticket, graph, title))

        # Wait node (system-triggered)
        if node.wait:
            print(f"  {MAGENTA}SYSTEM WAIT: {node.wait}{RESET}")
            print(f"  {DIM}In production, the cursor pauses here until the system resolves this.{RESET}")
            print(f"  {DIM}For this demo, you will simulate the system's outcome below.{RESET}")
            print()
            # If the wait node has evidence_schema, the agent reports the system outcome
            if node.evidence_schema:
                response = collect(node)
                if response is None:
                    print("\n  Traversal cancelled.")
                    break
            else:
                try:
                    input(f"  {DIM}Press Enter to simulate condition being met...{RESET}")
                except (EOFError, KeyboardInterrupt):
                    print("\n  Traversal cancelled.")
                    break
                response = {"_wait_satisfied": True}
            response["_condition"] = node.wait
            ticket.record(node.id, response, "system")
            nxt = next_node(node, response, evaluator)
            if not nxt:
                ticket.state = "complete"
                break
            ticket.cursor = nxt
            continue

        # Performer check
        if node.performer not in ("initiator", "system"):
            print(f"  {MAGENTA}{BOLD}This step requires: {node.performer}{RESET}")
            print(f"  {DIM}(In production, a different agent handles this){RESET}")

        # Collect
        response = collect(node)
        if response is None:
            print("\n  Traversal cancelled.")
            ticket.state = "cancelled"
            break

        ticket.record(node.id, response, node.performer)

        # Simulate hooks
        for phase in ("on_exit",):
            if phase in node.hooks:
                hooks = node.hooks[phase]
                if isinstance(hooks, list):
                    for h in hooks:
                        cmd = h.get("command", h) if isinstance(h, dict) else h
                        print(f"  {DIM}[hook] {cmd}{RESET}")
                elif isinstance(hooks, dict):
                    cmd = hooks.get("command", "")
                    print(f"  {DIM}[hook] {cmd}{RESET}")

        # Advance
        nxt = next_node(node, response, evaluator)
        if not nxt:
            ticket.state = "complete"
            _print_summary(ticket, graph)
            break
        ticket.cursor = nxt

    return ticket


def _print_summary(ticket: Ticket, graph: Graph):
    w = 72
    print(f"\n{BOLD}{'=' * w}")
    print(f"  TRAVERSAL COMPLETE — {ticket.id}")
    print(f"{'=' * w}{RESET}\n")
    print(f"  Steps: {len(ticket.history)}  |  State: {ticket.state}\n")
    for entry in ticket.history:
        nid = entry["node_id"]
        resp = entry["response"]
        visit = entry["visit"]
        perf = entry.get("performer", "")
        tag = f" (#{visit})" if visit > 1 else ""
        perf_tag = f" [{perf}]" if perf and perf != "initiator" else ""
        print(f"    {BOLD}{nid}{tag}{perf_tag}:{RESET} {_summarize(resp, 80)}")
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="QMS Graph Engine")
    subparsers = parser.add_subparsers(dest="command")

    # Legacy / default: interactive mode
    interact_p = subparsers.add_parser("interactive", aliases=["i"], help="Interactive traversal (human)")
    interact_p.add_argument("directories", nargs="+", help="Graph directories to load")
    interact_p.add_argument("--title", default="QMS Graph")
    interact_p.add_argument("--ticket", default="ticket-001")
    interact_p.add_argument("--dump", help="Dump ticket to JSON file after traversal")

    # Validate
    validate_p = subparsers.add_parser("validate", help="Validate graph integrity")
    validate_p.add_argument("directories", nargs="+")

    # Auto (test mode)
    auto_p = subparsers.add_parser("auto", help="Automated run with scripted responses")
    auto_p.add_argument("directories", nargs="+")
    auto_p.add_argument("--responses", required=True, help="JSON file with scripted responses")
    auto_p.add_argument("--ticket", default="auto-001")
    auto_p.add_argument("--dump", help="Dump ticket to JSON file")

    # Map: visualize graph topology with optional ticket position
    map_p = subparsers.add_parser("map", help="Visualize graph topology with cursor position")
    map_p.add_argument("directories", nargs="+")
    map_p.add_argument("--ticket-file", help="Path to ticket JSON to show position on map")
    map_p.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    map_p.add_argument("--json", action="store_true", help="Output graph structure as JSON")

    # --- Step API (for AI agents) ---

    # Start: create a new ticket and return initial status
    start_p = subparsers.add_parser("start", help="Create a new ticket on a graph")
    start_p.add_argument("directories", nargs="+")
    start_p.add_argument("--ticket", default="ticket-001")
    start_p.add_argument("--ticket-dir", default=".tickets", help="Directory to store ticket state")

    # Status: get current node + lookahead
    status_p = subparsers.add_parser("status", help="Get current node and lookahead")
    status_p.add_argument("directories", nargs="+")
    status_p.add_argument("--ticket-file", required=True, help="Path to ticket JSON file")

    # Respond: submit response(s) and advance
    respond_p = subparsers.add_parser("respond", help="Submit response(s) and advance cursor")
    respond_p.add_argument("directories", nargs="+")
    respond_p.add_argument("--ticket-file", required=True, help="Path to ticket JSON file")
    resp_group = respond_p.add_mutually_exclusive_group(required=True)
    resp_group.add_argument("--response", help="JSON string or @file with response(s)")
    resp_group.add_argument("--response-file", help="Path to JSON file containing response(s)")

    # History: review all evidence collected so far
    history_p = subparsers.add_parser("history", help="Show all evidence collected in a ticket")
    history_p.add_argument("directories", nargs="+")
    history_p.add_argument("--ticket-file", required=True, help="Path to ticket JSON file")
    history_p.add_argument("--json", action="store_true", help="Output as JSON instead of human-readable")

    args = parser.parse_args()

    # Backward compatibility: if no subcommand, treat positional args as directories for interactive mode
    if args.command is None:
        # Check if there are remaining args that look like directories
        remaining = sys.argv[1:]
        if remaining:
            args.command = "interactive"
            args.directories = remaining
            args.title = "QMS Graph"
            args.ticket = "ticket-001"
            args.dump = None
        else:
            parser.print_help()
            sys.exit(1)

    # --- Load graph (common to all commands) ---
    graph = load_graph(*args.directories)

    # === VALIDATE ===
    if args.command == "validate":
        errors = graph.validate()
        if errors:
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
            sys.exit(1)
        print(json.dumps({"valid": True, "nodes": len(graph.nodes)}))
        sys.exit(0)

    # === MAP ===
    if args.command == "map":
        ticket = None
        if hasattr(args, 'ticket_file') and args.ticket_file:
            ticket = load_ticket(args.ticket_file, graph)

        if hasattr(args, 'json') and args.json:
            # Machine-readable graph structure
            map_data = _graph_to_json(graph, ticket)
            print(json.dumps(map_data, indent=2, default=str))
        else:
            use_color = not (hasattr(args, 'no_color') and args.no_color)
            print(render_map(graph, ticket, use_color=use_color))
        sys.exit(0)

    # === AUTO ===
    if args.command == "auto":
        with open(args.responses, "r") as f:
            scripted = json.load(f)
        runner = AutoRunner(graph, scripted, args.ticket)
        result = runner.run()
        print(f"  AutoRun: {result['steps']} steps, state={result['state']}")
        if result["errors"]:
            for e in result["errors"]:
                print(f"    - {e}")
        for entry in result["log"]:
            print(f"    {entry}")
        if args.dump:
            with open(args.dump, "w") as f:
                json.dump(result["ticket"], f, indent=2, default=str)
        sys.exit(1 if result["errors"] else 0)

    # === INTERACTIVE ===
    if args.command in ("interactive", "i"):
        print(f"\n  Loaded {BOLD}{len(graph.nodes)}{RESET} nodes from {len(args.directories)} directory(ies)")
        if graph.start_node:
            print(f"  Start:  {graph.start_node.id}")
        print()
        if graph.metadata:
            m = graph.metadata
            if m.name:
                print(f"  Graph: {BOLD}{m.name}{RESET} (v{m.version})")
            if m.description:
                print(f"  {DIM}{m.description.strip()[:120]}{RESET}")
            if m.invokes:
                for inv in m.invokes:
                    print(f"  {DIM}Invokes: {inv.get('graph','')} -- {inv.get('trigger','')}{RESET}")
            if m.reviewer_assignment_guide:
                print(f"  {DIM}Reviewer guide: {', '.join(f'{k}->{v}' for k,v in m.reviewer_assignment_guide.items())}{RESET}")
            print()
        try:
            ticket = run_interactive(graph, args.title, args.ticket)
            if args.dump:
                with open(args.dump, "w") as f:
                    f.write(ticket.to_json())
        except KeyboardInterrupt:
            print("\n\nExiting.")
        sys.exit(0)

    # === START ===
    if args.command == "start":
        ticket_dir = Path(args.ticket_dir)
        ticket_dir.mkdir(parents=True, exist_ok=True)
        ticket_path = ticket_dir / f"{args.ticket}.json"

        ticket = Ticket(args.ticket, graph)
        engine = StepEngine(graph, ticket)
        result = engine.status()
        save_ticket(ticket, str(ticket_path))

        result["ticket_file"] = str(ticket_path).replace("\\", "/")
        print(json.dumps(result, indent=2, default=str))
        sys.exit(0)

    # === STATUS ===
    if args.command == "status":
        ticket = load_ticket(args.ticket_file, graph)
        engine = StepEngine(graph, ticket)
        result = engine.status()
        print(json.dumps(result, indent=2, default=str))
        sys.exit(0)

    # === RESPOND ===
    if args.command == "respond":
        ticket = load_ticket(args.ticket_file, graph)
        engine = StepEngine(graph, ticket)

        # Parse response: --response-file takes priority, then --response
        if hasattr(args, 'response_file') and args.response_file:
            with open(args.response_file, "r", encoding="utf-8") as f:
                responses = json.load(f)
        else:
            resp_arg = args.response
            if resp_arg.startswith("@"):
                with open(resp_arg[1:], "r", encoding="utf-8") as f:
                    responses = json.load(f)
            else:
                responses = json.loads(resp_arg)

        result = engine.respond(responses)
        save_ticket(ticket, args.ticket_file)

        print(json.dumps(result, indent=2, default=str))
        sys.exit(1 if result["errors"] else 0)

    # === HISTORY ===
    if args.command == "history":
        ticket = load_ticket(args.ticket_file, graph)

        if hasattr(args, 'json') and args.json:
            print(json.dumps({
                "ticket_id": ticket.id,
                "state": ticket.state,
                "cursor": ticket.cursor,
                "steps": len(ticket.history),
                "history": ticket.history,
                "responses": ticket.responses,
            }, indent=2, default=str))
        else:
            w = 72
            print(f"\n{BOLD}{'=' * w}")
            print(f"  Ticket: {ticket.id}  |  State: {ticket.state}  |  Steps: {len(ticket.history)}")
            print(f"{'=' * w}{RESET}\n")
            for i, entry in enumerate(ticket.history, 1):
                nid = entry["node_id"]
                resp = entry["response"]
                visit = entry["visit"]
                perf = entry.get("performer", "")
                ts = entry.get("timestamp", "")
                node = graph.get(nid)
                prompt = node.prompt[:60] if node else nid

                visit_tag = f" (#{visit})" if visit > 1 else ""
                perf_tag = f"  [{perf}]" if perf and perf != "initiator" else ""

                print(f"  {BOLD}Step {i}: {nid}{visit_tag}{perf_tag}{RESET}")
                print(f"  {DIM}{prompt}{RESET}")
                if isinstance(resp, dict):
                    for k, v in resp.items():
                        if str(k).startswith("_"):
                            continue
                        val_str = str(v)
                        if len(val_str) > 80:
                            val_str = val_str[:77] + "..."
                        print(f"    {CYAN}{k}:{RESET} {val_str}")
                else:
                    print(f"    {_summarize(resp, 80)}")
                print()
        sys.exit(0)


if __name__ == "__main__":
    main()
