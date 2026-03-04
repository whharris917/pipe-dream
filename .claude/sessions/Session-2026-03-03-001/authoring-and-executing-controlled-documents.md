# Authoring and Executing Controlled Documents

## I. The Document Editor

A controlled document is authored in a purpose-built editor — not a text
editor, not a form wizard, not a prompt sequence. The editor understands
document types, structural constraints, and the property model. It is a
document IDE.

**Document creation is guided.** The author selects a document type (and
optionally a sub-type). The document ID is auto-populated. The author fills
in the title. The template for that type is loaded as the starting skeleton.

**The schema grows organically.** The author does not declare all fields
upfront. As the author writes the document, they reference properties that
already exist or define new ones. The schema emerges from the act of
authoring — it is discovered, not pre-declared.

**Structural integrity is enforced.** Certain elements are locked — they
cannot be removed or changed by the author. The document ID, the title
header, required sections, and required execution elements are protected.
Within these guardrails, the author has creative freedom.

## II. The Property Model

Every document has three property namespaces:

**System Properties** are auto-populated and not editable by the author.
Document ID, creation date, version, status, ownership — these are managed
by the system.

**User Properties** are defined and populated by the author during drafting.
They may be created manually or may appear automatically when the author
adds interactive elements that require them. User properties can grow
throughout the authoring process.

**Execution Properties** have their schema defined during authoring but
their values remain empty until the document is executed. The author designs
the execution interface; the executor fills it in.

## III. Composable Sections

Documents are assembled from composable sections. A section is a
self-contained unit that carries its own properties, its own interactive
elements, and its own execution behavior.

**Sections are importable.** If a type of change requires a specialized
section, the author imports it. All associated system and user properties
are added to the document's property library automatically.

**Sections are reusable.** A section is designed once and can be imported
into any document type. A "Security Review" section does not care whether it
lives in a Code Change CR or a Document Change CR. It plugs in and the
document absorbs its schema.

## IV. The Table Primitive

There is one interactive primitive: the table. Every interactive element in
an executable document is a table — from a single fillable field (a 1x1
table) to a complex multi-step verification procedure (M x N).

**Columns are fields. Rows are instances.** The top row contains headers,
defined during drafting and locked during execution.

**Each column has a type.** Column types fall into two categories:

**Non-executable types** are populated during drafting and locked during
execution:

- **ID** — auto-generated unique identifier per row
- **Row Number** — auto-incrementing integer
- **Design** — freeform content written during drafting, frozen at execution

**Executable types** are empty during drafting and populated during
execution:

- **Recorded Value** — freeform entry with per-cell audit trail
- **Signature** — the performer attests to the recorded value
- **Witness** — a second person (not the performer) attests to the truth of
  the recorded value
- **Issue** — cross-reference to a deviation record
- **Choice List** — selection from options defined during drafting

**The authoring experience defines the execution interface.** When the
author adds a table and sets column types, they are simultaneously designing
the visual layout, defining the execution schema, specifying audit
requirements, and establishing how the completed document will render.

## V. Dynamic Growth, Cross-References, and Prerequisites

**Tables can grow.** A simple "+ Add Row" feature is available during
drafting. It is optionally available during execution, configured per table
by the author. This replaces loop constructs with a natural, direct
mechanism.

**Properties can reference other documents.** A document may reference
properties from any other document in the system through a cross-reference
mechanism. A verification record can reference its parent change record's
properties. A change record can reference system properties from a governed
submodule's registry. One mechanism handles all cross-document
relationships.

**Sequential interaction is enforced through prerequisites.** During
drafting, the author defines per-row prerequisites — which rows, cells, or
sections must be completed before a given row is unlocked for execution.
Rows are released automatically once their prerequisites are satisfied.

Sequential execution is a chain of prerequisites. Branching is a
prerequisite on a choice list value. Parallelism is rows sharing the same
prerequisite. The execution topology emerges from prerequisite declarations.

**A prerequisite is a property assertion.** The simplest form is
`TARGET_PROPERTY = REQUIRED_VALUE` — a cell is unlocked when the referenced
property holds the required value. A prerequisite cell may contain a direct
assertion, a cross-reference to a boolean property elsewhere, or be blank
(no prerequisite — immediately available).

When gate logic is complex, the author builds a **prerequisite aggregator
table**: a standalone table whose purpose is to compute a boolean from
multiple inputs. Other rows reference that boolean as their prerequisite.
Complex gating is not a built-in engine feature — it is an emergent pattern
from the primitives.

**Tables sort by prerequisites.** Execution order is determined by the
prerequisite topology, not by visual position. Rows with no prerequisites
appear first, rows whose prerequisites are satisfied come next, and rows
still gated remain at the bottom. The author declares dependencies; the
ordering follows. During execution, the table is always a live progress
view: completed, actionable, and locked — in that order.

**Document dependencies are expressed as prerequisites.** When an Issue cell
references a deviation record (VAR), that cross-reference carries a
prerequisite assertion against the VAR's status property. A type 2 VAR must
reach pre-approval; a type 1 must reach post-approval. The parent
document's closure gate — itself just a prerequisite row — references those
status properties. No special cascade logic, no hardcoded closure rules.
The dependency is declared at the moment the issue is recorded, as a
first-class property reference.

## VI. Work Instructions

Not all interactive documents are saved. A **Work Instruction** is a
disposable guided document whose purpose is to produce an artifact — another
document, a configuration, a decision — rather than to persist as a record
itself.

**Guidance and execution are separate concerns.** Walking someone through a
decision or procedure (guidance) is different from filling in an approved
document's executable cells (execution). Work Instructions handle guidance;
executable tables handle execution. Earlier designs conflated these.

**A Work Instruction is a document whose output is another document.** A
Change Classification Form asks a series of questions (what kind of change,
does it affect code or documentation, is it a correction or an
enhancement). Based on the answers, it creates a document of the correct
type with the appropriate sections imported, properties pre-populated, and
execution tables pre-configured. Then the form evaporates. The resulting
document has no memory of how it was created — only what it contains.

**The decision tree uses the same primitives.** A Work Instruction is an
executable document whose Choice List columns with prerequisites form the
decision tree. Each choice gates which rows unlock next. Terminal rows
produce an action (create a document, import a section, set a property)
rather than recording a persistent value. The interactive mechanism is
the same; the lifecycle endpoint differs.

## VII. Context Economy

An AI agent pays a token cost for every visible character in its workspace.
Irrelevant context actively degrades performance. The workspace must show
only what is relevant right now.

**Calculated is a column type.** Alongside the non-executable types (ID,
Design, Row Number), a Calculated column contains an expression evaluated
against the property library. Its value updates whenever its inputs change.
Calculated cells can produce display text, derived values, or booleans that
control visibility.

**Section visibility is a calculated property.** A section is visible only
when its visibility condition — a Calculated boolean — evaluates to true.
When false, the section is not rendered to the workspace at all. The agent
never sees it, never pays the token cost, never gets distracted by it.

**Conditional content emerges from calculated cells.** Instructional text
that adapts to previous answers, prerequisite aggregators, derived
summaries — all are Calculated cells referencing other properties. The
workspace presents only the context the agent needs at this moment in the
interaction.

## VIII. The Agent Interface

**Checkout gives you a document. You edit it. Checkin processes your edits.**
That is the entire interface.

For execution, the agent sees tables with frozen cells and open
placeholders. It fills in the placeholders. Checks in. Next unlocked cells
appear. The table is self-explanatory — column types are visible,
placeholders indicate what to do, locked cells are visually distinct.

For authoring, the agent sees the document as editable text with tables
rendered in readable form. It writes prose, adds rows, edits design cells.
The structure is visible and self-documenting.

The agent already knows how to edit a document. The system renders structure
into self-explanatory form at checkout and parses edits back into structure
at checkin. No special commands, no operational vocabulary, no SOP study
required. The document IS the interface, and the interface is: edit what
you see.

## IX. The Data Model

The document's internal representation is a JSON structure with four
top-level concerns: three property namespaces and a sections container.

```
{
    system_properties: { ... },
    user_properties: { ... },
    execution_properties: { ... },
    sections: { "1": { ... }, "2": { ... } }
}
```

**Two element types.** A section contains an ordered list of elements.
Each element is either `text` (a prose block, optionally containing
Jinja2-style property references like `{{ user_properties.custom_1 }}`)
or `table` (the interactive primitive described in Section IV).

**Tables are named, not numbered.** Each table carries a `name` property
used for stable cross-references and prerequisite paths. Position-based
references would break when sections are reordered or imported. The name
is the table's identity.

**Column schema and rendering order are separate.** Columns are defined
as a dictionary keyed by display name, each entry specifying a `type`
(one of the column types from Section IV). A separate `column_order`
array controls rendering sequence. This decouples the semantic definition
from the visual layout.

**Row values are sparse.** A row's `values` dictionary is keyed by column
name and includes only populated columns. A row with
`{"Instructions": "Do this"}` has no ID value (auto-generated at render),
no Prerequisites value (meaning: no gate, immediately available). The
data model carries only what the author explicitly provided.

**Prerequisite paths use `::` as a separator.** A prerequisite reference
like `section_1::verification_table::row_3` provides a stable,
hierarchical addressing scheme. The same syntax works within a document
and across documents via cross-references.

**Locking is hierarchical.** A `locked` flag appears at three levels:

- **Section level:** A locked section protects everything within it —
  all elements, all rows.
- **Element level:** A locked element within an unlocked section means
  that specific text block or table cannot be removed, but adjacent
  content remains editable.
- **Row level:** A locked row within an unlocked table means the row's
  design content is frozen and the row cannot be deleted, but the table
  can still grow via new rows.

This hierarchy lets templates enforce structural requirements (required
sections, required execution tables, required header rows) while leaving
the author free to build within those guardrails.

**Sections are keyed, not indexed.** Sections use string keys in a
dictionary rather than array positions. This provides stable references
that survive reordering and section imports.

The prototype data model is captured in `document_dna.json`. The
workspace rendering mockup in `prompt.txt` demonstrates how this
structure presents to the agent at checkout — menu bar, section
navigation, tables with column types visible in headers, `[+ Add Row]`
affordances, and a command input region.

## X. Implementation Strategy

**Build the engine first.** The core functionality — documents, tables,
typed columns, properties, prerequisites, cross-references, sections,
calculated cells — is a pure Python library. No CLI, no file I/O, no
agent interface. A library you can explore in an interactive Python
terminal.

**Defer the interface.** How an agent interacts with DocuBuilder (checkout/
checkin, CLI commands, workspace rendering) is a separate concern. The
engine must be solid before the interface is designed. The engine's API
will reveal what the interface needs to expose.

**Start standalone.** DocuBuilder begins as an independent tool, outside
QMS control. Once the core is proven through interactive exploration, it
can be brought under change control and integrated into qms-cli.
