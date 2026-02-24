# Withdraw from Review or Approval

```
qms withdraw DOC-ID
```

Pulls the document back to its previous editable state. Owner only.

| From | Returns to |
|------|-----------|
| IN_REVIEW | DRAFT |
| IN_APPROVAL | REVIEWED |
| POST_REVIEW | IN_EXECUTION |
| POST_APPROVAL | POST_REVIEWED |

[< Back](README.md)
