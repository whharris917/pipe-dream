# The Merge Gate

Code can only merge to `main` when **all three** are satisfied:

1. All tests pass (CI-verified)
2. RS is EFFECTIVE
3. RTM is EFFECTIVE with all requirements verified

No override mechanism. Squash merges are prohibited (they destroy referenced commit hashes).

See `QMS-Docs/09-Code-Governance.md`.

[< Back](README.md)
