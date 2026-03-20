# Session-2026-03-20-001

## Current State (last updated: renderer split + ELK removal complete)
- **Active document:** CR-110 (IN_EXECUTION v1.1)
- **Current task:** qms-workflow-engine repo cleanup and restructure
- **Blocking on:** Nothing
- **Next:** Per PROJECT_STATE forward plan

## Progress Log

### Session Start
- Read previous session notes (Session-2026-03-19-002)
- Read PROJECT_STATE.md, SELF.md, START_HERE.md
- Read all 4 architecture articles from previous session
- Initialized session

### Dependency Analysis
- Mapped all external references from wfe-ui/ to outside directories
- Found 2 real external refs: QUALITY_MANUAL_DIR (3 levels up to pipe-dream), WORKFLOWS_DIR (1 level up to v1 workflows/)
- Found vestigial sys.path hack in runtime/renderer.py

### sys.path Hack Removal
- Removed 5-line sys.path injection from `runtime/renderer.py` (lines 14-19)
- Imports resolve without it since utils.py and engine/ are local to wfe-ui

### v1 Engine Removal
- Deleted: `wfe/` (12 modules), `workflows/` (11 YAMLs), `templates/` (2 YAMLs), `compiled/` (4 MDs), `.wfe/` (runtime state), `db.json`, `pyproject.toml`, `qms_workflow_engine.egg-info/`, `.pytest_cache/`, `__pycache__/`
- Removed dead code in app.py: `WORKFLOWS_DIR`, `_list_workflows()`, v1 workflow list on /initiate route
- ~5,174 lines deleted

### Repo Restructure: wfe-ui/ → engine/ + app/
- `wfe-ui/runtime/` → `engine/runtime/` (workflow interpretation)
- `wfe-ui/engine/` → `engine/execution/` (table execution)
- `wfe-ui/builder_handler.py` → `engine/builder.py`
- `wfe-ui/utils.py` → `engine/utils.py`
- `wfe-ui/app.py` → `app/app.py`
- `wfe-ui/api.py` → `app/api.py`
- `wfe-ui/templates/` → `app/templates/`
- `wfe-ui/static/` → `app/static/`
- `wfe-ui/data/` → `data/`
- `wfe-ui/ENGINE.md` → `docs/ENGINE.md`
- `wfe-ui/TAXONOMY.md` → `docs/TAXONOMY.md`
- Merged wfe-ui/.gitignore into root .gitignore
- Created `engine/__init__.py`, `app/__init__.py`
- Created `run.py` at repo root as single entry point
- Removed `if __name__` block from app/app.py

### Import Rewiring (6 files)
- `app/app.py`: builder_handler → engine.builder, runtime → engine.runtime, api → app.api, fixed DATA_DIR path
- `app/api.py`: engine.* → engine.execution.*
- `engine/builder.py`: runtime.* → .runtime.*, fixed data paths
- `engine/runtime/renderer.py`: utils → ..utils, engine.* → ..execution.*

### Updated README.md
- Replaced v1 DAG engine description with unified runtime summary

### Verification
- All imports pass: engine.runtime, engine.execution, engine.builder, app.api, app.app
- Flask smoke test: GET /, /agent, /workshop all return 200
- User confirmed `python run.py` works

### Renderer Split: agent_observer.html → 7 JS files
- Extracted all renderer code from `agent_observer.html` (3,433 lines) into `app/static/renderers/`:
  - `registry.js` (265 lines) — renderer framework, mode toggle, state dispatch
  - `raw.js` (21 lines) — Raw JSON renderer
  - `simple-shared.js` (1,343 lines) — shared `wf*` rendering functions, flowchart helpers, banner
  - `simple.js` (334 lines) — CSS constants + 4 Simple variant registrations
  - `exp-a.js` (262 lines) — Experimental A (blueprint layout)
  - `exp-b.js` (222 lines) — Experimental B (card grid)
  - `exp-c.js` (325 lines) — Experimental C (tree outline)
- `agent_observer.html` reduced to 134-line thin shell: HTML, Jinja vars, script tags, SSE + boot
- Jinja variables injected via `window._WFE_ALLOWED_RENDERERS` and `window._WFE_STREAM_URL`

### ELK.js Dead Code Removal
- Identified ELK.js as completely superseded by schematic engine (renderHybrid) since Mar 18-19
- `_wfMiniFlowchart` defined but never called — only caller was the legacy banner path
- Removed from `registry.js`: `_elk`, `_elkBuildGraph`, `_elkLayout` (~90 lines)
- Removed from `simple-shared.js`: `_wfMiniFlowchart`, `_MB`, `_mbW`, `_mbRenderSvg`, `_mbRenderBannerSvg`, `_mbArrow` (~185 lines)
- Removed elkjs CDN `<script>` tag from `agent_observer.html` — no more external dependency
- Fixed stale "legacy ELK-based" comment on `expDRenderDefinition`
