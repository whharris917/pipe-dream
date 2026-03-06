"""
Graph template system using Python class inheritance.

Templates are Python classes. Inheritance uses native class inheritance.
Extension points are method calls that dispatch to subclass overrides.
Documents are serialized graphs (JSON) created by instantiate().
"""

import json
import time
from dataclasses import dataclass, field as datafield
from typing import Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Field:
    """Evidence field definition."""
    type: str = "text"
    required: bool = False
    values: list = None
    hint: str = ""

    def to_dict(self):
        d = {"type": self.type, "required": self.required}
        if self.values:
            d["values"] = self.values
        if self.hint:
            d["hint"] = self.hint
        return d


@dataclass
class Node:
    """A node in the graph."""
    id: str
    prompt: str
    context: str = ""
    evidence_schema: dict = datafield(default_factory=dict)
    performer: str = "initiator"
    terminal: bool = False
    hooks: dict = datafield(default_factory=dict)
    locked: bool = False
    edges: list = datafield(default_factory=list)
    gate: str = ""

    def to_dict(self):
        d = {
            "id": self.id,
            "prompt": self.prompt,
            "performer": self.performer,
            "terminal": self.terminal,
            "locked": self.locked,
            "edges": self.edges,
        }
        if self.context:
            d["context"] = self.context
        if self.evidence_schema:
            d["evidence_schema"] = {
                k: v.to_dict() if isinstance(v, Field) else v
                for k, v in self.evidence_schema.items()
            }
        if self.hooks:
            d["hooks"] = self.hooks
        if self.gate:
            d["gate"] = self.gate
        return d


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

class Graph:
    """A graph of nodes. The universal runtime data structure."""

    def __init__(self, id, name="", description=""):
        self.id = id
        self.name = name
        self.description = description
        self.nodes: dict[str, Node] = {}
        self.entry_point: Optional[str] = None

    @property
    def start_node(self):
        return self.nodes.get(self.entry_point)

    def get(self, node_id):
        return self.nodes.get(node_id)

    def validate(self):
        errors = []
        if not self.entry_point:
            errors.append("No entry point")
        elif self.entry_point not in self.nodes:
            errors.append(f"Entry point '{self.entry_point}' not found")

        for nid, node in self.nodes.items():
            for edge in node.edges:
                target = edge["to"] if isinstance(edge, dict) else edge.to
                if target not in self.nodes:
                    errors.append(f"Edge from '{nid}' to unknown '{target}'")

        if self.entry_point and self.entry_point in self.nodes:
            reachable = set()
            self._walk(self.entry_point, reachable)
            for nid in self.nodes:
                if nid not in reachable:
                    errors.append(f"Unreachable: '{nid}'")
        return errors

    def _walk(self, nid, visited):
        if nid in visited:
            return
        visited.add(nid)
        node = self.nodes.get(nid)
        if node:
            for edge in node.edges:
                target = edge["to"] if isinstance(edge, dict) else edge.to
                self._walk(target, visited)

    def to_dict(self):
        return {
            "graph": {
                "id": self.id,
                "name": self.name,
                "description": self.description,
                "entry_point": self.entry_point,
            },
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
        }

    @classmethod
    def from_dict(cls, data):
        gd = data["graph"]
        g = cls(gd["id"], gd.get("name", ""), gd.get("description", ""))
        g.entry_point = gd.get("entry_point")
        for nid, nd in data.get("nodes", {}).items():
            evidence = {}
            for fname, fd in nd.get("evidence_schema", {}).items():
                evidence[fname] = Field(
                    type=fd.get("type", "text"),
                    required=fd.get("required", False),
                    values=fd.get("values"),
                    hint=fd.get("hint", ""),
                )
            node = Node(
                id=nid, prompt=nd["prompt"],
                context=nd.get("context", ""),
                evidence_schema=evidence,
                performer=nd.get("performer", "initiator"),
                terminal=nd.get("terminal", False),
                locked=nd.get("locked", False),
                edges=nd.get("edges", []),
                hooks=nd.get("hooks", {}),
                gate=nd.get("gate", ""),
            )
            g.nodes[nid] = node
        return g

    def diff(self, template_graph):
        """Compare this graph against a template graph."""
        missing = [nid for nid in template_graph.nodes if nid not in self.nodes]
        added = [nid for nid in self.nodes if nid not in template_graph.nodes]
        modified = []
        for nid in template_graph.nodes:
            if nid in self.nodes:
                tn = template_graph.nodes[nid]
                dn = self.nodes[nid]
                diffs = []
                if dn.prompt != tn.prompt:
                    diffs.append("prompt")
                if dn.context != tn.context:
                    diffs.append("context")
                if dn.performer != tn.performer:
                    diffs.append("performer")
                if dn.terminal != tn.terminal:
                    diffs.append("terminal")
                if dn.gate != tn.gate:
                    diffs.append("gate")
                if set(dn.evidence_schema.keys()) != set(tn.evidence_schema.keys()):
                    diffs.append("evidence_schema")
                # Compare edge targets, not just counts
                dn_targets = [(e["to"] if isinstance(e, dict) else e) for e in dn.edges]
                tn_targets = [(e["to"] if isinstance(e, dict) else e) for e in tn.edges]
                if dn_targets != tn_targets:
                    diffs.append("edges")
                if diffs:
                    modified.append((nid, diffs))
        return {
            "missing": missing, "added": added, "modified": modified,
            "compliant": len(missing) == 0 and len(modified) == 0,
        }


# ---------------------------------------------------------------------------
# Graph builder (used during template definition)
# ---------------------------------------------------------------------------

class _GraphBuilder:
    """Accumulates nodes and edges during template.define()."""

    def __init__(self, template_id):
        self.template_id = template_id
        self._nodes: list[Node] = []
        self._explicit_edges: dict[str, list] = {}  # from_id -> [(to_id, cond)]

    def node(self, id, *, prompt, context="", evidence=None,
             performer="initiator", terminal=False, hooks=None,
             gate="", locked=False):
        full_id = f"{self.template_id}.{id}"
        ev = {}
        if evidence:
            for fname, fval in evidence.items():
                if isinstance(fval, Field):
                    ev[fname] = fval
                elif isinstance(fval, dict):
                    ev[fname] = Field(**fval)
                else:
                    ev[fname] = Field(type="text")
        n = Node(
            id=full_id, prompt=prompt, context=context,
            evidence_schema=ev, performer=performer,
            terminal=terminal, hooks=hooks or {},
            locked=locked, gate=gate,
        )
        self._nodes.append(n)
        return n

    def edge(self, from_node, to_node, condition=""):
        from_id = from_node.id if isinstance(from_node, Node) else from_node
        to_id = to_node.id if isinstance(to_node, Node) else to_node
        self._explicit_edges.setdefault(from_id, []).append((to_id, condition))

    def finalize(self):
        g = Graph(self.template_id)
        for n in self._nodes:
            g.nodes[n.id] = n
        if self._nodes:
            g.entry_point = self._nodes[0].id

        # Build edges: explicit edges first, then auto-linear fallthrough
        for i, n in enumerate(self._nodes):
            edges = []
            if n.id in self._explicit_edges:
                edges = [{"to": tid, "condition": cond} if cond
                         else {"to": tid}
                         for tid, cond in self._explicit_edges[n.id]]
            # Auto-linear: add fallthrough to next node if no unconditional edge exists
            has_unconditional = any(
                not (e.get("condition", "") if isinstance(e, dict) else "")
                for e in edges
            )
            if not n.terminal and not has_unconditional and i + 1 < len(self._nodes):
                edges.append({"to": self._nodes[i + 1].id})
            n.edges = edges
        return g


# ---------------------------------------------------------------------------
# Template base class
# ---------------------------------------------------------------------------

class Template:
    """Base class for graph templates using Python class inheritance.

    Subclass and override define() to create a template.
    Extension points are methods named define_*() that subclasses override.
    """

    id = ""
    name = ""
    description = ""
    abstract = False

    def build(self):
        """Build a Graph from this template definition."""
        builder = _GraphBuilder(self.id)
        self.define(builder)
        graph = builder.finalize()
        graph.name = self.name
        graph.description = self.description
        return graph

    def define(self, g):
        """Override to define the template's nodes and edges."""
        pass

    def fill(self, g, name):
        """Insert fill data or call define_{name}() on the subclass.

        Templates call self.fill(g, "execution_body") at extension points.
        If instantiate() was called with fills={"execution_body": [...]},
        those nodes are inserted. Otherwise, define_execution_body(g) is called.
        """
        fills = getattr(self, '_pending_fills', {})
        if name in fills:
            for nd in fills[name]:
                ev = {}
                for fname, fd in nd.get("evidence", {}).items():
                    if isinstance(fd, Field):
                        ev[fname] = fd
                    elif isinstance(fd, dict):
                        ev[fname] = Field(**fd)
                    else:
                        ev[fname] = Field(type="text")
                g.node(
                    nd["id"], prompt=nd["prompt"],
                    context=nd.get("context", ""),
                    evidence=ev,
                    performer=nd.get("performer", "initiator"),
                    terminal=nd.get("terminal", False),
                )
        else:
            method = getattr(self, f"define_{name}", None)
            if method:
                method(g)

    def instantiate(self, doc_id, fills=None):
        """Create a document Graph with template nodes locked."""
        self._pending_fills = fills or {}
        graph = self.build()
        self._pending_fills = {}
        graph.id = doc_id
        graph.name = f"{self.name}: {doc_id}"

        # Determine which nodes came from fills (should stay unlocked during drafting)
        fill_node_ids = set()
        for fill_nodes in (fills or {}).values():
            for fn in fill_nodes:
                fill_node_ids.add(f"{self.id}.{fn['id']}")

        for node in graph.nodes.values():
            if node.id not in fill_node_ids:
                node.locked = True
        return graph

    def freeze(self, graph):
        """Lock all nodes (pre-approval transition)."""
        for node in graph.nodes.values():
            node.locked = True
        return graph
