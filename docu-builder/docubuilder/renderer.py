"""Render a document to a markdown view for agents."""

from docubuilder.model import (
    get_cell_status, evaluate_prerequisites, is_row_complete,
    element_type_id, col_is_executable,
)

# Column type display abbreviations
COL_TYPE_LABELS = {
    "id": "ID",
    "design": "Design",
    "prerequisite": "Prereq",
    "recorded_value": "Recorded Value",
    "signature": "Signature",
    "witness": "Witness",
    "choice_list": "Choice List",
    "calculated": "Calculated",
    "cross_reference": "Cross Ref",
}


def render(doc: dict, current_section: str | None = None,
           show_all: bool = False,
           inspect_context: str = "") -> str:
    """Render a document to markdown. Shows one section at a time (minimal context).
    If current_section is None, shows the navigation overview.
    If show_all is True, renders all sections inline.
    inspect_context is displayed in the Context section below the command reference."""
    phase = doc["system_properties"]["phase"]
    doc_id = doc["system_properties"]["document_id"]
    title = doc["system_properties"]["title"]

    lines = []

    # Header
    lines.append(f"# {doc_id}: {title}")
    lines.append(f"Phase: {phase.upper()}")
    lines.append("")

    # Table of contents
    sections = doc["sections"]
    lines.append("## Table of Contents")
    if not sections:
        lines.append("(No sections. Use `add_section` to create one.)")
        lines.append("")
    else:
        lines.append("")
        lines.append("| SEC-NUM:ID | Title |")
        lines.append("| --- | --- |")
        for sec_num, (sid, sec) in enumerate(sections.items(), 1):
            tags = ""
            if sec.get("locked"):
                tags = " (LOCKED)"
            elif sec.get("enforced"):
                tags = " (ENFORCED)"
            lines.append(f"| `SEC-{sec_num}:{sid}` | {sec['title']}{tags} |")
        lines.append("")

    for sec_num, (sid, sec) in enumerate(sections.items(), 1):
        visible = show_all or sid == current_section
        toggle = "[-]" if visible else "[+]"
        tags = ""
        if sec.get("locked"):
            tags = " (LOCKED)"
        elif sec.get("enforced"):
            tags = " (ENFORCED)"
        lines.append(f"## {toggle} `SEC-{sec_num}:{sid}` - {sec['title']}{tags}")

        if visible:
            lines.append("")
            lines.append(_render_section_content(doc, sid, sec_num, phase))
        else:
            lines.append("")

    # Command zone
    if phase == "authoring":
        lines.append("## Authoring Commands")
        lines.append("")
        lines.append("| Command | Description |")
        lines.append("|---------|-------------|")
        lines.append("| `nav <section_id>` | Navigate to section |")
        lines.append("| `view_all` | Show all sections at once |")
        lines.append("| `add_section <id> <title> [before=X] [after=X]` | Add a new section |")
        lines.append("| `move_section <section_id> before=<ref>` | Move a section |")
        lines.append("| `add_text <section_id> <name> <text>` | Add text block |")
        lines.append("| `edit_text <section_id> <elem_id> <new_text>` | Edit a text block |")
        lines.append("| `add_table <section_id> <name> col:type ... [sequential=false]` | Add a table (see README for column types) |")
        lines.append("| `add_column <section_id> <tbl_id> name:type [before=X] [after=X]` | Add a column to a table |")
        lines.append("| `rename_column <section_id> <tbl_id> <old> <new>` | Rename a column |")
        lines.append("| `move_column <section_id> <tbl_id> <col> before=<ref>` | Reorder a column |")
        lines.append("| `add_row <section_id> <tbl_id> [col=val ...]` | Append a row to a table |")
        lines.append("| `delete_section <section_id>` | Delete an unlocked section |")
        lines.append("| `delete_element <section_id> <elem_id>` | Delete an unlocked element |")
        lines.append("| `delete_row <section_id> <tbl_id> <row_idx>` | Delete an unlocked row |")
        lines.append("| `enforce <section_id> [elem_id] [row_idx]` | Mark as enforced (locked in templates) |")
        lines.append("| `inspect <element_ref>` | Show element details and actions in Context section |")
        lines.append("| `save_template <file_path>` | Save as reusable template |")
        lines.append("| `finalize` | Freeze structure, enter execution phase |")
    else:
        lines.append("## Execution Commands")
        lines.append("")
        lines.append("| Command | Description |")
        lines.append("|---------|-------------|")
        lines.append("| `nav <section_id>` | Navigate to section |")
        lines.append("| `view_all` | Show all sections at once |")
        lines.append("| `exec <section_id> <tbl_id> <row_idx> <col>=<val> ...` | Fill executable cells |")
        lines.append("| `amend <section_id> <tbl_id> <row_idx> <col>=<val> reason=<text>` | Amend a cell |")
        lines.append("| `add_row <section_id> <tbl_id> col=val ...` | Add row (extendable tables only) |")
        lines.append("| `inspect <element_ref>` | Show element details and actions in Context section |")
    lines.append("")

    # Context section (after command reference)
    lines.append("## Context")
    lines.append("")
    if inspect_context:
        lines.append(inspect_context)
    else:
        lines.append("Use `inspect <element_id>` to see available actions for an element.")
    lines.append("")

    lines.append("---")
    lines.append("Write your command below, then save this file.")
    lines.append("")
    lines.append(">> ")

    return "\n".join(lines)


def _render_section_content(doc: dict, section_id: str, sec_num: int, phase: str) -> str:
    """Render a single section's content (without the header)."""
    section = doc["sections"][section_id]
    lines = []

    if not section["elements"]:
        lines.append("(No elements. Use `add_text` or `add_table` to add content.)")
        lines.append("")

    for i, element in enumerate(section["elements"]):
        type_id = element_type_id(section, i)
        if element["type"] == "text":
            lines.append(_render_text(element, type_id))
        elif element["type"] == "table":
            lines.append(_render_table(element, type_id, i, phase,
                                       doc=doc, section_id=section_id))
        lines.append("")

    return "\n".join(lines)


def _render_text(element: dict, type_id: str) -> str:
    """Render a text block."""
    name = element["name"]
    tag_parts = []
    if element.get("locked"):
        tag_parts.append("LOCKED")
    elif element.get("enforced"):
        tag_parts.append("ENFORCED")
    tags = f" ({', '.join(tag_parts)})" if tag_parts else ""

    label = f"[{type_id}:{name}]"
    lines = [f"<span style=\"color: gold\">**{label}**</span>{tags}"]
    lines.append("")
    for line in element["value"].split("\n"):
        lines.append(line)
    return "\n".join(lines)


def _exec_cell_indicator(element: dict, row: dict, ri: int, col_name: str,
                         row_blocked: bool, doc: dict, section_id: str,
                         flat_index: int) -> str:
    """Return `[READY]` or `[BLOCKED]` for an empty/reverted executable cell."""
    if row_blocked:
        return "`[BLOCKED]`"
    status = get_cell_status(
        element, row, ri, col_name,
        doc=doc, section_id=section_id,
        element_index=flat_index
    ) if doc else "ready"
    return "`[BLOCKED]`" if status == "blocked" else "`[READY]`"


def _render_table(element: dict, type_id: str, flat_index: int, phase: str,
                  doc: dict = None, section_id: str = None) -> str:
    """Render a table with its rows."""
    name = element["name"]
    tag_parts = []
    if element.get("locked"):
        tag_parts.append("LOCKED")
    elif element.get("enforced"):
        tag_parts.append("ENFORCED")
    if element.get("extendable"):
        tag_parts.append("EXTENDABLE")
    if element.get("sequential"):
        tag_parts.append("SEQ")
    tags = f" ({', '.join(tag_parts)})" if tag_parts else ""

    lines = [f"<span style=\"color: gold\">**[{type_id}:{name}]**</span>{tags}"]
    lines.append("")

    col_order = element["column_order"]
    col_defs = element["columns"]

    # Build header: Name (Type)
    headers = []
    for col_name in col_order:
        col_type = col_defs[col_name]["type"]
        type_label = COL_TYPE_LABELS.get(col_type, col_type)
        headers.append(f"{col_name} ({type_label})")

    # Build row data
    row_strs = []
    for ri, row in enumerate(element["rows"]):
        row_tags = []
        if row.get("locked"):
            row_tags.append("LOCKED")
        elif row.get("enforced"):
            row_tags.append("ENFORCED")
        # Evaluate row-level blocking (prerequisite check)
        row_blocked = False
        if phase == "execution" and doc and section_id:
            blocked, _ = evaluate_prerequisites(doc, section_id, flat_index, ri)
            if blocked:
                row_blocked = True

        cells = []
        for col_name in col_order:
            col_type = col_defs[col_name]["type"]

            # Auto-generate ID (use table-level prefix if set, else "R")
            if col_type == "id":
                prefix = element.get("id_prefix", "R")
                cells.append(f"{prefix}{ri + 1}")
            elif col_name in row["values"]:
                val = row["values"][col_name]
                if isinstance(val, dict) and "entries" in val:
                    # Execution audit trail -- show current value
                    if val["entries"] and val["entries"][-1].get("value") is not None:
                        current = val["entries"][-1]["value"]
                        # Count only user-initiated amendments (not system cascade reverts)
                        amendments = [e for e in val["entries"]
                                      if e.get("reason") and e.get("performer") != "system"
                                      and e.get("value") is not None]
                        if amendments:
                            cells.append(f"{current} (amended x{len(amendments)})")
                        else:
                            cells.append(current)
                    else:
                        # Reverted cell — check blocking
                        cells.append(_exec_cell_indicator(
                            element, row, ri, col_name, row_blocked,
                            doc, section_id, flat_index))
                else:
                    cells.append(str(val))
            else:
                # Empty cell
                if col_is_executable(col_type):
                    if phase == "authoring":
                        cells.append("`[EXECUTABLE]`")
                    else:
                        cells.append(_exec_cell_indicator(
                            element, row, ri, col_name, row_blocked,
                            doc, section_id, flat_index))
                else:
                    cells.append("N/A" if col_type == "prerequisite" else "")

        # Add BLOCKED tag for rows blocked by prerequisites
        if row_blocked:
            row_tags = ["BLOCKED"]

        row_strs.append((cells, row_tags))

    # Render markdown table
    # Header row
    header_line = "| " + " | ".join(headers) + " | |"
    sep_line = "|" + "|".join("---" for _ in headers) + "|---|"
    lines.append(header_line)
    lines.append(sep_line)

    # Data rows
    for ri, (cells, row_tags) in enumerate(row_strs):
        tags_str = ", ".join(row_tags)
        if tags_str:
            tags_str = f"({tags_str})"
        data_line = "| " + " | ".join(cells) + " | " + tags_str + " |"
        lines.append(data_line)

    # Extendable indicator
    if element.get("extendable") and phase == "execution":
        empty_cols = " | ".join("" for _ in headers)
        lines.append(f"| {empty_cols} | [+ Add Row] |")

    # Execution progress
    if phase == "execution":
        exec_cols = [c for c in col_order if col_is_executable(col_defs[c]["type"])]
        if exec_cols:
            total = len(element["rows"]) * len(exec_cols)
            filled = 0
            for row in element["rows"]:
                for ec in exec_cols:
                    val = row["values"].get(ec)
                    if isinstance(val, dict) and val.get("entries") and val["entries"][-1].get("value") is not None:
                        filled += 1
            lines.append("")
            lines.append(f"Progress: {filled}/{total} cells executed")

    return "\n".join(lines)
