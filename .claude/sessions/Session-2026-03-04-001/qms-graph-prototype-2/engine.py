#!/usr/bin/env python3
"""
QMS Graph Engine (Prototype 2) - Python template edition.

Traverses Graph objects built from Python Template classes.
Documents are JSON files containing serialized graph + ticket state.

Usage:
  python engine.py start <template.module.Class> --doc-id <id> [--doc-dir <dir>]
  python engine.py status <doc-file>
  python engine.py respond <doc-file> --response-file <file>
  python engine.py map <doc-file> [--no-color]
  python engine.py history <doc-file> [--json]
  python engine.py validate <template.module.Class>
  python engine.py diff <doc-file> <template.module.Class>
  python engine.py list-templates
"""

import sys
import os
import re
import json
import time
import argparse
import importlib
import inspect
from pathlib import Path

# Add parent dir to path so templates/ is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph import Graph, Node, Field, Template


# ---------------------------------------------------------------------------
# Ticket
# ---------------------------------------------------------------------------

class Ticket:
    def __init__(self, id, graph, start_node=None):
        self.id = id
        self.cursor = start_node or (graph.entry_point if graph else None)
        self.responses = {}
        self.history = []
        self.state = "active"
        self.created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.metadata = {}

    def record(self, node_id, response, performer="initiator"):
        self.responses[node_id] = response
        self.history.append({
            "node_id": node_id, "response": response,
            "performer": performer,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        })

    def to_dict(self):
        return {
            "id": self.id, "cursor": self.cursor,
            "responses": self.responses, "history": self.history,
            "state": self.state, "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data, graph):
        t = cls(data["id"], graph, data.get("cursor"))
        t.responses = data.get("responses", {})
        t.history = data.get("history", [])
        t.state = data.get("state", "active")
        t.created_at = data.get("created_at", "")
        t.metadata = data.get("metadata", {})
        return t


# ---------------------------------------------------------------------------
# Condition evaluation
# ---------------------------------------------------------------------------

def _eval_condition(expression, namespace):
    """Evaluate a condition expression in a safe namespace."""
    if not expression:
        return True
    namespace.setdefault("int", int)
    namespace.setdefault("str", str)
    namespace.setdefault("len", len)
    namespace.setdefault("bool", bool)
    try:
        return bool(eval(expression, {"__builtins__": {}}, namespace))
    except Exception:
        return False


class Evaluator:
    """Evaluates edge conditions using ticket state."""

    def __init__(self, ticket):
        self.ticket = ticket

    def evaluate(self, expression):
        if not expression:
            return True
        ns = dict(self.ticket.responses)
        ns["ticket"] = self.ticket.metadata
        if self.ticket.history:
            ns["response"] = self.ticket.history[-1]["response"]
        return _eval_condition(expression, ns)


# ---------------------------------------------------------------------------
# Document I/O
# ---------------------------------------------------------------------------

def save_document(graph, ticket, path):
    data = {
        "graph": graph.to_dict(),
        "ticket": ticket.to_dict(),
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def load_document(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    graph = Graph.from_dict(data["graph"])
    ticket = Ticket.from_dict(data["ticket"], graph)
    return graph, ticket


# ---------------------------------------------------------------------------
# Template loading
# ---------------------------------------------------------------------------

def load_template_class(spec):
    """Load a Template class from a dotted path like 'templates.diagnostic.Diagnostic'.

    Accepts:
      - 'templates.diagnostic' -> auto-find non-abstract Template in module
      - 'templates.diagnostic.Diagnostic' -> use explicit class name
    """
    # Try importing spec as a module first (auto-find class)
    try:
        mod = importlib.import_module(spec)
        for name, obj in inspect.getmembers(mod, inspect.isclass):
            if (issubclass(obj, Template) and obj is not Template
                    and obj.__module__ == mod.__name__
                    and not obj.__dict__.get('abstract', False)):
                return obj
        raise ValueError(f"No Template subclass found in {spec}")
    except ImportError:
        pass

    # Fall back: split last component as class name
    parts = spec.rsplit(".", 1)
    if len(parts) < 2:
        raise ValueError(f"Cannot resolve template: {spec}")
    module_path, class_name = parts
    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    if not (inspect.isclass(cls) and issubclass(cls, Template)):
        raise ValueError(f"{spec} is not a Template subclass")
    return cls


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_response(node, response):
    errors = []
    warnings = []
    schema = node.evidence_schema
    for fname, field in schema.items():
        is_required = field.required if isinstance(field, Field) else field.get("required", False)
        if is_required and fname not in response:
            errors.append(f"Missing required field '{fname}'")
            continue
        if fname in response:
            val = response[fname]
            ftype = field.type if isinstance(field, Field) else field.get("type", "text")
            values = field.values if isinstance(field, Field) else field.get("values")
            if ftype == "enum" and values:
                if str(val) not in [str(v) for v in values]:
                    errors.append(f"Field '{fname}': '{val}' not in {values}")
            elif ftype == "integer":
                if not isinstance(val, int):
                    errors.append(f"Field '{fname}': expected int, got {type(val).__name__}")
    # Warn on unexpected fields
    for fname in response:
        if fname not in schema:
            warnings.append(f"Unknown field '{fname}' (not in schema)")
    return errors, warnings


# ---------------------------------------------------------------------------
# Engine operations
# ---------------------------------------------------------------------------

def resolve_next(graph, ticket, evaluator):
    """Determine the next node based on edge conditions."""
    node = graph.get(ticket.cursor)
    if not node or node.terminal:
        return None
    for edge in node.edges:
        cond = edge.get("condition", "") if isinstance(edge, dict) else ""
        target = edge["to"] if isinstance(edge, dict) else edge
        if evaluator.evaluate(cond):
            return target
    return None


def spawn_retry(graph, node, response):
    """If node has a retry spec and condition is met, spawn cloned nodes.

    Clones the specified nodes with an incremented suffix, wires them
    between the current node and its forward target. The graph grows
    forward (stays acyclic). Returns the first spawned node ID, or None.
    """
    if not node.retry:
        return None

    condition = node.retry.get("when", "")
    ns = dict(response)
    ns["response"] = response
    if not _eval_condition(condition, ns):
        return None

    base_node_names = node.retry["nodes"]
    prefix = node.id.rsplit(".", 1)[0]

    # Find next available suffix
    suffix = 2
    while f"{prefix}.{base_node_names[0]}-{suffix}" in graph.nodes:
        suffix += 1

    # Find the forward target (first unconditional edge)
    forward_target = None
    for edge in node.edges:
        if not edge.get("condition"):
            forward_target = edge["to"]
            break
    if forward_target is None:
        return None

    # Clone nodes
    cloned_ids = []
    for base_name in base_node_names:
        original = graph.nodes.get(f"{prefix}.{base_name}")
        if not original:
            continue
        new_id = f"{prefix}.{base_name}-{suffix}"
        clone = Node(
            id=new_id, prompt=original.prompt, context=original.context,
            evidence_schema=dict(original.evidence_schema),
            performer=original.performer, terminal=False,
            hooks=dict(original.hooks), locked=original.locked,
            edges=[], gate=original.gate,
            retry=dict(original.retry) if original.retry else None,
        )
        graph.nodes[new_id] = clone
        cloned_ids.append(new_id)

    if not cloned_ids:
        return None

    # Wire clones: linear chain, last one points to original forward target
    for i, cid in enumerate(cloned_ids):
        if i + 1 < len(cloned_ids):
            graph.nodes[cid].edges = [{"to": cloned_ids[i + 1]}]
        else:
            graph.nodes[cid].edges = [{"to": forward_target}]

    # Splice: replace current node's forward edge with edge to first clone
    node.edges = [
        {"to": cloned_ids[0]} if (not e.get("condition") and e.get("to") == forward_target) else e
        for e in node.edges
    ]

    return cloned_ids[0]


def do_respond(graph, ticket, response):
    """Record response, advance cursor, return status."""
    if ticket.state == "complete":
        return {"error": "Document is already complete", "state": "complete"}

    evaluator = Evaluator(ticket)
    node = graph.get(ticket.cursor)

    if not node:
        return {"error": "No current node"}

    # Validate
    errors, warnings = validate_response(node, response)
    if errors:
        result = {
            "errors": errors,
            "stopped_reason": "validation_error",
            "cursor": ticket.cursor,
        }
        if warnings:
            result["warnings"] = warnings
        return result

    # Check gate condition
    if node.gate:
        gate_ns = dict(response)
        gate_ns["response"] = response
        if not _eval_condition(node.gate, gate_ns):
            result = {
                "gate_blocked": True,
                "gate": node.gate,
                "cursor": ticket.cursor,
                "message": "Gate condition not met. Revise your response.",
            }
            if warnings:
                result["warnings"] = warnings
            return result

    # Record
    ticket.record(ticket.cursor, response, node.performer)

    # Terminal check
    if node.terminal:
        ticket.state = "complete"
        result = {"cursor": ticket.cursor, "state": "complete", "steps": len(ticket.history)}
        if warnings:
            result["warnings"] = warnings
        return result

    # Check retry — may spawn new nodes and redirect cursor
    spawned = spawn_retry(graph, node, response)
    if spawned:
        ticket.cursor = spawned
    else:
        # Normal edge resolution
        next_id = resolve_next(graph, ticket, evaluator)
        if next_id:
            ticket.cursor = next_id
        else:
            ticket.state = "complete"

    result = {
        "cursor": ticket.cursor,
        "state": ticket.state,
        "steps": len(ticket.history),
    }
    if warnings:
        result["warnings"] = warnings
    return result


def get_status(graph, ticket):
    """Get current status for the agent."""
    node = graph.get(ticket.cursor)
    if not node:
        return {"state": ticket.state, "cursor": ticket.cursor}

    schema = {}
    for fname, field in node.evidence_schema.items():
        if isinstance(field, Field):
            schema[fname] = field.to_dict()
        else:
            schema[fname] = field

    return {
        "state": ticket.state,
        "cursor": ticket.cursor,
        "steps_completed": len(ticket.history),
        "total_nodes": len(graph.nodes),
        "node": {
            "id": node.id,
            "prompt": node.prompt,
            "context": node.context,
            "performer": node.performer,
            "terminal": node.terminal,
            "locked": node.locked,
            "evidence_schema": schema,
            "edges": node.edges,
        },
    }


def render_map(graph, ticket=None, use_color=True):
    """Render the graph topology as text."""
    if use_color:
        GREEN, CYAN, BOLD, DIM, RESET = "\033[32m", "\033[36m", "\033[1m", "\033[2m", "\033[0m"
    else:
        GREEN = CYAN = BOLD = DIM = RESET = ""

    lines = [f"\n{'=' * 60}", f"  {graph.name or graph.id}", f"{'=' * 60}\n"]

    visited = set()
    cursor = ticket.cursor if ticket else None

    def walk(nid, indent=0):
        if nid in visited:
            lines.append(f"{'  ' * indent}{CYAN}^ loop back to {nid}{RESET}")
            return
        visited.add(nid)
        node = graph.get(nid)
        if not node:
            return

        # Status marker
        completed = set()
        if ticket:
            completed = {h["node_id"] for h in ticket.history}

        if nid in completed:
            marker = f"{GREEN}+{RESET}"
        elif nid == cursor:
            marker = f"{BOLD}>>>{RESET}"
        else:
            marker = f"{DIM}.{RESET}"

        lock = " [locked]" if node.locked else ""
        term = "  END" if node.terminal else ""
        lines.append(f"{'  ' * indent}{marker}  {node.id}  {node.prompt[:50]}{lock}{term}")

        for edge in node.edges:
            target = edge["to"] if isinstance(edge, dict) else edge
            cond = edge.get("condition", "") if isinstance(edge, dict) else ""
            if cond:
                lines.append(f"{'  ' * (indent + 1)}|-- if {cond[:60]}")
            walk(target, indent + 1)

    if graph.entry_point:
        walk(graph.entry_point)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Automated test runner
# ---------------------------------------------------------------------------

def auto_run(graph, responses_by_node, ticket_id="auto"):
    """Run through a graph with scripted responses. Returns result dict.

    Responses are looked up by exact node ID first, then by base name
    (stripping -N suffix from spawned retry clones). List values are
    indexed by how many times that base name has been consumed.
    """
    ticket = Ticket(ticket_id, graph)
    steps = 0
    max_steps = 200
    base_response_counts = {}  # base_id -> times consumed

    while ticket.cursor and ticket.state == "active" and steps < max_steps:
        node = graph.get(ticket.cursor)
        if not node:
            break

        nid = node.id
        # Map spawned clone IDs back to their base name
        base_id = re.sub(r'-\d+$', '', nid)

        # Look up response: exact ID first, then base name
        if nid in responses_by_node:
            resp_source = responses_by_node[nid]
        else:
            resp_source = responses_by_node.get(base_id, {})

        # Handle list responses (indexed by base name visit count)
        visit_idx = base_response_counts.get(base_id, 0)
        if isinstance(resp_source, list):
            if visit_idx < len(resp_source):
                response = dict(resp_source[visit_idx])
            else:
                response = dict(resp_source[-1]) if resp_source else {}
        else:
            response = dict(resp_source) if resp_source else {}

        base_response_counts[base_id] = visit_idx + 1

        # Auto-fill required fields not already provided
        for fname, field in node.evidence_schema.items():
            req = field.required if isinstance(field, Field) else field.get("required", False)
            if req and fname not in response:
                ftype = field.type if isinstance(field, Field) else field.get("type", "text")
                values = field.values if isinstance(field, Field) else field.get("values")
                if ftype == "enum" and values:
                    response[fname] = values[0]
                elif ftype == "integer":
                    response[fname] = 0
                elif ftype == "bool":
                    response[fname] = True
                else:
                    response[fname] = "auto"

        result = do_respond(graph, ticket, response)
        steps += 1

        # Stop on errors or gate blocks
        if result.get("errors") or result.get("gate_blocked"):
            break

    return {
        "steps": steps,
        "state": ticket.state,
        "history": ticket.history,
        "responses": ticket.responses,
        "ticket": ticket,
        "graph": graph,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="QMS Graph Engine (Python Templates)")
    sub = parser.add_subparsers(dest="command")

    # start
    p_start = sub.add_parser("start", help="Start a new document from a template")
    p_start.add_argument("template", help="Template class (e.g., templates.code_cr.CodeCR)")
    p_start.add_argument("--doc-id", required=True, help="Document ID")
    p_start.add_argument("--doc-dir", default=".documents", help="Document directory")
    p_start.add_argument("--fills", help="JSON file with extension point fills")

    # status
    p_status = sub.add_parser("status", help="Show current status")
    p_status.add_argument("doc_file", help="Document JSON file")

    # respond
    p_respond = sub.add_parser("respond", help="Submit a response")
    p_respond.add_argument("doc_file", help="Document JSON file")
    p_respond_group = p_respond.add_mutually_exclusive_group(required=True)
    p_respond_group.add_argument("--response-file", help="JSON response file")
    p_respond_group.add_argument("--response", help="Inline JSON response string")

    # map
    p_map = sub.add_parser("map", help="Show graph topology")
    p_map.add_argument("doc_file", help="Document JSON file")
    p_map.add_argument("--no-color", action="store_true")

    # history
    p_hist = sub.add_parser("history", help="Show collected evidence")
    p_hist.add_argument("doc_file", help="Document JSON file")
    p_hist.add_argument("--json", action="store_true")

    # validate
    p_val = sub.add_parser("validate", help="Validate a template")
    p_val.add_argument("template", help="Template class")

    # diff
    p_diff = sub.add_parser("diff", help="Compare document against template")
    p_diff.add_argument("doc_file", help="Document JSON file")
    p_diff.add_argument("template", help="Template class")

    # list-templates
    sub.add_parser("list-templates", help="List available templates")

    args = parser.parse_args()

    if args.command == "start":
        cls = load_template_class(args.template)
        fills = None
        if args.fills:
            with open(args.fills, "r") as f:
                fills = json.load(f)
        tpl = cls()
        graph = tpl.instantiate(args.doc_id, fills=fills)
        errors = graph.validate()
        if errors:
            print(json.dumps({"errors": errors}, indent=2))
            sys.exit(1)
        ticket = Ticket(args.doc_id, graph)
        doc_path = str(Path(args.doc_dir) / f"{args.doc_id}.json").replace("\\", "/")
        save_document(graph, ticket, doc_path)
        status = get_status(graph, ticket)
        status["doc_file"] = doc_path
        print(json.dumps(status, indent=2))

    elif args.command == "status":
        graph, ticket = load_document(args.doc_file)
        print(json.dumps(get_status(graph, ticket), indent=2))

    elif args.command == "respond":
        graph, ticket = load_document(args.doc_file)
        if args.response_file:
            with open(args.response_file, "r") as f:
                response = json.load(f)
        else:
            response = json.loads(args.response)
        result = do_respond(graph, ticket, response)
        save_document(graph, ticket, args.doc_file)
        # Include next node status
        if ticket.state == "active":
            result["status"] = get_status(graph, ticket)
        print(json.dumps(result, indent=2))

    elif args.command == "map":
        graph, ticket = load_document(args.doc_file)
        print(render_map(graph, ticket, use_color=not args.no_color))

    elif args.command == "history":
        graph, ticket = load_document(args.doc_file)
        if hasattr(args, 'json') and args.json:
            print(json.dumps({
                "id": ticket.id, "state": ticket.state,
                "steps": len(ticket.history),
                "history": ticket.history,
                "responses": ticket.responses,
            }, indent=2, default=str))
        else:
            print(f"\n  Document: {ticket.id} | State: {ticket.state}")
            print(f"  Steps completed: {len(ticket.history)}\n")
            for h in ticket.history:
                print(f"  [{h['timestamp']}] {h['node_id']}")
                if isinstance(h['response'], dict):
                    for k, v in h['response'].items():
                        val = str(v)[:60]
                        print(f"    {k}: {val}")
                print()

    elif args.command == "validate":
        cls = load_template_class(args.template)
        graph = cls().build()
        errors = graph.validate()
        print(json.dumps({
            "valid": len(errors) == 0,
            "nodes": len(graph.nodes),
            "errors": errors,
            "template": cls.id,
            "name": cls.name,
        }, indent=2))

    elif args.command == "diff":
        graph, ticket = load_document(args.doc_file)
        cls = load_template_class(args.template)
        tpl_graph = cls().build()
        result = graph.diff(tpl_graph)
        print(json.dumps(result, indent=2))

    elif args.command == "list-templates":
        import templates
        tpl_dir = Path(templates.__file__).parent
        found = []
        for py_file in sorted(tpl_dir.glob("*.py")):
            if py_file.stem.startswith("_"):
                continue
            try:
                mod = importlib.import_module(f"templates.{py_file.stem}")
                for name, obj in inspect.getmembers(mod, inspect.isclass):
                    if (issubclass(obj, Template) and obj is not Template
                            and obj.__module__ == mod.__name__):
                        is_abstract = obj.__dict__.get('abstract', False)
                        abstract = " (abstract)" if is_abstract else ""
                        bases = " extends " + ", ".join(
                            b.__name__ for b in obj.__bases__
                            if b is not Template and issubclass(b, Template)
                        ) if any(b is not Template and issubclass(b, Template)
                                for b in obj.__bases__) else ""
                        found.append(f"  templates.{py_file.stem}.{name}{bases}{abstract}")
            except Exception as e:
                found.append(f"  templates.{py_file.stem}: ERROR ({e})")
        print("\nAvailable templates:\n")
        for line in found:
            print(line)
        print()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
