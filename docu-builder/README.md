# DocuBuilder

A Python library for authoring and executing structured documents through a **checkout/edit/checkin** cycle. Documents have two phases: **authoring** (build the structure) and **execution** (fill in executable fields).

## How It Works

All interaction happens through a markdown file (`document.md`) in the workspace:

1. **Checkout** writes a rendered markdown file to the workspace
2. **Read** the file to see document state, available commands, and the `>> ` prompt
3. **Write** your command after the `>> ` prompt and save the file
4. **Checkin** parses the command, executes it, and auto-checks-out the next rendition

The agent never touches JSON directly. The markdown file IS the interface.

## Quick Start

```python
import sys
sys.path.insert(0, "/path/to/docu-builder")
from docubuilder import Engine

# Create a new document (auto-checks-out first rendition to document.md)
eng = Engine.new("DOC-001", "My Document", "/path/to/workspace")

# Read the rendered document
doc_path = "/path/to/workspace/document.md"
with open(doc_path) as f:
    print(f.read())  # Shows document state, commands, and >> prompt

# Write a command: find the >> prompt line and replace it
with open(doc_path) as f:
    lines = f.read().split("\n")
for i in range(len(lines) - 1, -1, -1):
    if lines[i].strip().startswith(">>"):
        lines[i] = ">> add_section purpose Purpose"
        break
with open(doc_path, "w") as f:
    f.write("\n".join(lines))

# Checkin: parses command, executes it, auto-checks-out next rendition
status = eng.checkin()
print(status)  # "Section 'purpose' added."

# Read the updated document.md and repeat the cycle
```

### Convenience Shortcut

For testing or scripting, `submit()` combines the write + checkin in one call:

```python
eng = Engine.new("DOC-001", "My Document", "/path/to/workspace")
eng.submit('add_section purpose Purpose')
eng.submit('add_text purpose intro "This is the purpose."')
```

## Creating and Loading Documents

```python
# New blank document (auto-checks-out first rendition)
eng = Engine.new(document_id, title, workspace_path)

# From a template (enforced elements become locked; starts in authoring phase)
eng = Engine.from_template(document_id, title, template_path, workspace_path)

# Load existing document from a workspace directory
eng = Engine.load(workspace_path)
eng.checkout()  # Write rendition to document.md
```

## Lifecycle

1. **Create** a document with `Engine.new()`, `Engine.from_template()`, or `Engine.load()`
2. **Author** by writing commands in `document.md` and calling `checkin()`
3. **Finalize** to freeze the structure and enter execution phase
4. **Execute** by filling in executable cells with `exec`

## Element Identification

Elements use type-specific IDs that are stable across insertions/deletions of other types:

- Sections: `SEC-1:purpose`, `SEC-2:steps` (1-based positional number + ID)
- Text blocks: `TXT-0`, `TXT-1` (0-based within type)
- Tables: `TBL-0`, `TBL-1` (0-based within type)

Element IDs (section IDs, text block names, table names) must be **lowercase alphanumeric only** (a-z, 0-9). No spaces, hyphens, or uppercase.

Commands accept these type IDs, element names, or flat indices. For example, `delete_element purpose TXT-1` and `delete_element purpose intro` both work.

## Authoring Commands

| Command | Description |
|---------|-------------|
| `nav <section_id>` | Navigate to a section |
| `view_all` | Show all sections at once |
| `add_section <id> <title> [before=X] [after=X]` | Create a section (auto-navigates to it) |
| `move_section <section_id> before=<ref>` | Move a section to a new position |
| `add_text <section_id> <name> <text> [before=X] [after=X]` | Add a text block |
| `edit_text <section_id> <elem_id> <new_text>` | Edit a text block |
| `add_table <section_id> <name> col:type ... [id_prefix=X] [sequential=false]` | Add a table (sequential by default) |
| `add_column <section_id> <tbl_id> name:type [before=X] [after=X]` | Add a column |
| `rename_column <section_id> <tbl_id> <old> <new>` | Rename a column |
| `move_column <section_id> <tbl_id> <col> before=<ref>` | Reorder a column |
| `add_row <section_id> <tbl_id> [col=val ...]` | Append a row to a table |
| `delete_section <section_id>` | Delete an unlocked section |
| `delete_element <section_id> <elem_id>` | Delete an unlocked element |
| `delete_row <section_id> <tbl_id> <row_idx>` | Delete an unlocked row |
| `enforce <section_id> [elem_id] [row_idx]` | Mark as enforced (becomes locked in templates) |
| `inspect <ref>` | Show element details in Context section (`TBL-0`, `TXT-0`, section ID) |
| `save_template <file_path>` | Save as reusable template |
| `finalize` | Freeze structure, enter execution phase |

## Execution Commands

| Command | Description |
|---------|-------------|
| `nav <section_id>` | Navigate to a section |
| `view_all` | Show all sections at once |
| `exec <section_id> <tbl_id> <row_idx> <col>=<val> ...` | Fill executable cells |
| `amend <section_id> <tbl_id> <row_idx> <col>=<val> reason=<text>` | Amend a cell |
| `add_row <section_id> <tbl_id> col=val ...` | Add row (extendable tables only) |
| `inspect <ref>` | Show element details in Context section (`TBL-0`, `TXT-0`, section ID) |

### Execution Example

```
>> exec steps TBL-0 0 Result="Test passed" Performer="alice"
>> amend steps TBL-0 0 Result="Test passed with warnings" reason="Added warning details"
```

## Column Types

Columns are specified as `name:type` when creating a table.

| Type | Mode | Behavior |
|------|------|----------|
| `id` | Auto | Auto-generated 1-based IDs (R1, R2...). Use `id_prefix=EI-` for EI-1, EI-2, etc. |
| `design` | Non-Executable | Set during authoring, frozen during execution. |
| `prerequisite` | Auto | Set during authoring. System-evaluated to block/unblock rows during execution. |
| `calculated` | Auto | Expression evaluated against document properties. Updates automatically. |
| `recorded_value` | Executable | Filled during execution with `exec`. Shows `<<  >>` when empty. |
| `signature` | Executable | Filled during execution with `exec`. Shows `<<  >>` when empty. |
| `witness` | Executable | Filled during execution with `exec`. Shows `<<  >>` when empty. |
| `choice_list` | Executable | Filled during execution with `exec`. Shows `<<  >>` when empty. |
| `cross_reference` | Executable | Filled during execution with a document ID (e.g., a VAR). Shows `<<  >>` when empty. |

## Quoting

Commands use shell-style parsing. Multi-word values need quotes:

```
>> add_table steps items Step:id "Description:design" "Result:recorded_value"
>> add_row steps TBL-0 Description="Commit the changes"
>> exec steps TBL-0 0 Result="All changes committed successfully"
```

## Enforcing and Locking

Elements have two properties: `locked` (system-controlled) and `enforced` (user-controlled).

- **Enforced**: Set by the author during authoring. Has no effect in the current document — everything remains fully editable. When the document is saved as a template and instantiated, enforced elements become **locked** in the new document.
- **Locked**: System-controlled. Cannot be set by users directly. Locked elements cannot be deleted, edited, or modified. A locked section also protects all its contents.

## Templates

Save an authored document as a template, then create new documents from it:

```python
eng = Engine.new("TMPL-001", "CR Template", "/tmp/template-ws")
eng.submit('add_section ei "Execution Items"')
eng.submit('add_table ei items Step:id Description:design Prereq:prerequisite Result:recorded_value Performer:signature id_prefix=EI-')
eng.submit('add_row ei TBL-0 Description="Pre-execution commit"')
eng.submit('add_row ei TBL-0 Description="Implement changes" Prereq="EI-1 complete"')
eng.submit('enforce ei TBL-0 0')  # Enforced -- locked in template instances
eng.submit('enforce ei TBL-0 1')  # Enforced -- locked in template instances
eng.submit('save_template /tmp/cr-template.json')

eng2 = Engine.from_template("CR-050", "Fix the Widget", "/tmp/cr-template.json", "/tmp/cr050-ws")
```

## Reading the Rendered View

The rendered document has these regions:

1. **Header** — document ID, title, phase
2. **Table of Contents** — all sections listed in a table
3. **Document Body** — section headers with `[-]` (expanded) or `[+]` (collapsed), followed by section content
4. **Command Reference** — available commands for the current phase
5. **Context** — shows element details when `inspect` is used; otherwise a usage hint
6. **Command Prompt** — `>> ` where you write your command

Element labels appear as gold bold text: `[TXT-0:intro]`, `[TBL-0:steps]`. Use the type ID (e.g., `TXT-0`, `TBL-0`) or element name in commands. Table headers show `ColumnName (Type)` — use the column name in `exec` and `amend` commands.

**Cell status (during authoring):**
- `[EXECUTABLE]` — executable cell placeholder; cannot be filled until execution phase

**Cell status (during execution):**
- `[READY]` — empty executable cell, can be executed now
- `[BLOCKED]` — cannot execute yet (prerequisite not met, or sequence not reached)
- `(BLOCKED)` — row-level tag indicating unmet prerequisites
- `(amended x1)` — cell was explicitly amended by a user; shows current value
- `Progress: 3/6 cells executed` — execution completion tracker

**Empty prerequisite cells** render as `N/A` to distinguish them from unfilled executable cells.

**Element tags:**
- `(LOCKED)` — system-controlled, cannot be modified/deleted
- `(ENFORCED)` — marked for template enforcement, editable in current document
- `(EXTENDABLE)` — table accepts new rows during execution
- `(SEQ)` — table requires executable cells to be filled left-to-right per row

**Prerequisites:** To use prerequisites, your table must have a column of type `prerequisite`. Set each row's prerequisite value during authoring (e.g., `add_row steps TBL-0 Prereq="EI-1 complete"`). During execution, rows with unmet prerequisites show as `(BLOCKED)` and cannot be executed. The format `{id} complete` means all executable cells in that row must be filled first. Each row must be completed in a separate checkin cycle before its dependents can execute.

**Sequential tables:** Tables are sequential by default (`(SEQ)` tag). Executable cells in each row must be filled left-to-right. Use `sequential=false` on `add_table` to disable. When a cell in a sequential table is amended, all subsequent executable cells in that row are automatically reverted (cascade). The revert is recorded in each affected cell's audit trail. Reverted cells show `[BLOCKED]` until their preceding cells are re-executed.

**Cascade-reblock:** If amending a cell in a sequential table causes a cascade revert that leaves the row incomplete, any rows whose prerequisites depend on that row will become `(BLOCKED)` again until the row is re-completed.

**Status column:** Tables have a trailing column that displays row-level tags like `(LOCKED)`, `(ENFORCED)`, `(BLOCKED)`, `(SEQ)`, and `[+ Add Row]`. This column has no header.

**Table extendability:** Tables are extendable by default (new rows can be added during execution). The `(EXTENDABLE)` tag in the rendered view indicates this.

## Error Handling

If a command fails, `checkin()` returns an error message (e.g., `"Error: Row is locked and cannot be deleted."`). The document state is unchanged. Fix the issue and try again.

The `>> ` prompt is always the last line in `document.md`. Commands are parsed with Python's `shlex.split()`.

## Persistence

Documents auto-save to the workspace on every successful checkin. The workspace contains:
- `document.md` — the current rendition (the agent's interface)
- `source.json` — the underlying document data (never edit directly)
- `session.json` — navigation state
