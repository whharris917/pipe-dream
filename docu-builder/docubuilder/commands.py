"""Parse and execute commands from the command zone."""

import shlex
from docubuilder import model
from docubuilder.model import COLUMN_MODES, VALID_COLUMN_TYPES


def parse_and_execute(doc: dict, command_text: str, performer: str = "agent",
                      current_section: str | None = None) -> str:
    """Parse a command string and execute it against the document.
    Returns a status message."""
    command_text = command_text.strip()
    if not command_text:
        return "No command entered."

    try:
        parts = shlex.split(command_text)
    except ValueError as e:
        return f"Error parsing command: {e}"

    if not parts:
        return "No command entered."

    cmd = parts[0].lower()

    try:
        if cmd == "nav":
            return _cmd_nav(doc, parts)
        elif cmd == "view_all":
            return "__VIEW_ALL__"
        elif cmd == "save_template":
            return _cmd_save_template(doc, command_text)
        elif cmd == "add_section":
            return _cmd_add_section(doc, parts)
        elif cmd == "move_section":
            return _cmd_move_section(doc, parts)
        elif cmd == "add_text":
            return _cmd_add_text(doc, parts)
        elif cmd == "edit_text":
            return _cmd_edit_text(doc, parts)
        elif cmd == "add_table":
            return _cmd_add_table(doc, parts)
        elif cmd == "add_column":
            return _cmd_add_column(doc, parts)
        elif cmd == "rename_column":
            return _cmd_rename_column(doc, parts)
        elif cmd == "move_column":
            return _cmd_move_column(doc, parts)
        elif cmd == "add_row":
            return _cmd_add_row(doc, parts, performer)
        elif cmd == "delete_section":
            return _cmd_delete_section(doc, parts)
        elif cmd == "delete_element":
            return _cmd_delete_element(doc, parts)
        elif cmd == "delete_row":
            return _cmd_delete_row(doc, parts)
        elif cmd == "enforce":
            return _cmd_enforce(doc, parts)
        elif cmd == "finalize":
            return _cmd_finalize(doc)
        elif cmd == "inspect":
            return _cmd_inspect(doc, parts, current_section)
        elif cmd == "exec":
            return _cmd_exec(doc, parts, performer)
        elif cmd == "amend":
            return _cmd_amend(doc, parts, performer)
        else:
            return f"Unknown command: '{cmd}'. Check the command reference above."
    except (ValueError, IndexError, KeyError) as e:
        return f"Error: {e}"


def _cmd_nav(doc: dict, parts: list) -> str:
    if len(parts) < 2:
        return "Usage: nav <section_id>"
    section_id = parts[1]
    if section_id not in doc["sections"]:
        return f"Error: Section '{section_id}' does not exist."
    return f"__NAV__:{section_id}"


def _cmd_add_section(doc: dict, parts: list) -> str:
    if len(parts) < 3:
        return "Usage: add_section <id> <title> [before=X] [after=X]"
    section_id = parts[1]
    position = None
    title_parts = []
    for part in parts[2:]:
        if part.startswith("before="):
            ref = part.split("=", 1)[1]
            idx, _ = model.resolve_section_index(doc, ref)
            position = idx
        elif part.startswith("after="):
            ref = part.split("=", 1)[1]
            idx, _ = model.resolve_section_index(doc, ref)
            position = idx + 1
        else:
            title_parts.append(part)
    title = " ".join(title_parts)
    if not title:
        return "Error: No title provided."
    model.add_section(doc, section_id, title, position=position)
    return f"__NAV_NEW__:{section_id}"


def _cmd_move_section(doc: dict, parts: list) -> str:
    if len(parts) < 3:
        return "Usage: move_section <section_id> before=<ref> | after=<ref>"
    section_id = parts[1]
    position = None
    for part in parts[2:]:
        if part.startswith("before="):
            ref = part.split("=", 1)[1]
            idx, _ = model.resolve_section_index(doc, ref)
            position = idx
        elif part.startswith("after="):
            ref = part.split("=", 1)[1]
            idx, _ = model.resolve_section_index(doc, ref)
            position = idx + 1
    if position is None:
        return "Error: Specify before=<ref> or after=<ref>."
    model.move_section(doc, section_id, position)
    return f"Section '{section_id}' moved."


def _cmd_add_text(doc: dict, parts: list) -> str:
    if len(parts) < 4:
        return "Usage: add_text <section_id> <name> <text> [before=X] [after=X]"
    section_id = parts[1]
    name = parts[2]
    position = None
    text_parts = []
    for part in parts[3:]:
        if part.startswith("before="):
            ref = part.split("=", 1)[1]
            position = model.resolve_element_index(doc, section_id, ref)
        elif part.startswith("after="):
            ref = part.split("=", 1)[1]
            position = model.resolve_element_index(doc, section_id, ref) + 1
        else:
            text_parts.append(part)
    text = " ".join(text_parts)
    if not text:
        return "Error: No text content provided."
    idx = model.add_text(doc, section_id, text, name=name, position=position)
    return f"Text block '{name}' added at index {idx} in section '{section_id}'."


def _cmd_edit_text(doc: dict, parts: list) -> str:
    if len(parts) < 4:
        return "Usage: edit_text <section_id> <elem_id> <new_text>"
    section_id = parts[1]
    el_idx = model.resolve_element_index(doc, section_id, parts[2])
    text = " ".join(parts[3:])
    model.edit_text(doc, section_id, el_idx, text)
    return f"Text block '{parts[2]}' updated."


def _cmd_add_table(doc: dict, parts: list) -> str:
    if len(parts) < 4:
        return "Usage: add_table <section_id> <name> col1:type1 col2:type2 ... [id_prefix=X] [sequential=false] [before=X] [after=X]"
    section_id = parts[1]
    table_name = parts[2]
    columns = []
    id_prefix = None
    sequential = True  # default: sequential
    position = None
    valid_types = VALID_COLUMN_TYPES
    for col_spec in parts[3:]:
        if col_spec.startswith("id_prefix="):
            id_prefix = col_spec.split("=", 1)[1]
            continue
        if col_spec.startswith("sequential="):
            val = col_spec.split("=", 1)[1].lower()
            sequential = val not in ("false", "no", "0")
            continue
        if col_spec.startswith("before="):
            ref = col_spec.split("=", 1)[1]
            position = model.resolve_element_index(doc, section_id, ref)
            continue
        if col_spec.startswith("after="):
            ref = col_spec.split("=", 1)[1]
            position = model.resolve_element_index(doc, section_id, ref) + 1
            continue
        if ":" not in col_spec:
            return f"Invalid column spec '{col_spec}'. Use 'name:type' format."
        col_name, col_type = col_spec.rsplit(":", 1)
        if col_type not in valid_types:
            return f"Unknown column type '{col_type}'. Valid: {', '.join(sorted(valid_types))}"
        columns.append({"name": col_name, "type": col_type})
    idx = model.add_table(doc, section_id, table_name, columns, sequential=sequential, position=position)
    if id_prefix:
        section = model._get_section(doc, section_id)
        section["elements"][idx]["id_prefix"] = id_prefix
    return f"Table '{table_name}' added at index {idx} in section '{section_id}'."


def _cmd_add_column(doc: dict, parts: list) -> str:
    if len(parts) < 4:
        return "Usage: add_column <section_id> <tbl_id> <name>:<type> [before=X] [after=X]"
    section_id = parts[1]
    tbl_idx = model.resolve_element_index(doc, section_id, parts[2])
    col_spec = None
    position = None
    table = model._get_table(doc, section_id, tbl_idx)
    valid_types = VALID_COLUMN_TYPES
    for part in parts[3:]:
        if part.startswith("before="):
            ref = part.split("=", 1)[1]
            if ref not in table["column_order"]:
                return f"Error: Column '{ref}' does not exist."
            position = table["column_order"].index(ref)
        elif part.startswith("after="):
            ref = part.split("=", 1)[1]
            if ref not in table["column_order"]:
                return f"Error: Column '{ref}' does not exist."
            position = table["column_order"].index(ref) + 1
        else:
            col_spec = part
    if not col_spec or ":" not in col_spec:
        return "Error: Column spec must be 'name:type' format."
    col_name, col_type = col_spec.rsplit(":", 1)
    if col_type not in valid_types:
        return f"Unknown column type '{col_type}'. Valid: {', '.join(sorted(valid_types))}"
    model.add_column(doc, section_id, tbl_idx, col_name, col_type, position=position)
    return f"Column '{col_name}' added to table."


def _cmd_rename_column(doc: dict, parts: list) -> str:
    if len(parts) < 5:
        return "Usage: rename_column <section_id> <tbl_id> <old_name> <new_name>"
    section_id = parts[1]
    tbl_idx = model.resolve_element_index(doc, section_id, parts[2])
    old_name = parts[3]
    new_name = parts[4]
    model.rename_column(doc, section_id, tbl_idx, old_name, new_name)
    return f"Column '{old_name}' renamed to '{new_name}'."


def _cmd_move_column(doc: dict, parts: list) -> str:
    if len(parts) < 4:
        return "Usage: move_column <section_id> <tbl_id> <col_name> before=<ref> | after=<ref>"
    section_id = parts[1]
    tbl_idx = model.resolve_element_index(doc, section_id, parts[2])
    col_name = parts[3]
    table = model._get_table(doc, section_id, tbl_idx)
    position = None
    for part in parts[4:]:
        if part.startswith("before="):
            ref = part.split("=", 1)[1]
            if ref not in table["column_order"]:
                return f"Error: Column '{ref}' does not exist."
            position = table["column_order"].index(ref)
        elif part.startswith("after="):
            ref = part.split("=", 1)[1]
            if ref not in table["column_order"]:
                return f"Error: Column '{ref}' does not exist."
            position = table["column_order"].index(ref) + 1
    if position is None:
        return "Error: Specify before=<ref> or after=<ref>."
    model.move_column(doc, section_id, tbl_idx, col_name, position)
    return f"Column '{col_name}' moved."


def _cmd_add_row(doc: dict, parts: list, performer: str) -> str:
    if len(parts) < 3:
        return "Usage: add_row <section_id> <tbl_id> [col=val ...]"
    section_id = parts[1]
    table_index = model.resolve_element_index(doc, section_id, parts[2])
    table = model._get_table(doc, section_id, table_index)
    values = {}
    for kv in parts[3:]:
        if "=" not in kv:
            return f"Invalid value spec '{kv}'. Use 'column=value' format."
        k, v = kv.split("=", 1)
        if k not in table["columns"]:
            return f"Error: Column '{k}' does not exist in table. Available: {', '.join(table['column_order'])}"
        values[k] = v
    idx = model.add_row(doc, section_id, table_index, values)
    return f"Row added at index {idx}."


def _cmd_delete_section(doc: dict, parts: list) -> str:
    if len(parts) < 2:
        return "Usage: delete_section <section_id>"
    model.delete_section(doc, parts[1])
    return f"Section '{parts[1]}' deleted."


def _cmd_delete_element(doc: dict, parts: list) -> str:
    if len(parts) < 3:
        return "Usage: delete_element <section_id> <elem_id>"
    idx = model.resolve_element_index(doc, parts[1], parts[2])
    model.delete_element(doc, parts[1], idx)
    return f"Element '{parts[2]}' deleted from section '{parts[1]}'."


def _cmd_delete_row(doc: dict, parts: list) -> str:
    if len(parts) < 4:
        return "Usage: delete_row <section_id> <tbl_id> <row_index>"
    tbl_idx = model.resolve_element_index(doc, parts[1], parts[2])
    model.delete_row(doc, parts[1], tbl_idx, int(parts[3]))
    return f"Row {parts[3]} deleted."


def _cmd_enforce(doc: dict, parts: list) -> str:
    if len(parts) < 2:
        return "Usage: enforce <section_id> [elem_id] [row_idx]"
    model._require_authoring(doc)
    section_id = parts[1]
    section = model._get_section(doc, section_id)

    if len(parts) == 2:
        section["enforced"] = True
        return f"Section '{section_id}' enforced."
    elif len(parts) == 3:
        el_idx = model.resolve_element_index(doc, section_id, parts[2])
        section["elements"][el_idx]["enforced"] = True
        return f"Element '{parts[2]}' in section '{section_id}' enforced."
    else:
        el_idx = model.resolve_element_index(doc, section_id, parts[2])
        row_idx = int(parts[3])
        table = model._get_table(doc, section_id, el_idx)
        table["rows"][row_idx]["enforced"] = True
        return f"Row {row_idx} in '{parts[2]}' enforced."


def _cmd_save_template(doc: dict, raw_command: str) -> str:
    # Extract path from raw command text to avoid shlex mangling backslashes
    rest = raw_command.strip()
    # Remove the command name
    if rest.lower().startswith("save_template"):
        rest = rest[len("save_template"):].strip()
    if not rest:
        return "Usage: save_template <file_path>"
    # Strip surrounding quotes if present
    if (rest.startswith('"') and rest.endswith('"')) or \
       (rest.startswith("'") and rest.endswith("'")):
        rest = rest[1:-1]
    model.save(doc, rest)
    return f"__TEMPLATE_SAVED__:{rest}"


def _cmd_finalize(doc: dict) -> str:
    if not doc["sections"]:
        return "Error: Cannot finalize a document with no sections."
    model.transition_to_execution(doc)
    return "Document transitioned to EXECUTION phase. Structure is now frozen."


def _cmd_inspect(doc: dict, parts: list, current_section: str | None = None) -> str:
    if len(parts) < 2:
        return "Usage: inspect <element_ref> (e.g., inspect TBL-0, inspect purpose)"
    ref = parts[1]
    phase = doc["system_properties"]["phase"]

    # Try as section reference
    sid = None
    if ref in doc["sections"]:
        sid = ref
    else:
        ref_upper = ref.upper()
        if ref_upper.startswith("SEC-"):
            try:
                _, sid = model.resolve_section_index(doc, ref)
            except ValueError:
                pass
    if sid:
        return f"__INSPECT__:{_inspect_section(doc, sid, phase)}"

    # Try as element reference — prefer current section, then search all
    search_order = []
    if current_section and current_section in doc["sections"]:
        search_order.append(current_section)
    for section_id in doc["sections"]:
        if section_id not in search_order:
            search_order.append(section_id)

    for section_id in search_order:
        section = doc["sections"][section_id]
        try:
            idx = model.resolve_element_index(doc, section_id, ref)
            el = section["elements"][idx]
            type_id = model.element_type_id(section, idx)
            if el["type"] == "table":
                return f"__INSPECT__:{_inspect_table(el, type_id, section_id, phase)}"
            elif el["type"] == "text":
                return f"__INSPECT__:{_inspect_text(el, type_id, section_id, phase)}"
        except (ValueError, KeyError):
            continue
    return f"Error: No element '{ref}' found."


# Column type display labels (reuse from renderer)
_COL_TYPE_LABELS = {
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

# Mode display labels
_MODE_LABELS = {
    "executable": "Executable",
    "auto": "Auto",
    "non-executable": "Non-Executable",
}


def _inspect_table(el: dict, type_id: str, section_id: str, phase: str) -> str:
    name = el["name"]
    lines = [f"**Inspecting `{type_id}:{name}` in section `{section_id}`**"]
    lines.append("")

    # Column properties table
    lines.append("Column Properties:")
    lines.append("")
    lines.append("| # | Name | Type | Mode |")
    lines.append("| --- | --- | --- | --- |")
    for i, col_name in enumerate(el["column_order"]):
        col_type = el["columns"][col_name]["type"]
        type_label = _COL_TYPE_LABELS.get(col_type, col_type)
        mode = _MODE_LABELS.get(COLUMN_MODES.get(col_type, ""), "Unknown")
        lines.append(f"| {i} | {col_name} | {type_label} | {mode} |")
    lines.append("")

    # Table properties
    lines.append(f"Rows: {len(el['rows'])}")
    lines.append(f"Sequential: {'Yes' if el.get('sequential') else 'No'}")
    lines.append("")

    # Contextual commands
    if phase == "authoring":
        lines.append("Available actions:")
        lines.append(f"- Rename a column: `rename_column {section_id} {type_id} <old_name> <new_name>`")
        lines.append(f"- Add a column: `add_column {section_id} {type_id} <name>:<type> [before=X] [after=X]`")
        lines.append(f"- Reorder a column: `move_column {section_id} {type_id} <col> before=<ref>`")
        lines.append(f"- Add a row: `add_row {section_id} {type_id} [col=val ...]`")
        lines.append(f"- Delete a row: `delete_row {section_id} {type_id} <row_idx>`")
        lines.append(f"- Delete this table: `delete_element {section_id} {type_id}`")
    else:
        lines.append("Available actions:")
        lines.append(f"- Execute a row: `exec {section_id} {type_id} <row_idx> <col>=<val> ...`")
        lines.append(f"- Amend a cell: `amend {section_id} {type_id} <row_idx> <col>=<val> reason=<text>`")
        if el.get("extendable"):
            lines.append(f"- Add a row: `add_row {section_id} {type_id} [col=val ...]`")

    return "\n".join(lines)


def _inspect_text(el: dict, type_id: str, section_id: str, phase: str) -> str:
    name = el["name"]
    lines = [f"**Inspecting `{type_id}:{name}` in section `{section_id}`**"]
    lines.append("")
    if phase == "authoring":
        lines.append("Available actions:")
        lines.append(f"- Edit content: `edit_text {section_id} {type_id} <new_text>`")
        lines.append(f"- Delete: `delete_element {section_id} {type_id}`")
    else:
        lines.append("Text blocks are read-only during execution.")
    return "\n".join(lines)


def _inspect_section(doc: dict, sid: str, phase: str) -> str:
    sec = doc["sections"][sid]
    lines = [f"**Inspecting section `{sid}`, titled \"{sec['title']}\"**"]
    lines.append("")
    lines.append(f"Elements: {len(sec['elements'])}")
    lines.append("")
    if phase == "authoring":
        lines.append("Available actions:")
        lines.append(f"- Navigate here: `nav {sid}`")
        lines.append(f"- Add text: `add_text {sid} <name> <text>`")
        lines.append(f"- Add table: `add_table {sid} <name> col:type ...`")
        lines.append(f"- Delete section: `delete_section {sid}`")
        lines.append(f"- Enforce section: `enforce {sid}`")
    else:
        lines.append("Available actions:")
        lines.append(f"- Navigate here: `nav {sid}`")
    return "\n".join(lines)


def _cmd_exec(doc: dict, parts: list, performer: str) -> str:
    if len(parts) < 5:
        return "Usage: exec <section_id> <tbl_id> <row_index> <column>=<value>"
    section_id = parts[1]
    table_index = model.resolve_element_index(doc, section_id, parts[2])
    row_index = int(parts[3])
    for kv in parts[4:]:
        if "=" not in kv:
            return f"Invalid spec '{kv}'. Use 'column=value' format."
        col, val = kv.split("=", 1)
        model.execute_cell(doc, section_id, table_index, row_index, col, val, performer)
    return f"Executed row {row_index} in table {table_index}."


def _cmd_amend(doc: dict, parts: list, performer: str) -> str:
    if len(parts) < 6:
        return "Usage: amend <section_id> <tbl_id> <row_index> <column>=<value> reason=<text>"
    section_id = parts[1]
    table_index = model.resolve_element_index(doc, section_id, parts[2])
    row_index = int(parts[3])

    reason = None
    assignments = []
    for kv in parts[4:]:
        if "=" not in kv:
            return f"Invalid spec '{kv}'. Use 'column=value' format."
        k, v = kv.split("=", 1)
        if k == "reason":
            reason = v
        else:
            assignments.append((k, v))

    if not reason:
        return "Amendment requires a reason. Add reason=<text> to the command."

    for col, val in assignments:
        model.amend_cell(doc, section_id, table_index, row_index, col, val, performer, reason)
    return f"Amended row {row_index} in table {table_index}."
