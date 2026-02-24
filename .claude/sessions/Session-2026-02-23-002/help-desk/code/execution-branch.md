# Create an Execution Branch

Every CR that modifies code uses an isolated branch:

1. Branch from `main` in the target system's repo
2. Name it after the CR (e.g., `cr-045-feature-name`)
3. Implement and commit iteratively
4. Record the starting commit hash in EI-1

Development happens in `.test-env/`, not in production submodule paths.

**When done:** [Merge to main](merge.md)

[< Back](README.md)
