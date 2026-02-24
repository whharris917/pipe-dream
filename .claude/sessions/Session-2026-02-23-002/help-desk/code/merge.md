# Merge to Main

Before merging, satisfy the [merge gate](../concepts/merge-gate.md):

1. All tests pass at the merge commit
2. RS is EFFECTIVE
3. RTM is EFFECTIVE

Then merge (no squash) and update the submodule pointer:

```
git add my-app && git commit -m "Update submodule"
```

See `QMS-Docs/09-Code-Governance.md`.

[< Back](README.md)
