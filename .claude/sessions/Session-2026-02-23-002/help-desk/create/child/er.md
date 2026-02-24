# Create an Exception Report

```
qms create ER --title "Your title" --parent TP-NNN
```

Use when a test step fails during TP execution. Parent must be a TP in IN_EXECUTION.

Requires: failed step reference, root cause analysis, resolution, and re-execution plan.

If this is a non-test failure, use a [VAR](var.md) instead.

[< Back](README.md)
