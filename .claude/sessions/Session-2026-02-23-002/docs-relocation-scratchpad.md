# Scratchpad: Split QMS-Docs into docs/ and manual/

## The Insight

There are two distinct document packages conflated into one directory:

1. **docs/** — Standard software documentation for qms-cli. "Here's how to use this tool."
2. **manual/** — The QMS Manual. Policy, governance philosophy, operational guidance, deviation management, evidence standards. "Here's how to run a quality management system."

These serve different audiences, change for different reasons, and should live in different directories.

Currently both are mixed together in `qms-cli/seed/docs/` (38 files), and `qms init` copies the entire pile into `{project}/QMS-Docs/`.

## Scope (this CR)

- Create `qms-cli/docs/` and `qms-cli/manual/` inside the qms-cli submodule
- Sort the 38 files from `seed/docs/` into the two directories
- Remove `seed/docs/` once emptied
- Update `qms init` to stop seeding QMS-Docs to project root
- **Leave `pipe-dream/QMS-Docs/` untouched** (migrate later)

## File Sort

### manual/ (35 files) — The QMS Manual

The operational methodology. Everything about *how to run a QMS*.

```
manual/
├── README.md                          (manual index/landing page)
├── START_HERE.md                      (decision tree — "what should I do?")
├── QMS-Policy.md                      (core policy and judgment criteria)
├── QMS-Glossary.md                    (term definitions)
├── FAQ.md                             (common questions)
├── 01-Overview.md                     (what the QMS is, recursive governance loop)
├── 02-Document-Control.md             (types, naming, versioning, statuses)
├── 03-Workflows.md                    (review, approval, rejection state machine)
├── 04-Change-Control.md               (CR content, review teams, execution)
├── 05-Deviation-Management.md         (investigations, CAPAs, closure)
├── 06-Execution.md                    (EI tables, evidence, scope integrity)
├── 07-Child-Documents.md              (ER, VAR, ADD, VR lifecycle)
├── 08-Interactive-Authoring.md        (template-driven authoring system)
├── 09-Code-Governance.md              (branches, merge gate, genesis sandbox)
├── 10-SDLC.md                         (RS, RTM, qualification)
├── 11-Agent-Orchestration.md          (agent roles, communication boundaries)
├── guides/
│   ├── document-lifecycle-quickref.md
│   ├── evidence-writing-guide.md
│   ├── failure-decision-guide.md
│   ├── post-review-checklist.md
│   ├── quality-unit-handbook.md
│   ├── review-guide.md
│   ├── routing-quickref.md
│   ├── scope-change-guide.md
│   └── vr-authoring-guide.md
└── types/
    ├── ADD.md, CR.md, ER.md, INV.md
    ├── RS.md, RTM.md, SOP.md, TC.md
    ├── TEMPLATE.md, TP.md, VAR.md, VR.md
```

### docs/ (starts with 1 file, grows over time) — CLI Software Docs

Standard software documentation. "Here's how to use the tool."

```
docs/
├── cli-reference.md                   (was 12-CLI-Reference.md)
```

The CLI Reference is the only existing file that clearly belongs here. Future additions: installation guide, configuration reference, MCP server setup, contributing guidelines. These don't exist yet — no need to manufacture them.

**Note:** The numbering prefix (`12-`) made sense when it was part of the manual's 01-12 sequence. As a standalone docs/ file, `cli-reference.md` is cleaner.

## Changes to qms init

### Remove

- `seed_docs()` function
- `QMS-Docs` blocker in `check_clean_runway()`
- `seed_docs(root)` call in `cmd_init()`

### Update

- Docstring: remove "QMS-Docs/ educational documentation"
- Success message: remove "Review QMS-Docs/" line, add "Read the QMS Manual at qms-cli/manual/ for how to operate the QMS"

### Seed CLAUDE.md

The starter `seed/claude.md` currently says:
```
1. `QMS-Docs/QMS-Policy.md`
2. `QMS-Docs/START_HERE.md`
3. `QMS-Docs/QMS-Glossary.md`
```

Update to:
```
1. `qms-cli/manual/QMS-Policy.md`
2. `qms-cli/manual/START_HERE.md`
3. `qms-cli/manual/QMS-Glossary.md`
```

This assumes the project includes qms-cli as a submodule at `qms-cli/`. That's the default setup; projects with different layouts will customize their CLAUDE.md.

## Tests

| Test | Change |
|------|--------|
| `test_init_seeds_docs` | Remove (init no longer seeds docs) |
| `test_init_blocked_by_existing_qms_docs` | Remove (no QMS-Docs blocker) |
| `test_init_with_root_flag` | Remove QMS-Docs assertion |
| New: `test_manual_exists` | Verify `qms-cli/manual/` has expected core files (smoke test) |
| New: `test_docs_exists` | Verify `qms-cli/docs/` has expected core files |

## SDLC Impact

- **REQ-INIT-006** ("init shall seed QMS-Docs/") — revise or retire
- **RTM entry** for REQ-INIT-006 — update accordingly

## Internal Cross-References

All cross-references within the manual files use relative paths (`[Workflows](03-Workflows.md)`, `[CR reference](types/CR.md)`). These remain valid regardless of parent directory name.

The one exception: `12-CLI-Reference.md` cross-references manual sections like `[Document Control](02-Document-Control.md)`. Once it moves to `docs/cli-reference.md`, these relative paths break. Options:
1. Update to `../manual/02-Document-Control.md`
2. Replace with self-contained content (the CLI ref shouldn't depend on the manual)
3. Keep the links as cross-package references

## Deferred (not this CR)

- Migrate pipe-dream's `QMS-Docs/` references to `qms-cli/manual/`
- Delete pipe-dream's `QMS-Docs/` directory
- Update pipe-dream agent definitions
- Update pipe-dream CLAUDE.md
