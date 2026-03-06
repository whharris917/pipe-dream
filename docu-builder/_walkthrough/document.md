# DOC-001: Test Protocol
Phase: EXECUTION

## Table of Contents

| SEC-NUM:ID | Title |
| --- | --- |
| `SEC-1:steps` | Execution Steps |

## [-] `SEC-1:steps` - Execution Steps

<span style="color: gold">**[TBL-0:items]**</span> (EXTENDABLE, SEQ)

| Step (ID) | Description (Design) | Prerequisites (Prereq) | Actual Results (Recorded Value) | Pass/Fail (Choice List) | Performer (Signature) | |
|---|---|---|---|---|---|---|
| S-1 | Verify installation | N/A | Installation verified | Pass | alice |  |
| S-2 | Run test suite | S-1 complete | `[READY]` | `[BLOCKED]` | `[BLOCKED]` |  |
| S-3 | Document results | S-2 complete | `[BLOCKED]` | `[BLOCKED]` | `[BLOCKED]` | (BLOCKED) |
|  |  |  |  |  |  | [+ Add Row] |

Progress: 3/9 cells executed

## Execution Commands

| Command | Description |
|---------|-------------|
| `nav <section_id>` | Navigate to section |
| `view_all` | Show all sections at once |
| `exec <section_id> <tbl_id> <row_idx> <col>=<val> ...` | Fill executable cells |
| `amend <section_id> <tbl_id> <row_idx> <col>=<val> reason=<text>` | Amend a cell |
| `add_row <section_id> <tbl_id> col=val ...` | Add row (extendable tables only) |
| `inspect <element_ref>` | Show element details and actions in Context section |

## Context

**Inspecting `TBL-0:items` in section `steps`**

Column Properties:

| # | Name | Type | Mode |
| --- | --- | --- | --- |
| 0 | Step | ID | Auto |
| 1 | Description | Design | Non-Executable |
| 2 | Prerequisites | Prereq | Auto |
| 3 | Actual Results | Recorded Value | Executable |
| 4 | Pass/Fail | Choice List | Executable |
| 5 | Performer | Signature | Executable |

Rows: 3
Sequential: Yes

Available actions:
- Execute a row: `exec steps TBL-0 <row_idx> <col>=<val> ...`
- Amend a cell: `amend steps TBL-0 <row_idx> <col>=<val> reason=<text>`
- Add a row: `add_row steps TBL-0 [col=val ...]`

---
Write your command below, then save this file.

>> 