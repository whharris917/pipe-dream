#!/usr/bin/env python3
"""Generate YAML workflow files from a ticket's collected evidence.

Called by hooks in the meta-workflow to produce template and instance directories.

Usage:
  python generate.py template <ticket-json> <output-dir>
  python generate.py instance <ticket-json> <template-dir> <output-dir>
"""

import sys
import json
import yaml
import os
from pathlib import Path


def generate_template(ticket_path: str, output_dir: str):
    """Generate a template workflow from evidence collected during authoring."""
    with open(ticket_path, "r", encoding="utf-8") as f:
        ticket = json.load(f)

    responses = ticket["responses"]
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Extract template metadata from m.start
    start_resp = responses.get("m.start", {})
    template_id = start_resp.get("template_id", "tpl")
    template_name = start_resp.get("template_name", "Untitled Template")
    template_desc = start_resp.get("template_description", "")

    # Collect all step definitions from repeated visits to m.define-step
    step_resps = responses.get("m.define-step", [])
    if isinstance(step_resps, dict):
        step_resps = [step_resps]

    # Collect field definitions (list of lists, one per step)
    field_resps = responses.get("m.define-field", [])
    if isinstance(field_resps, dict):
        field_resps = [field_resps]

    # Collect edge definitions
    edge_resps = responses.get("m.define-edges", [])
    if isinstance(edge_resps, dict):
        edge_resps = [edge_resps]

    # Build step data structures
    steps = []
    field_idx = 0
    edge_idx = 0

    for step_resp in step_resps:
        step_id = step_resp.get("step_id", f"step-{len(steps)+1}")
        full_id = f"{template_id}.{step_id}"
        num_fields = int(step_resp.get("num_fields", 0))
        num_edges = int(step_resp.get("num_edges", 1))

        # Gather fields for this step
        fields = {}
        for i in range(num_fields):
            if field_idx < len(field_resps):
                fr = field_resps[field_idx]
                fname = fr.get("field_name", f"field_{i+1}")
                fdef = {"type": fr.get("field_type", "text")}
                if fr.get("field_required", "yes") == "yes":
                    fdef["required"] = True
                if fr.get("field_values"):
                    fdef["values"] = [v.strip() for v in fr["field_values"].split(",")]
                if fr.get("field_hint"):
                    fdef["hint"] = fr["field_hint"]
                fields[fname] = fdef
                field_idx += 1

        # Gather edges for this step
        edges = []
        for i in range(num_edges):
            if edge_idx < len(edge_resps):
                er = edge_resps[edge_idx]
                edge = {"to": f"{template_id}.{er.get('target_step', 'end')}"}
                if er.get("condition"):
                    edge["condition"] = er["condition"]
                edges.append(edge)
                edge_idx += 1

        steps.append({
            "step_id": step_id,
            "full_id": full_id,
            "prompt": step_resp.get("step_prompt", ""),
            "context": step_resp.get("step_context", ""),
            "performer": step_resp.get("performer", "initiator"),
            "terminal": step_resp.get("is_terminal", "no") == "yes",
            "fields": fields,
            "edges": edges,
        })

    # Write _graph.yaml
    graph_meta = {
        "graph": {
            "id": template_id,
            "name": template_name,
            "version": "1.0",
            "entry_point": f"{template_id}.{steps[0]['step_id']}" if steps else "",
            "description": template_desc,
        }
    }
    with open(out / "_graph.yaml", "w", encoding="utf-8") as f:
        yaml.dump(graph_meta, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # Write each step as a YAML file
    for step in steps:
        node_data = {
            "node": {
                "id": step["full_id"],
                "prompt": step["prompt"],
            }
        }
        if step["context"]:
            node_data["node"]["context"] = step["context"]
        if step["performer"] != "initiator":
            node_data["node"]["performer"] = step["performer"]
        if step["terminal"]:
            node_data["node"]["terminal"] = True
        if step["fields"]:
            node_data["node"]["evidence_schema"] = step["fields"]
        if step["edges"]:
            node_data["node"]["edges"] = step["edges"]

        filename = step["step_id"] + ".yaml"
        with open(out / filename, "w", encoding="utf-8") as f:
            yaml.dump(node_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"Generated template: {len(steps)} nodes in {output_dir}")
    return steps


def generate_instance(ticket_path: str, template_dir: str, output_dir: str):
    """Generate an instance workflow by specializing a template."""
    with open(ticket_path, "r", encoding="utf-8") as f:
        ticket = json.load(f)

    responses = ticket["responses"]
    tpl_path = Path(template_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Load template metadata
    with open(tpl_path / "_graph.yaml", "r", encoding="utf-8") as f:
        tpl_meta = yaml.safe_load(f)
    tpl_id = tpl_meta["graph"]["id"]

    # Instance metadata from m.inst-start
    inst_resp = responses.get("m.inst-start", {})
    inst_name = inst_resp.get("instance_name", "Untitled Instance")
    inst_desc = inst_resp.get("instance_description", "")

    # Load all template node files
    tpl_nodes = []
    for yaml_file in sorted(tpl_path.glob("*.yaml")):
        if yaml_file.stem.startswith("_"):
            continue
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data:
            tpl_nodes.append((yaml_file.stem, data))

    # Collect specializations from repeated visits to m.inst-specialize
    spec_resps = responses.get("m.inst-specialize", [])
    if isinstance(spec_resps, dict):
        spec_resps = [spec_resps]

    # Build a lookup of specializations by step_id
    specializations = {}
    for sr in spec_resps:
        sid = sr.get("step_id", "")
        specializations[sid] = sr

    # Write instance _graph.yaml
    inst_meta = {
        "graph": {
            "id": tpl_id,
            "name": inst_name,
            "version": "1.0",
            "entry_point": tpl_meta["graph"].get("entry_point", ""),
            "description": inst_desc,
        }
    }
    with open(out / "_graph.yaml", "w", encoding="utf-8") as f:
        yaml.dump(inst_meta, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # Write each node, applying specializations
    for stem, data in tpl_nodes:
        node = data.get("node", data)
        node_id = node.get("id", "")
        # Extract the step part of the ID (after the prefix)
        step_id = node_id.split(".", 1)[-1] if "." in node_id else node_id

        spec = specializations.get(step_id, {})

        if spec.get("specialized_prompt"):
            node["prompt"] = spec["specialized_prompt"]
        if spec.get("specialized_context"):
            node["context"] = spec["specialized_context"]

        # Specialize hints in evidence schema
        if spec.get("specialized_hints") and "evidence_schema" in node:
            hint_lines = spec["specialized_hints"].split(";")
            schema_keys = list(node["evidence_schema"].keys())
            for i, hint in enumerate(hint_lines):
                hint = hint.strip()
                if hint and i < len(schema_keys):
                    key = schema_keys[i]
                    if isinstance(node["evidence_schema"][key], dict):
                        node["evidence_schema"][key]["hint"] = hint

        out_data = {"node": node}
        with open(out / f"{stem}.yaml", "w", encoding="utf-8") as f:
            yaml.dump(out_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"Generated instance: {len(tpl_nodes)} nodes in {output_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python generate.py template <ticket-json> <output-dir>")
        print("  python generate.py instance <ticket-json> <template-dir> <output-dir>")
        sys.exit(1)

    mode = sys.argv[1]
    if mode == "template":
        generate_template(sys.argv[2], sys.argv[3])
    elif mode == "instance":
        generate_instance(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)
