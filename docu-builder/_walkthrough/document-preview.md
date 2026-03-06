# WALK-001: Walkthrough Document
Phase: AUTHORING

## Table of Contents

| SEC-NUM:ID | Title |
| --- | --- |
| `SEC-1:purpose` | Purpose |
| `SEC-2:steps` | Execution Steps |

## [-] `SEC-1:purpose` - Purpose

> `[TXT-0:introduction]` (LOCKED)

First block

> `[TXT-1:details]`

Updated details block

> `[TBL-0:Steps]` (EXTENDABLE)

| Step (ID) | Description (Design) | Result (Recorded Value) | |
|---|---|---|---|
| S-1 | Do the thing |  |  |

## [+] `SEC-2:steps` - Execution Steps

## [+] `SEC-3:third` - Title of Third Section

## [+] `SEC-4:third` - Title of Fourth Section

## Authoring Commands

| Command | Description |
|---------|-------------|
| `nav <section_id>` | Navigate to section |
| `view_all` | Show all sections at once |
| `add_section <id> <title>` | Add a new section |
| `add_text <section_id> <text> [name=X]` | Add text block |
| `edit_text <section_id> <elem_id> <new_text>` | Edit a text block |
| `add_table <section_id> <name> col:type ...` | Add a table (see README for column types) |
| `add_row <section_id> <tbl_id> [col=val ...]` | Append a row to a table |
| `delete_section <section_id>` | Delete an unlocked section |
| `delete_element <section_id> <elem_id>` | Delete an unlocked element |
| `delete_row <section_id> <tbl_id> <row_idx>` | Delete an unlocked row |
| `lock <section_id> [elem_id] [row_idx]` | Lock section, element, or row |
| `seal <section_id> [elem_id] [row_idx]` | Permanently lock (survives templates) |
| `save_template <file_path>` | Save as reusable template |
| `finalize` | Freeze structure, enter execution phase |

---
Write your command below, then save this file.

>> 