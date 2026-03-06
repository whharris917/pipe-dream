"""Document data model. All state lives in a single JSON-serializable dict."""

import re
import json
import copy
from datetime import datetime, timezone


# --- Column mode classification ---
# Every column type belongs to exactly one mode:
#   executable    — filled by users during execution
#   auto          — system-evaluated, not user-fillable
#   non-executable — set during authoring, frozen during execution

COLUMN_MODES = {
    "id": "auto",
    "design": "non-executable",
    "prerequisite": "auto",
    "calculated": "auto",
    "recorded_value": "executable",
    "signature": "executable",
    "witness": "executable",
    "choice_list": "executable",
    "cross_reference": "executable",
}

VALID_COLUMN_TYPES = set(COLUMN_MODES.keys())


def col_is_executable(col_type: str) -> bool:
    """True if the column is filled by users during execution."""
    return COLUMN_MODES.get(col_type) == "executable"


def col_is_auto(col_type: str) -> bool:
    """True if the column is system-evaluated (not user-fillable)."""
    return COLUMN_MODES.get(col_type) == "auto"


def _validate_element_id(name: str, label: str = "ID") -> None:
    """Validate that an element ID uses only lowercase letters and digits."""
    if not re.fullmatch(r"[a-z0-9]+", name):
        raise ValueError(
            f"{label} '{name}' is invalid. Use only lowercase letters and digits (a-z, 0-9)."
        )


def new_document(document_id: str, title: str) -> dict:
    """Create a blank document in authoring phase."""
    return {
        "system_properties": {
            "document_id": document_id,
            "title": title,
            "phase": "authoring",
            "created": _now(),
        },
        "user_properties": {},
        "execution_properties": {},
        "sections": {},
    }


def new_document_from_template(document_id: str, title: str, template: dict) -> dict:
    """Create a document from a template, overriding id and title.
    Elements with enforced=True in the template get locked=True in the new document."""
    doc = copy.deepcopy(template)
    doc["system_properties"]["document_id"] = document_id
    doc["system_properties"]["title"] = title
    doc["system_properties"]["phase"] = "authoring"
    doc["system_properties"]["created"] = _now()
    # Apply enforced→locked: enforced elements become locked in the new document
    for section in doc["sections"].values():
        if section.get("enforced"):
            section["locked"] = True
        for element in section["elements"]:
            if element.get("enforced"):
                element["locked"] = True
            if element["type"] == "table":
                for row in element.get("rows", []):
                    if row.get("enforced"):
                        row["locked"] = True
    return doc


# --- Section operations ---

def add_section(doc: dict, section_id: str, title: str,
                position: int | None = None) -> None:
    """Add a new section to the document. Position is 0-based insertion index."""
    _require_authoring(doc)
    _validate_element_id(section_id, "Section ID")
    if section_id in doc["sections"]:
        raise ValueError(f"Section '{section_id}' already exists.")
    new_section = {
        "title": title,
        "locked": False,
        "enforced": False,
        "elements": [],
    }
    if position is None:
        doc["sections"][section_id] = new_section
    else:
        _insert_section(doc, section_id, new_section, position)


def move_section(doc: dict, section_id: str, position: int) -> None:
    """Move a section to a new position (0-based)."""
    _require_authoring(doc)
    section = _get_section(doc, section_id)
    keys = list(doc["sections"].keys())
    if position < 0 or position >= len(keys):
        raise ValueError(f"Position {position} out of range (0-{len(keys) - 1}).")
    # Remove and reinsert at position
    del doc["sections"][section_id]
    _insert_section(doc, section_id, section, position)


def resolve_section_index(doc: dict, ref: str) -> tuple[int, str]:
    """Resolve a section reference to (index, section_id).
    Accepts: section_id, or SEC-N:id format."""
    keys = list(doc["sections"].keys())
    # Try SEC-N:id format
    ref_upper = ref.upper()
    if ref_upper.startswith("SEC-"):
        rest = ref[4:]  # preserve original case after SEC-
        if ":" in rest:
            num_str, sid = rest.split(":", 1)
            if sid in doc["sections"]:
                return keys.index(sid), sid
        else:
            try:
                num = int(rest)
                idx = num - 1  # SEC numbers are 1-based
                if 0 <= idx < len(keys):
                    return idx, keys[idx]
            except ValueError:
                pass
    # Try as plain section_id
    if ref in doc["sections"]:
        return keys.index(ref), ref
    raise ValueError(f"No section '{ref}' found.")


def _insert_section(doc: dict, section_id: str, section: dict, position: int) -> None:
    """Insert a section at a specific position by rebuilding the ordered dict."""
    keys = list(doc["sections"].keys())
    if position < 0 or position > len(keys):
        raise ValueError(f"Position {position} out of range (0-{len(keys)}).")
    items = list(doc["sections"].items())
    items.insert(position, (section_id, section))
    doc["sections"] = dict(items)


def delete_section(doc: dict, section_id: str) -> None:
    """Delete a section. Locked sections cannot be deleted."""
    _require_authoring(doc)
    section = _get_section(doc, section_id)
    if section.get("locked"):
        raise ValueError(f"Section '{section_id}' is locked and cannot be deleted.")
    del doc["sections"][section_id]


# --- Element operations ---

def add_text(doc: dict, section_id: str, text: str, name: str,
             position: int | None = None) -> int:
    """Add a text block to a section. Name is required. Returns the element index."""
    _require_authoring(doc)
    if not name:
        raise ValueError("Text block name is required.")
    _validate_element_id(name, "Text block name")
    section = _get_section(doc, section_id)
    _require_section_unlocked(section, section_id)
    element = {"type": "text", "locked": False, "enforced": False, "name": name, "value": text}
    return _insert_element(section, element, position)


def add_table(doc: dict, section_id: str, name: str, columns: list[dict],
              extendable: bool = True, sequential: bool = True,
              position: int | None = None) -> int:
    """Add a table to a section. columns is a list of {name, type} dicts.
    sequential=True (default) means executable cells must be filled left-to-right.
    Returns the element index."""
    _require_authoring(doc)
    _validate_element_id(name, "Table name")
    section = _get_section(doc, section_id)
    _require_section_unlocked(section, section_id)
    col_defs = {}
    col_order = []
    for col in columns:
        col_defs[col["name"]] = {"type": col["type"]}
        col_order.append(col["name"])
    element = {
        "type": "table",
        "locked": False,
        "enforced": False,
        "name": name,
        "columns": col_defs,
        "column_order": col_order,
        "extendable": extendable,
        "sequential": sequential,
        "rows": [],
    }
    return _insert_element(section, element, position)


# --- Column operations ---

def add_column(doc: dict, section_id: str, element_index: int,
               col_name: str, col_type: str, position: int | None = None) -> None:
    """Add a column to a table. Position is 0-based index in column_order."""
    _require_authoring(doc)
    table = _get_table(doc, section_id, element_index)
    if table.get("locked"):
        raise ValueError("Table is locked and cannot be modified.")
    if col_name in table["columns"]:
        raise ValueError(f"Column '{col_name}' already exists.")
    table["columns"][col_name] = {"type": col_type}
    if position is None:
        table["column_order"].append(col_name)
    else:
        if position < 0 or position > len(table["column_order"]):
            raise ValueError(f"Position {position} out of range.")
        table["column_order"].insert(position, col_name)


def rename_column(doc: dict, section_id: str, element_index: int,
                  old_name: str, new_name: str) -> None:
    """Rename a column in a table. Updates column_order and all row values."""
    _require_authoring(doc)
    table = _get_table(doc, section_id, element_index)
    if table.get("locked"):
        raise ValueError("Table is locked and cannot be modified.")
    if old_name not in table["columns"]:
        raise ValueError(f"Column '{old_name}' does not exist.")
    if new_name in table["columns"]:
        raise ValueError(f"Column '{new_name}' already exists.")
    # Update column definition
    table["columns"][new_name] = table["columns"].pop(old_name)
    # Update column order
    idx = table["column_order"].index(old_name)
    table["column_order"][idx] = new_name
    # Update row values
    for row in table["rows"]:
        if old_name in row["values"]:
            row["values"][new_name] = row["values"].pop(old_name)


def move_column(doc: dict, section_id: str, element_index: int,
                col_name: str, position: int) -> None:
    """Move a column to a new position (0-based) in the column order."""
    _require_authoring(doc)
    table = _get_table(doc, section_id, element_index)
    if table.get("locked"):
        raise ValueError("Table is locked and cannot be modified.")
    if col_name not in table["columns"]:
        raise ValueError(f"Column '{col_name}' does not exist.")
    if position < 0 or position >= len(table["column_order"]):
        raise ValueError(f"Position {position} out of range.")
    table["column_order"].remove(col_name)
    table["column_order"].insert(position, col_name)


def add_row(doc: dict, section_id: str, element_index: int,
            values: dict | None = None) -> int:
    """Add a row to a table. Returns the row index."""
    table = _get_table(doc, section_id, element_index)
    phase = doc["system_properties"]["phase"]
    if phase == "execution" and not table.get("extendable", False):
        raise ValueError("Table is not extendable; cannot add rows during execution.")
    if phase == "authoring" and table.get("locked"):
        raise ValueError("Table is locked; cannot add rows during authoring.")
    row = {
        "values": values or {},
        "locked": False,
        "enforced": False,
    }
    table["rows"].append(row)
    return len(table["rows"]) - 1


def edit_text(doc: dict, section_id: str, element_index: int, text: str) -> None:
    """Edit the content of a text block."""
    _require_authoring(doc)
    section = _get_section(doc, section_id)
    _require_section_unlocked(section, section_id)
    if element_index < 0 or element_index >= len(section["elements"]):
        raise ValueError(f"Element index {element_index} out of range.")
    el = section["elements"][element_index]
    if el["type"] != "text":
        raise ValueError(f"Element {element_index} is not a text block.")
    if el.get("locked"):
        raise ValueError("Text block is locked and cannot be edited.")
    el["value"] = text


def delete_element(doc: dict, section_id: str, element_index: int) -> None:
    """Delete an element from a section."""
    _require_authoring(doc)
    section = _get_section(doc, section_id)
    _require_section_unlocked(section, section_id)
    if element_index < 0 or element_index >= len(section["elements"]):
        raise ValueError(f"Element index {element_index} out of range.")
    el = section["elements"][element_index]
    if el.get("locked"):
        raise ValueError("Element is locked and cannot be deleted.")
    section["elements"].pop(element_index)


def delete_row(doc: dict, section_id: str, element_index: int, row_index: int) -> None:
    """Delete a row from a table."""
    _require_authoring(doc)
    table = _get_table(doc, section_id, element_index)
    if table.get("locked"):
        raise ValueError("Table is locked; cannot delete rows.")
    if row_index < 0 or row_index >= len(table["rows"]):
        raise ValueError(f"Row index {row_index} out of range.")
    row = table["rows"][row_index]
    if row.get("locked"):
        raise ValueError("Row is locked and cannot be deleted.")
    table["rows"].pop(row_index)


# --- Execution operations ---

def transition_to_execution(doc: dict) -> None:
    """Freeze document structure and enter execution phase."""
    _require_authoring(doc)
    doc["system_properties"]["phase"] = "execution"
    doc["system_properties"]["execution_started"] = _now()


def execute_cell(doc: dict, section_id: str, element_index: int,
                 row_index: int, column_name: str, value: str,
                 performer: str) -> None:
    """Populate an executable cell during execution."""
    _require_execution(doc)
    table = _get_table(doc, section_id, element_index)
    row = _get_row(table, row_index)

    # Check column exists and is executable
    if column_name not in table["columns"]:
        raise ValueError(f"Column '{column_name}' does not exist.")
    col_type = table["columns"][column_name]["type"]
    if not col_is_executable(col_type):
        raise ValueError(f"Column '{column_name}' is not executable (type: {col_type}, mode: {COLUMN_MODES[col_type]}).")

    # Check prerequisites
    blocked, reason = evaluate_prerequisites(doc, section_id, element_index, row_index)
    if blocked:
        raise ValueError(f"Row is blocked: {reason}")

    # Sequential check (table-level setting)
    if table.get("sequential"):
        exec_cols = [c for c in table["column_order"]
                     if col_is_executable(table["columns"][c]["type"])]
        col_idx = exec_cols.index(column_name) if column_name in exec_cols else -1
        for i, prev_col in enumerate(exec_cols):
            if i >= col_idx:
                break
            if prev_col not in row["values"] or not _has_execution_value(row["values"].get(prev_col)):
                raise ValueError(
                    f"Sequential table: must fill '{prev_col}' before '{column_name}'.")

    # Record with audit trail
    ts = _now()
    if column_name not in row["values"]:
        row["values"][column_name] = {"entries": []}
    audit = row["values"][column_name]
    if isinstance(audit, dict) and "entries" in audit:
        audit["entries"].append({
            "value": value,
            "performer": performer,
            "timestamp": ts,
        })
    else:
        # First execution — convert from authoring value or blank
        row["values"][column_name] = {
            "entries": [{"value": value, "performer": performer, "timestamp": ts}]
        }


def amend_cell(doc: dict, section_id: str, element_index: int,
               row_index: int, column_name: str, value: str,
               performer: str, reason: str) -> None:
    """Amend a previously executed cell. Appends to audit trail."""
    _require_execution(doc)
    table = _get_table(doc, section_id, element_index)
    row = _get_row(table, row_index)

    # Check amendability — default is amendable
    # TODO: per-element amendability flag check

    if column_name not in row["values"]:
        raise ValueError(f"Column '{column_name}' has not been executed yet.")
    audit = row["values"][column_name]
    if not isinstance(audit, dict) or "entries" not in audit:
        raise ValueError(f"Column '{column_name}' has no execution history.")
    if not audit["entries"]:
        raise ValueError(f"Column '{column_name}' has not been executed yet.")

    ts = _now()
    audit["entries"].append({
        "value": value,
        "performer": performer,
        "timestamp": ts,
        "reason": reason,
    })

    # Sequential cascade: revert all subsequent executable cells
    if table.get("sequential"):
        exec_cols = [c for c in table["column_order"]
                     if col_is_executable(table["columns"][c]["type"])]
        if column_name in exec_cols:
            amended_idx = exec_cols.index(column_name)
            for subsequent_col in exec_cols[amended_idx + 1:]:
                sub_val = row["values"].get(subsequent_col)
                if _has_execution_value(sub_val):
                    sub_val["entries"].append({
                        "value": None,
                        "performer": "system",
                        "timestamp": ts,
                        "reason": f"Auto-reverted: amendment to prior cell '{column_name}'",
                    })


# --- Prerequisite evaluation ---

def evaluate_prerequisites(doc: dict, section_id: str,
                           element_index: int, row_index: int) -> tuple[bool, str]:
    """Check if a row's prerequisites are satisfied.
    Returns (is_blocked, reason). If not blocked, reason is empty."""
    table = _get_table(doc, section_id, element_index)
    row = _get_row(table, row_index)

    # Find prerequisite column(s)
    prereq_values = []
    for col_name in table["column_order"]:
        if table["columns"][col_name]["type"] == "prerequisite":
            val = row["values"].get(col_name, "")
            if isinstance(val, str) and val.strip():
                prereq_values.append(val.strip())

    if not prereq_values:
        return False, ""

    # Parse and evaluate each prerequisite
    for prereq_text in prereq_values:
        # Support multiple prerequisites separated by semicolons
        for clause in prereq_text.split(";"):
            clause = clause.strip()
            if not clause:
                continue
            blocked, reason = _evaluate_single_prerequisite(table, clause)
            if blocked:
                return True, reason

    return False, ""


def _evaluate_single_prerequisite(table: dict, clause: str) -> tuple[bool, str]:
    """Evaluate a single prerequisite clause like 'EI-1 complete'.
    Resolves row references within the same table."""
    # Pattern: "<row_id> complete" — row must be fully executed
    match = re.match(r"^(.+?)\s+complete$", clause, re.IGNORECASE)
    if not match:
        # Unrecognized prerequisite format — treat as informational, not blocking
        return False, ""

    target_id = match.group(1).strip()

    # Resolve the target row by auto-generated ID
    prefix = table.get("id_prefix", "R")
    if not target_id.startswith(prefix):
        return False, ""  # Can't resolve — not blocking

    try:
        target_num = int(target_id[len(prefix):])
    except ValueError:
        return False, ""

    target_row_index = target_num - 1  # IDs are 1-based
    if target_row_index < 0 or target_row_index >= len(table["rows"]):
        return True, f"Prerequisite '{target_id}' references a non-existent row."

    target_row = table["rows"][target_row_index]

    # Check if the target row is fully executed (all executable cells filled)
    if not is_row_complete(table, target_row):
        return True, f"Prerequisite not met: '{target_id}' is not complete."

    return False, ""


def is_row_complete(table: dict, row: dict) -> bool:
    """Check if all executable cells in a row have been filled."""
    for col_name in table["column_order"]:
        col_type = table["columns"][col_name]["type"]
        if not col_is_executable(col_type):
            continue  # Only executable columns count
        val = row["values"].get(col_name)
        if not _has_execution_value(val):
            return False
    return True


def get_cell_status(table: dict, row: dict, row_index: int,
                    col_name: str, doc: dict = None,
                    section_id: str = None,
                    element_index: int = None) -> str:
    """Determine the display status of a cell.
    Returns: 'complete', 'ready', or 'blocked'."""
    col_type = table["columns"][col_name]["type"]

    # Non-executable and auto columns are always "complete" (display their value)
    if not col_is_executable(col_type):
        return "complete"

    # Check if already executed
    val = row["values"].get(col_name)
    if _has_execution_value(val):
        return "complete"

    # Check prerequisite blocking (row-level)
    if doc and section_id and element_index is not None:
        blocked, _ = evaluate_prerequisites(doc, section_id, element_index, row_index)
        if blocked:
            return "blocked"

    # Check sequential blocking (cell-level)
    if table.get("sequential"):
        exec_cols = [c for c in table["column_order"]
                     if col_is_executable(table["columns"][c]["type"])]
        col_idx = exec_cols.index(col_name) if col_name in exec_cols else -1
        for i, prev_col in enumerate(exec_cols):
            if i >= col_idx:
                break
            prev_val = row["values"].get(prev_col)
            if not _has_execution_value(prev_val):
                return "blocked"  # A prior cell in the sequence isn't done

    return "ready"


# --- Persistence ---

def save(doc: dict, path: str) -> None:
    """Save document to JSON file."""
    with open(path, "w") as f:
        json.dump(doc, f, indent=2)


def load(path: str) -> dict:
    """Load document from JSON file."""
    with open(path) as f:
        return json.load(f)


# --- Element helpers ---

# Type prefix mapping
_TYPE_PREFIXES = {"text": "TXT", "table": "TBL"}
_PREFIX_TO_TYPE = {v: k for k, v in _TYPE_PREFIXES.items()}


def element_type_id(section: dict, element_index: int) -> str:
    """Compute the type-specific ID for an element (e.g., TXT-0, TBL-1)."""
    target = section["elements"][element_index]
    prefix = _TYPE_PREFIXES[target["type"]]
    type_count = 0
    for i, el in enumerate(section["elements"]):
        if i == element_index:
            return f"{prefix}-{type_count}"
        if el["type"] == target["type"]:
            type_count += 1
    return f"{prefix}-{type_count}"


def _insert_element(section: dict, element: dict, position: int | None) -> int:
    """Insert an element at a position, or append if position is None."""
    if position is None:
        section["elements"].append(element)
        return len(section["elements"]) - 1
    if position < 0 or position > len(section["elements"]):
        raise ValueError(f"Position {position} out of range (0-{len(section['elements'])}).")
    section["elements"].insert(position, element)
    return position


def resolve_element_index(doc: dict, section_id: str, ref: str) -> int:
    """Resolve an element reference to a flat index.
    Accepts: type-specific ID (TXT-0, TBL-1), name, or flat index."""
    section = _get_section(doc, section_id)

    # Try type-specific ID (e.g., TXT-0, TBL-1)
    ref_upper = ref.upper()
    for prefix, el_type in _PREFIX_TO_TYPE.items():
        if ref_upper.startswith(prefix + "-"):
            try:
                type_idx = int(ref_upper[len(prefix) + 1:])
            except ValueError:
                break
            count = 0
            for i, el in enumerate(section["elements"]):
                if el["type"] == el_type:
                    if count == type_idx:
                        return i
                    count += 1
            raise ValueError(f"No element '{ref}' in section '{section_id}'.")

    # Try as name
    for i, el in enumerate(section["elements"]):
        if el.get("name", "").lower() == ref.lower():
            return i

    # Try as flat integer index
    try:
        idx = int(ref)
        if 0 <= idx < len(section["elements"]):
            return idx
        raise ValueError(f"Element index {idx} out of range.")
    except ValueError:
        pass

    raise ValueError(f"No element '{ref}' in section '{section_id}'.")


# --- Internal helpers ---

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_authoring(doc: dict) -> None:
    if doc["system_properties"]["phase"] != "authoring":
        raise ValueError("This operation is only allowed during authoring.")


def _require_execution(doc: dict) -> None:
    if doc["system_properties"]["phase"] != "execution":
        raise ValueError("This operation is only allowed during execution.")


def _get_section(doc: dict, section_id: str) -> dict:
    if section_id not in doc["sections"]:
        raise ValueError(f"Section '{section_id}' does not exist.")
    return doc["sections"][section_id]


def _require_section_unlocked(section: dict, section_id: str) -> None:
    if section.get("locked"):
        raise ValueError(f"Section '{section_id}' is locked.")


def _get_table(doc: dict, section_id: str, element_index: int) -> dict:
    section = _get_section(doc, section_id)
    if element_index < 0 or element_index >= len(section["elements"]):
        raise ValueError(f"Element index {element_index} out of range.")
    el = section["elements"][element_index]
    if el["type"] != "table":
        raise ValueError(f"Element {element_index} is not a table.")
    return el


def _get_row(table: dict, row_index: int) -> dict:
    if row_index < 0 or row_index >= len(table["rows"]):
        raise ValueError(f"Row index {row_index} out of range.")
    return table["rows"][row_index]


def _has_execution_value(val) -> bool:
    """Check if a cell has a current execution value.
    A cell with a revert entry (value=None) as its last entry is not considered executed."""
    if isinstance(val, dict) and "entries" in val:
        if not val["entries"]:
            return False
        return val["entries"][-1].get("value") is not None
    return False
