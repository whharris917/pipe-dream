# Three-Tier Metadata

| Tier | What | Who writes | Location |
|------|------|-----------|----------|
| **Frontmatter** | Title, revision summary | Author | In the `.md` file |
| **Sidecar** | Status, version, owner, reviewers | CLI only | `.meta/{TYPE}/` |
| **Audit trail** | Every lifecycle event | CLI only | `.audit/{TYPE}/` (append-only) |

Separation ensures editing cannot corrupt workflow state, and audit history is immutable.

See `QMS-Docs/02-Document-Control.md`.

[< Back](README.md)
