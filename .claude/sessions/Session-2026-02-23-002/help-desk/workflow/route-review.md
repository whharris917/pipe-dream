# Route for Review

```
qms route DOC-ID --review
```

Submits the document for reviewer evaluation.

- From DRAFT: enters IN_REVIEW (pre-execution review)
- From IN_EXECUTION: enters POST_REVIEW (post-execution review)

The CLI infers which phase automatically.

**Blocked?** Document must be checked in (not checked out).

**Next:** Wait for [reviewers to evaluate](../review/README.md), then [route for approval](route-approval.md).

[< Back](README.md)
