#!/usr/bin/env python3
"""
Automated test harness for qms-graph-prototype-2.

Tests template building, validation, instantiation, traversal, serialization,
and edge cases. Run directly: python test_harness.py
"""

import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph import Graph, Node, Field, Template, _GraphBuilder
from engine import (
    Ticket, Evaluator, auto_run, save_document, load_document,
    validate_response, do_respond, get_status, resolve_next,
    render_map, load_template_class, spawn_retry,
)

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {detail}")


# ===========================================================================
# Test 1: Template building and validation
# ===========================================================================
print("\n=== Test 1: Template building and validation ===\n")

for tpl_path in [
    "templates.diagnostic", "templates.repair",
    "templates.incident", "templates.logic_puzzle",
]:
    cls = load_template_class(tpl_path)
    tpl = cls()
    graph = tpl.build()
    errors = graph.validate()
    check(f"{tpl_path} builds", graph is not None)
    check(f"{tpl_path} validates", len(errors) == 0, str(errors))
    check(f"{tpl_path} has entry", graph.entry_point is not None)
    check(f"{tpl_path} has nodes", len(graph.nodes) > 0, f"nodes={len(graph.nodes)}")

    # Exactly one terminal node
    terminals = [n for n in graph.nodes.values() if n.terminal]
    check(f"{tpl_path} has 1 terminal", len(terminals) == 1,
          f"terminals={[t.id for t in terminals]}")


# ===========================================================================
# Test 2: Inheritance chain correctness
# ===========================================================================
print("\n=== Test 2: Inheritance chain correctness ===\n")

from templates.diagnostic import Diagnostic
from templates.incident import Incident
from templates.repair import Repair
from templates.procedure_base import ProcedureBase

# Diagnostic should have ProcedureBase's start/verify/close + its own nodes
diag = Diagnostic().build()
diag_ids = list(diag.nodes.keys())
check("diagnostic has start", "diagnostic.start" in diag_ids)
check("diagnostic has observe", "diagnostic.observe" in diag_ids)
check("diagnostic has hypothesize", "diagnostic.hypothesize" in diag_ids)
check("diagnostic has test", "diagnostic.test" in diag_ids)
check("diagnostic has conclude", "diagnostic.conclude" in diag_ids)
check("diagnostic has verify", "diagnostic.verify" in diag_ids)
check("diagnostic has close", "diagnostic.close" in diag_ids)
check("diagnostic 7 nodes", len(diag_ids) == 7, f"got {len(diag_ids)}")

# Incident extends Diagnostic: should have all diagnostic nodes + contain + remediate
inc = Incident().build()
inc_ids = list(inc.nodes.keys())
check("incident has start", "incident.start" in inc_ids)
check("incident has observe", "incident.observe" in inc_ids)
check("incident has contain", "incident.contain" in inc_ids)
check("incident has remediate", "incident.remediate" in inc_ids)
check("incident has conclude", "incident.conclude" in inc_ids)
check("incident 9 nodes", len(inc_ids) == 9, f"got {len(inc_ids)}: {inc_ids}")

# Incident's start node should have severity field (overridden from ProcedureBase)
start = inc.nodes["incident.start"]
check("incident start has severity", "severity" in start.evidence_schema)
check("incident start has active_impact", "active_impact" in start.evidence_schema)

# Repair should have ProcedureBase + its own nodes
rep = Repair().build()
rep_ids = list(rep.nodes.keys())
check("repair has assess", "repair.assess" in rep_ids)
check("repair has plan", "repair.plan" in rep_ids)
check("repair has execute", "repair.execute" in rep_ids)
check("repair has test-repair", "repair.test-repair" in rep_ids)
check("repair 7 nodes", len(rep_ids) == 7, f"got {len(rep_ids)}: {rep_ids}")


# ===========================================================================
# Test 3: Instantiation and locking
# ===========================================================================
print("\n=== Test 3: Instantiation and locking ===\n")

tpl = Diagnostic()
doc = tpl.instantiate("DIAG-001")
check("doc id is DIAG-001", doc.id == "DIAG-001")
check("all nodes locked", all(n.locked for n in doc.nodes.values()))

# Instantiate with fills — fill nodes should be unlocked
tpl2 = Repair()
fills = {"repair_steps": [
    {"id": "custom-step", "prompt": "Custom repair step",
     "evidence": {"notes": Field("text", required=True)}},
]}
doc2 = tpl2.instantiate("REP-001", fills=fills)
check("fill node exists", "repair.custom-step" in doc2.nodes)
check("fill node unlocked", not doc2.nodes["repair.custom-step"].locked)
check("template node locked", doc2.nodes["repair.start"].locked)

# Freeze should lock everything
tpl2.freeze(doc2)
check("after freeze all locked", all(n.locked for n in doc2.nodes.values()))


# ===========================================================================
# Test 4: Full traversal with auto_run
# ===========================================================================
print("\n=== Test 4: Full traversal with auto_run ===\n")

# Logic Puzzle — simplest, 3 nodes
puzzle_cls = load_template_class("templates.logic_puzzle")
puzzle_graph = puzzle_cls().build()
result = auto_run(puzzle_graph, {})
check("puzzle completes", result["state"] == "complete")
check("puzzle 3 steps", result["steps"] == 3, f"steps={result['steps']}")

# Diagnostic — 7 nodes linear
diag_graph = Diagnostic().build()
result = auto_run(diag_graph, {})
check("diagnostic completes", result["state"] == "complete")
check("diagnostic 7 steps", result["steps"] == 7, f"steps={result['steps']}")

# Repair — 7 nodes linear
rep_graph = Repair().build()
result = auto_run(rep_graph, {})
check("repair completes", result["state"] == "complete")
check("repair 7 steps", result["steps"] == 7, f"steps={result['steps']}")

# Incident — 9 nodes linear
inc_graph = Incident().build()
result = auto_run(inc_graph, {})
check("incident completes", result["state"] == "complete")
check("incident 9 steps", result["steps"] == 9, f"steps={result['steps']}")


# ===========================================================================
# Test 5: Response validation
# ===========================================================================
print("\n=== Test 5: Response validation ===\n")

node = Node(
    id="test", prompt="Test",
    evidence_schema={
        "name": Field("text", required=True),
        "status": Field("enum", required=True, values=["ok", "fail"]),
        "notes": Field("text", required=False),
    },
)

# Valid response
errors, warnings = validate_response(node, {"name": "foo", "status": "ok"})
check("valid response", len(errors) == 0, str(errors))
check("no warnings on valid", len(warnings) == 0)

# Missing required
errors, warnings = validate_response(node, {"status": "ok"})
check("missing required caught", len(errors) == 1)
check("error mentions name", "name" in errors[0])

# Bad enum value
errors, warnings = validate_response(node, {"name": "foo", "status": "maybe"})
check("bad enum caught", len(errors) == 1)
check("error mentions status", "status" in errors[0])

# Missing multiple required
errors, warnings = validate_response(node, {})
check("2 missing required", len(errors) == 2)

# Extra field warning
errors, warnings = validate_response(node, {"name": "foo", "status": "ok", "bogus": "x"})
check("extra field warns", len(warnings) == 1)
check("warning mentions bogus", "bogus" in warnings[0])

# Completed document rejection
print("\n=== Test 5b: Completed document rejection ===\n")

from templates.logic_puzzle import LogicPuzzle
g_complete = LogicPuzzle().build()
t_complete = Ticket("complete-test", g_complete)
auto_run_result = auto_run(g_complete, {})
t_complete = auto_run_result["ticket"]
result = do_respond(g_complete, t_complete, {"answer": "test"})
check("completed doc rejected", "error" in result)
check("error says complete", "complete" in result.get("error", "").lower())


# ===========================================================================
# Test 6: do_respond with validation errors
# ===========================================================================
print("\n=== Test 6: do_respond validation ===\n")

graph = Diagnostic().build()
ticket = Ticket("test-respond", graph)

# Try with missing required field
result = do_respond(graph, ticket, {"objective": "test"})
check("validation error returned", "errors" in result, str(result))
check("cursor unchanged", ticket.cursor == "diagnostic.start")

# Now with valid response
result = do_respond(graph, ticket, {"objective": "test", "ready": "yes"})
check("advances after valid", ticket.cursor == "diagnostic.observe", ticket.cursor)
check("1 step", len(ticket.history) == 1)


# ===========================================================================
# Test 7: Serialization round-trip
# ===========================================================================
print("\n=== Test 7: Serialization round-trip ===\n")

graph = Incident().instantiate("INC-RT")
ticket = Ticket("INC-RT", graph)

# Complete 3 steps
do_respond(graph, ticket, {
    "objective": "Server down", "severity": "high",
    "active_impact": "yes", "ready": "yes",
})
do_respond(graph, ticket, {
    "symptoms": "CPU 100%", "onset": "10:00 AM",
})
do_respond(graph, ticket, {
    "hypothesis": "Memory leak", "confidence": "medium",
})

with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
    tmppath = f.name

save_document(graph, ticket, tmppath)
g2, t2 = load_document(tmppath)

check("graph id preserved", g2.id == "INC-RT")
check("ticket cursor preserved", t2.cursor == ticket.cursor)
check("history preserved", len(t2.history) == 3)
check("responses preserved", len(t2.responses) == 3)
check("node count preserved", len(g2.nodes) == len(graph.nodes))
check("locked state preserved", g2.nodes["incident.start"].locked)

# Continue from loaded state
result = do_respond(g2, t2, {
    "test_description": "Check memory", "test_result": "Confirmed",
    "hypothesis_confirmed": "yes",
})
check("continue after load", t2.cursor == "incident.contain", t2.cursor)

os.unlink(tmppath)


# ===========================================================================
# Test 8: Graph diff
# ===========================================================================
print("\n=== Test 8: Graph diff ===\n")

tpl = Diagnostic()
template_graph = tpl.build()
doc_graph = tpl.instantiate("DIFF-001")

# No diff when freshly instantiated
diff = doc_graph.diff(template_graph)
check("no missing nodes", len(diff["missing"]) == 0)
check("no added nodes", len(diff["added"]) == 0)

# Add a node to the document
extra = Node(id="diagnostic.extra", prompt="Extra step")
doc_graph.nodes["diagnostic.extra"] = extra
diff = doc_graph.diff(template_graph)
check("added node detected", "diagnostic.extra" in diff["added"])

# Remove a node
del doc_graph.nodes["diagnostic.observe"]
diff = doc_graph.diff(template_graph)
check("missing node detected", "diagnostic.observe" in diff["missing"])


# ===========================================================================
# Test 9: Evaluator
# ===========================================================================
print("\n=== Test 9: Evaluator ===\n")

graph = Diagnostic().build()
ticket = Ticket("eval-test", graph)

# Record some history for evaluator testing
ticket.record("diagnostic.start", {"objective": "test", "ready": "yes"})
ticket.record("diagnostic.observe", {"symptoms": "X", "onset": "now"})

ev = Evaluator(ticket)
check("simple true", ev.evaluate("True"))
check("simple false", not ev.evaluate("False"))
check("empty is true", ev.evaluate(""))
check("response access works", ev.evaluate(
    "response.get('symptoms') == 'X'"))
check("int available", ev.evaluate("int('42') == 42"))
check("len available", ev.evaluate("len('abc') == 3"))
check("bad expr is false", not ev.evaluate("undefined_var"))


# ===========================================================================
# Test 10: render_map
# ===========================================================================
print("\n=== Test 10: render_map ===\n")

graph = Diagnostic().build()
ticket = Ticket("map-test", graph)
output = render_map(graph, ticket, use_color=False)
check("map has title", "Diagnostic" in output)
check("map has nodes", "diagnostic.start" in output)
check("map has terminal", "END" in output)


# ===========================================================================
# Test 11: Gate conditions
# ===========================================================================
print("\n=== Test 11: Gate conditions ===\n")

# Build a simple graph with a gate
class GatedTemplate(Template):
    id = "gated"
    name = "Gated"
    def define(self, g):
        g.node("confirm", prompt="Confirm readiness",
               evidence={"ready": Field("enum", required=True, values=["yes", "no"])},
               gate="response.get('ready') == 'yes'")
        g.node("done", prompt="Done", terminal=True,
               evidence={"result": Field("text", required=True)})

gated_graph = GatedTemplate().build()
gated_ticket = Ticket("gate-test", gated_graph)

# Try with gate-failing response
result = do_respond(gated_graph, gated_ticket, {"ready": "no"})
check("gate blocks", result.get("gate_blocked") is True)
check("cursor unchanged after gate", gated_ticket.cursor == "gated.confirm")
check("no history after gate block", len(gated_ticket.history) == 0)

# Now with gate-passing response
result = do_respond(gated_graph, gated_ticket, {"ready": "yes"})
check("gate passes", "gate_blocked" not in result)
check("advances after gate pass", gated_ticket.cursor == "gated.done")
check("1 step after gate pass", len(gated_ticket.history) == 1)

# ===========================================================================
# Test 11a2: Acyclic retry (spawn forward)
# ===========================================================================
print("\n=== Test 11a2: Acyclic retry (spawn forward) ===\n")

from templates.diagnostic import Diagnostic as DiagForRetry
diag_retry = DiagForRetry().build()

# Verify test node has retry spec (not loop-back edges)
test_node = diag_retry.nodes["diagnostic.test"]
check("test has retry spec", test_node.retry is not None)
check("retry names correct", test_node.retry["nodes"] == ["hypothesize", "test"])
# Test should have exactly 1 edge (forward to conclude), no loop-back
test_node_edges = test_node.edges
check("test has 1 edge", len(test_node_edges) == 1, str(test_node_edges))
check("test forward to conclude", test_node_edges[0].get("to") == "diagnostic.conclude")

# Validate the graph is acyclic
errors = diag_retry.validate()
check("diagnostic is acyclic", len(errors) == 0, str(errors))

# Run with a failed hypothesis — should spawn retry nodes forward
retry_result = auto_run(diag_retry, {
    "diagnostic.start": {"objective": "test", "ready": "yes"},
    "diagnostic.observe": {"symptoms": "X", "onset": "now"},
    "diagnostic.hypothesize": [
        {"hypothesis": "First guess", "confidence": "low"},
        {"hypothesis": "Second guess", "confidence": "high"},
    ],
    "diagnostic.test": [
        {"test_description": "Check A", "test_result": "Failed",
         "hypothesis_confirmed": "no"},
        {"test_description": "Check B", "test_result": "Confirmed",
         "hypothesis_confirmed": "yes"},
    ],
})
check("retry completes", retry_result["state"] == "complete")
check("retry takes 9 steps", retry_result["steps"] == 9,
      f"steps={retry_result['steps']}")

# Verify spawned nodes exist in the graph
retry_graph = retry_result["graph"]
check("hypothesize-2 spawned", "diagnostic.hypothesize-2" in retry_graph.nodes)
check("test-2 spawned", "diagnostic.test-2" in retry_graph.nodes)

# Verify traversal path includes spawned nodes
visited_nodes = [h["node_id"] for h in retry_result["history"]]
check("visits hypothesize-2", "diagnostic.hypothesize-2" in visited_nodes)
check("visits test-2", "diagnostic.test-2" in visited_nodes)
# Original hypothesize and test visited once each
check("original hypothesize once", visited_nodes.count("diagnostic.hypothesize") == 1)
check("original test once", visited_nodes.count("diagnostic.test") == 1)

# Also verify incident inherits the retry spec
inc_retry = Incident().build()
inc_test = inc_retry.nodes["incident.test"]
check("incident test has retry", inc_test.retry is not None)
# Forward from incident's test should go to contain (not conclude)
forward_targets = [e["to"] for e in inc_test.edges if not e.get("condition")]
check("incident test forward to contain", "incident.contain" in forward_targets,
      str(forward_targets))

# ===========================================================================
# Test 11b: Deep diff
# ===========================================================================
print("\n=== Test 11b: Deep diff ===\n")

tpl3 = Diagnostic()
tpl_graph3 = tpl3.build()
doc3 = tpl3.instantiate("DEEPDIFF")

# Tamper with prompt
doc3.nodes["diagnostic.start"].prompt = "Tampered prompt"
diff3 = doc3.diff(tpl_graph3)
modified_nodes = {nid for nid, _ in diff3["modified"]}
check("prompt tamper detected", "diagnostic.start" in modified_nodes)
check("not compliant", not diff3["compliant"])

# Reset prompt, tamper with edges
doc3.nodes["diagnostic.start"].prompt = tpl_graph3.nodes["diagnostic.start"].prompt
doc3.nodes["diagnostic.start"].edges = [{"to": "diagnostic.close"}]
diff3 = doc3.diff(tpl_graph3)
modified_nodes = {nid for nid, _ in diff3["modified"]}
check("edge tamper detected", "diagnostic.start" in modified_nodes)

# ===========================================================================
# Test 11c: Inline response CLI
# ===========================================================================
print("\n=== Test 11c: Inline response ===\n")

import subprocess
proto_dir = os.path.dirname(os.path.abspath(__file__))
# Create a doc
subprocess.run([sys.executable, "engine.py", "start", "templates.logic_puzzle",
                "--doc-id", "INLINE-001"], capture_output=True, cwd=proto_dir)
# Respond with inline JSON
result = subprocess.run(
    [sys.executable, "engine.py", "respond", ".documents/INLINE-001.json",
     "--response", '{"understood": "yes"}'],
    capture_output=True, text=True, cwd=proto_dir)
check("inline respond works", result.returncode == 0, result.stderr[:200] if result.stderr else "")
if result.returncode == 0:
    data = json.loads(result.stdout)
    check("inline advances cursor", "puzzle.work" in data.get("cursor", ""), data.get("cursor", ""))


# ===========================================================================
# Test 11d: Cycle detection
# ===========================================================================
print("\n=== Test 11d: Cycle detection ===\n")

# Build a graph with a deliberate cycle
cyclic = Graph("cyclic-test")
cyclic.entry_point = "a"
cyclic.nodes["a"] = Node(id="a", prompt="Step A", edges=[{"to": "b"}])
cyclic.nodes["b"] = Node(id="b", prompt="Step B", edges=[{"to": "c"}])
cyclic.nodes["c"] = Node(id="c", prompt="Step C", edges=[{"to": "a"}])  # cycle!
errors = cyclic.validate()
check("cycle detected", any("cycle" in e.lower() for e in errors), str(errors))

# Acyclic should pass
acyclic = Graph("acyclic-test")
acyclic.entry_point = "x"
acyclic.nodes["x"] = Node(id="x", prompt="X", edges=[{"to": "y"}])
acyclic.nodes["y"] = Node(id="y", prompt="Y", edges=[{"to": "z"}])
acyclic.nodes["z"] = Node(id="z", prompt="Z", terminal=True, edges=[])
errors = acyclic.validate()
check("acyclic passes", len(errors) == 0, str(errors))

# All templates must be acyclic
for tpl_path in ["templates.diagnostic", "templates.repair",
                  "templates.incident", "templates.logic_puzzle",
                  "templates.code_review", "templates.safety_incident"]:
    cls = load_template_class(tpl_path)
    g = cls().build()
    errors = g.validate()
    check(f"{tpl_path} acyclic", len(errors) == 0, str(errors))


# ===========================================================================
# Test 11e: spawn_retry mechanics
# ===========================================================================
print("\n=== Test 11e: spawn_retry mechanics ===\n")

# Build a minimal graph with retry
retry_g = Graph("retry-mech")
retry_g.entry_point = "retry-mech.a"
retry_g.nodes["retry-mech.a"] = Node(
    id="retry-mech.a", prompt="A",
    evidence_schema={"ok": Field("enum", required=True, values=["yes", "no"])},
    retry={"when": "response.get('ok') != 'yes'", "nodes": ["a"]},
    edges=[{"to": "retry-mech.b"}],
)
retry_g.nodes["retry-mech.b"] = Node(
    id="retry-mech.b", prompt="B", terminal=True, edges=[],
)

# Trigger retry
first = spawn_retry(retry_g, retry_g.nodes["retry-mech.a"], {"ok": "no"})
check("spawn returns first clone", first == "retry-mech.a-2", str(first))
check("clone exists", "retry-mech.a-2" in retry_g.nodes)
check("clone points to b", retry_g.nodes["retry-mech.a-2"].edges == [{"to": "retry-mech.b"}])
check("original redirected to clone", retry_g.nodes["retry-mech.a"].edges[0]["to"] == "retry-mech.a-2")
check("clone inherits retry", retry_g.nodes["retry-mech.a-2"].retry is not None)

# Trigger again — should get suffix 3
second = spawn_retry(retry_g, retry_g.nodes["retry-mech.a-2"], {"ok": "no"})
check("second spawn suffix 3", second == "retry-mech.a-3", str(second))
check("a-3 points to b", retry_g.nodes["retry-mech.a-3"].edges == [{"to": "retry-mech.b"}])

# No trigger when condition not met
no_spawn = spawn_retry(retry_g, retry_g.nodes["retry-mech.a-3"], {"ok": "yes"})
check("no spawn on pass", no_spawn is None)


# ===========================================================================
# Test 12: Edge cases
# ===========================================================================
print("\n=== Test 12: Edge cases ===\n")

# Empty graph
empty = Graph("empty")
errors = empty.validate()
check("empty graph invalid", len(errors) > 0)

# Template with no define() override
class EmptyTemplate(Template):
    id = "empty"
    name = "Empty"

g = EmptyTemplate().build()
check("empty template 0 nodes", len(g.nodes) == 0)

# Load template by explicit class name
cls = load_template_class("templates.diagnostic.Diagnostic")
check("explicit class load", cls.__name__ == "Diagnostic")

# Load abstract template should fail
try:
    cls = load_template_class("templates.procedure_base")
    check("abstract load fails", False, "Should have raised")
except ValueError:
    check("abstract load fails", True)


# ===========================================================================
# Summary
# ===========================================================================
print(f"\n{'=' * 60}")
print(f"  Results: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
print(f"{'=' * 60}\n")

sys.exit(1 if FAIL else 0)
