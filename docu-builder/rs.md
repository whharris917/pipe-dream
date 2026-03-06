# DocuBuilder — Informal Requirements Specification

*This is not a QMS-controlled document. It lives in the genesis sandbox and serves as a working reference for prototyping.*

*Source: authoring-and-executing-controlled-documents.md (Session 2026-03-03-001)*

---

## 0. AI Usability

### REQ-AI-001: Context Minimization

DocuBuilder shall be designed first and foremost for use by AI agents, prioritizing minimal context presentation to agents at all times.

---

## 1. Authoring

### REQ-AUTH-001: Insert Text Blocks

The author shall be able to insert text blocks into documents.

### REQ-AUTH-002: Insert Tables

The author shall be able to insert tables into documents.

### REQ-AUTH-003: Insert Sections

The author shall be able to insert new sections into documents.

### REQ-AUTH-004: Template-Based Creation

Documents shall be creatable from an existing template.

### REQ-AUTH-005: Define Column Types

During document authoring, the author shall be able to set and change the type of each column in a table.

### REQ-AUTH-006: Edit Text Blocks

The author shall be able to edit the content of unlocked text blocks.

### REQ-AUTH-007: Positional Insertion

Elements (sections, text blocks, tables) shall support positional insertion relative to existing elements via `before` and `after` references.

### REQ-AUTH-008: Section Reordering

The author shall be able to move sections to new positions within the document.

### REQ-AUTH-009: Column Management

The author shall be able to add, rename, and reorder columns in existing tables during authoring.

### REQ-AUTH-010: Auto-Navigate on Section Creation

Newly created sections shall be automatically selected for viewing.

### REQ-AUTH-011: Required Element IDs

All elements (sections, text blocks, tables) shall have a required alphanumeric identifier. Element IDs shall use only lowercase letters and digits (a-z, 0-9).

---

## 2. Enforcing and Locking

### REQ-LOCK-001: Enforced Elements

During authoring, the author shall be able to mark sections, elements, and individual table rows as enforced. The `enforced` property has no effect during authoring of that document — enforced elements remain fully editable.

### REQ-LOCK-002: Template Enforcement

When a document is instantiated from a template, all elements with `enforced=True` in the template shall have `locked=True` set by the system in the new document.

### REQ-LOCK-003: Locked Elements Cannot Be Deleted

Locked elements shall not be deletable.

### REQ-LOCK-004: Locked Elements Cannot Be Edited

Locked text blocks shall not be editable. Locked tables shall not accept column additions, renames, or reorders. A locked section protects all elements within it.

### REQ-LOCK-005: Locked Is System-Controlled

The `locked` property shall not be directly modifiable by users. It is set exclusively by the system during template instantiation based on the `enforced` property.

---

## 3. Table Columns

### REQ-COL-001: Column Modes

Each table column shall belong to exactly one of three modes:
- **Executable** — filled by users during execution.
- **Auto** — system-evaluated; not directly fillable by users.
- **Non-Executable** — set during authoring, frozen during execution.

### REQ-COL-002: Non-Executable Column Types

Non-executable columns shall support the following type: Design.

### REQ-COL-003: Executable Column Types

Executable columns shall support the following types: Recorded Value, Signature, Witness, Choice List, and Cross Reference.

### REQ-COL-004: Auto Column Types

Auto columns shall support the following types: ID, Prerequisite, and Calculated.

### REQ-COL-005: Auto-Populated ID

ID columns shall be auto-populated with unique identifiers using a configurable prefix (default: "R") in the format `{prefix}{row_number}`, where row numbers are 1-based.

### REQ-COL-006: Executable Columns Blocked During Authoring

Executable column cells shall not be populated during document authoring. They shall be rendered with a visual indicator (`[EXECUTABLE]`) to distinguish them from empty non-executable cells.

### REQ-COL-007: Choice List Options Defined During Authoring

Choice List columns shall have their option list defined during document authoring.

### REQ-COL-008: Calculated Columns

A Calculated column type shall contain an expression evaluated against the document's properties. Calculated column values shall update automatically when their inputs change.

### REQ-COL-009: Cross Reference Columns

Cross Reference columns shall hold a reference to an external document (e.g., a VAR). They are executable and count toward row completion. When a row's execution result indicates failure, the executor shall fill the Cross Reference cell with the relevant document ID before the row can be considered complete for prerequisite purposes.

### REQ-COL-010: Empty Prerequisite Display

Prerequisite cells with no value shall be rendered as "N/A" to visually distinguish them from unfilled executable cells.

---

## 4. Execution State

### REQ-EXEC-001: Locked/Enforced Apply During Authoring

The `locked` property (system-controlled) shall govern editability during authoring. The `enforced` property (user-controlled) shall have no effect during authoring of the current document.

### REQ-EXEC-002: Blocked/Unblocked Apply During Execution

The terms blocked and unblocked shall apply during document execution and govern whether executable columns may be populated.

### REQ-EXEC-003: Prerequisite-Based Blocking

A section, table, or row shall be blocked — and no executable content within it may be populated — until its prerequisites have been met.

### REQ-EXEC-004: Prerequisite Definition

A prerequisite shall be an assertion against a document property or element state. A prerequisite is satisfied when its assertion evaluates to true. The format `{row_id} complete` shall assert that all executable cells in the referenced row have been filled.

### REQ-EXEC-005: Executable Audit Trail

All executable elements shall maintain an internal audit trail preserving all previous responses, including amendments and system-initiated reverts.

### REQ-EXEC-006: Execution Timestamps

A timestamp shall be recorded whenever any element is executed, amended, or reverted.

### REQ-EXEC-007: Table Extendability

During document drafting, the author shall be able to designate tables as extendable or non-extendable. Extendable tables may have rows added during execution.

### REQ-EXEC-008: Amendability

During document drafting, the author shall be able to designate elements as amendable or not amendable.

### REQ-EXEC-009: Sequential Tables

Tables shall be sequential by default. In a sequential table, executable elements in each row shall be populated in order from left to right. During document drafting, the author shall be able to disable sequential behavior on a per-table basis.

### REQ-EXEC-010: Sequential Amendment Cascade

When a cell in a sequential table is amended, all subsequent executable cells in that row shall be automatically reverted to an unexecuted state. The revert shall be recorded in each affected cell's audit trail with the reason for reversion. Reverted cells must be re-executed in sequential order.

### REQ-EXEC-011: Duplicatable Sections

During document drafting, the author shall be able to designate sections as duplicatable. Duplicatable sections may be duplicated during execution. Duplicated sections shall be labeled `{original_section_id}-DUPLICATE-1`, `{original_section_id}-DUPLICATE-2`, etc.

### REQ-EXEC-012: Document Phases

Documents shall have two phases: authoring and execution. Transitioning to execution shall freeze the document structure. During execution, only executable elements, extendable tables (per REQ-EXEC-007), and duplicatable sections (per REQ-EXEC-011) may be modified.

### REQ-EXEC-013: Text Blocks Read-Only During Execution

Text blocks shall be read-only during execution.

### REQ-EXEC-014: Prerequisite Temporal Separation

Prerequisite rows must be completed in a prior checkin cycle before their dependents can be executed. This ensures distinct timestamps for audit trail integrity.

---

## 5. Data Model

### REQ-DATA-001: JSON Schema

Documents shall be defined using a strict JSON schema that fully specifies all properties of the document, including its sections, elements, their locked/enforced status, all execution behavior, and all interactions with elements (including their audit trails) during execution.

### REQ-DATA-002: Validated Mutation Interface

All edits to documents during drafting, and all actions during execution, shall be mediated by a wrapper interface that ensures only valid mutations are made to the underlying JSON source file.

### REQ-DATA-003: JSON Opacity

Agents using the DocuBuilder system shall never be required to read, understand, make edits to, or reason about the underlying JSON structure.

### REQ-DATA-004: Text-Based Agent Interface

Agents using the DocuBuilder system shall be presented an intuitive, low-context, navigable text-based interface for authoring and executing documents. The rendition format shall be markdown.

### REQ-DATA-005: Interface Guidance

The text-based interface shall provide helpful guidance during authoring and execution.

### REQ-DATA-006: Visual Distinction of Field States

The text-based interface shall use formatting and notational conventions to clearly distinguish editable/executable fields from locked/blocked fields. Specifically:
- `[READY]` shall indicate a ready (empty, executable) cell during execution
- `[BLOCKED]` shall indicate a blocked cell during execution (prerequisite not met, or sequence not reached)
- `[EXECUTABLE]` shall indicate an executable cell during authoring
- `(LOCKED)`, `(ENFORCED)`, `(BLOCKED)` tags shall indicate element state

### REQ-DATA-007: Minimal README

DocuBuilder shall have a minimal, concise README that provides just enough context to get an agent started with using the system. All specific guidance shall be presented in context during use of the DocuBuilder system.

---

## 6. Interaction Model

### REQ-INT-001: Command Zone

All agent interactions during authoring and execution shall be made via DocuBuilder commands written in a designated zone at the bottom of the current rendition of the document being drafted or executed.

### REQ-INT-002: Checkin Triggers Command Execution

Checkin of the document shall trigger execution of the command written in the command zone.

### REQ-INT-003: Automatic Checkout Cycle

Application of changes to the JSON source file shall trigger an automatic checkout of the next rendition. This checkout-modify-checkin cycle forms the basis of all document authoring and execution.

### REQ-INT-004: Minimal Default Rendition

Document renditions shall be kept minimal by default. Navigation commands shall be available to access different sections within documents.

### REQ-INT-005: Type-Specific Element Identification

Elements shall be identified using type-specific IDs: `TXT-N` for text blocks, `TBL-N` for tables, where N is a 0-based index within that type. Sections shall be identified as `SEC-N:id` where N is a 1-based positional number. Commands shall accept type IDs, element names, or flat indices as references.

### REQ-INT-006: Table of Contents

The rendered document shall include a Table of Contents listing all sections. Section headers shall indicate expand/collapse state: `[-]` for visible sections, `[+]` for collapsed sections.

### REQ-INT-007: Command Reference

The rendered document shall include a context-appropriate command reference table showing available commands for the current phase (authoring or execution).

### REQ-INT-008: Input Validation

Commands that accept column references (e.g., `add_row`, `exec`) shall validate column names against the table definition and return an error listing available columns when an unknown column name is provided.

### REQ-INT-009: Finalization Guard

The `finalize` command shall reject documents that have no sections. Documents must have at least one section before transitioning to execution phase.

### REQ-INT-010: Consistent Error Format

All error messages returned by commands shall begin with `Error:` to enable reliable programmatic error detection.

### REQ-INT-011: Inspect Command

An `inspect` command shall populate a Context section in the rendered document with detailed properties and available actions for the inspected element. The Context section shall appear after the command reference. When no element is inspected, the Context section shall display a usage hint.

---

## 7. Properties

### REQ-PROP-001: Property Namespaces

Every document shall have three property namespaces: system properties (auto-populated, not editable by the author), user properties (defined and populated by the author during drafting), and execution properties (schema defined during authoring, values populated during execution).

### REQ-PROP-002: Cross-Document References

Document properties shall be able to reference properties from other documents. This mechanism shall support all cross-document relationships, including parent-child dependencies and shared state.

---

## 8. Context Economy

### REQ-CTX-001: Section Visibility

During document authoring, the author shall be able to define a visibility condition for a section. Sections whose visibility condition evaluates to false shall not be rendered in the agent's view.

---

## 9. Work Instructions

### REQ-WI-001: Disposable Guided Documents

The system shall support Work Instructions — disposable documents whose purpose is to produce an artifact (another document, a configuration, a decision) rather than to persist as a permanent record.

### REQ-WI-002: Same Primitives

Work Instructions shall use the same table, column, prerequisite, and section primitives as persistent documents. Only the lifecycle endpoint differs.
