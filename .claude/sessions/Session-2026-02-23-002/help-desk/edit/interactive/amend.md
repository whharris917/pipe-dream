# Amend a Previous Response

```
qms interact DOC-ID --goto prompt_id --reason "Why you're amending"
qms interact DOC-ID --respond "New response" --reason "Why you're amending"
```

Navigates to a previously answered prompt. The original response is preserved -- amendments append, never replace.

To cancel without amending: `qms interact DOC-ID --cancel-goto`

[< Back](README.md)
