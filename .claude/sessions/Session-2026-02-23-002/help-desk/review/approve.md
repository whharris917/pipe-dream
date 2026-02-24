# Approve a Document

```
qms approve DOC-ID
```

Advances the document to its next approved state:

- Non-executable: IN_APPROVAL > **EFFECTIVE**
- Executable (pre): IN_APPROVAL > **PRE_APPROVED**
- Executable (post): POST_APPROVAL > **POST_APPROVED**

Version increments to N.0 on approval.

[< Back](README.md)
