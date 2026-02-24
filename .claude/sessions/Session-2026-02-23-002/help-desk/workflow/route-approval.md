# Route for Approval

```
qms route DOC-ID --approval
```

Submits the document for approver sign-off. **Blocked if any reviewer submitted `request-updates`.**

- From REVIEWED: enters IN_APPROVAL
- From POST_REVIEWED: enters POST_APPROVAL

**If blocked:** Address reviewer feedback > [check in](../edit/checkin.md) > [re-route for review](route-review.md).

[< Back](README.md)
