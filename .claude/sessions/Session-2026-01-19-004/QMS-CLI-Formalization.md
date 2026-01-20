# QMS CLI: A Formal Model

## 1. Types (The Vocabulary)

```
User        = {lead, claude, qa, tu_ui, tu_scene, tu_sketch, tu_sim, bu}
Group       = {Initiators, QA, Reviewers}
DocType     = {SOP, CR, INV, TP, ER, VAR, RS, RTM, TEMPLATE, ...}
Status      = {DRAFT, IN_REVIEW, REVIEWED, ..., CLOSED, RETIRED}
Action      = {create, checkout, checkin, route, assign, review, approve, reject, release, revert, close, cancel}
Outcome     = {RECOMMEND, REQUEST_UPDATES}
Phase       = {pre_release, post_release}
```

## 2. State (What the System Tracks)

The entire system state `S` is a tuple:

```
S = (M, A, T, W)

Where:
  M : DocID → Metadata        # .meta/ files
  A : DocID → [AuditEvent]    # .audit/ files (append-only list)
  T : User → [Task]           # inbox/ task files
  W : User → {DocID}          # workspace contents
```

**Metadata** for a document:
```
Metadata = {
  doc_id            : DocID
  doc_type          : DocType
  version           : Version       # "N.X" format
  status            : Status
  executable        : Bool
  responsible_user  : User | null
  checked_out       : Bool
  pending_assignees : [User]
  execution_phase   : Phase | null  # only for executable
  reviews           : User → Outcome # accumulated reviews
}
```

## 3. Authorization Filter

Every command passes through an authorization function:

```
authorized(user, action, doc) : Bool =

  inGroup(user, action)                         # Group membership check
  ∧ (¬owner_only(action) ∨ isOwner(user, doc))       # Owner check
  ∧ (¬assigned_only(action) ∨ isAssigned(user, doc)) # Assignment check
```

Where:
```
inGroup(user, action) = ∃g ∈ PERMISSIONS[action].groups : user ∈ USER_GROUPS[g]
isOwner(user, doc)    = M[doc].responsible_user = user
isAssigned(user, doc) = user ∈ M[doc].pending_assignees
```

## 4. State Machine (Valid Transitions)

```
δ : Status × Trigger → Status | ⊥

Triggers:
  route_review    : DRAFT → IN_REVIEW (or IN_PRE_REVIEW, IN_POST_REVIEW)
  all_reviewed    : IN_REVIEW → REVIEWED
  route_approval  : REVIEWED → IN_APPROVAL
  approve         : IN_APPROVAL → APPROVED (when all approve)
  reject          : IN_APPROVAL → REVIEWED
  effective       : APPROVED → EFFECTIVE
  release         : PRE_APPROVED → IN_EXECUTION
  revert          : POST_REVIEWED → IN_EXECUTION
  close           : POST_APPROVED → CLOSED
```

The transition function is **total within valid edges** and **undefined (⊥) otherwise**.

## 5. Commands as Guarded Transformations

Each command is a **guarded state transformation**:

```
command : Action × User × DocID × Params → Result<S', Error>

command(action, user, doc, params) =
  if ¬validUser(user)               → Error("Unknown user")
  if ¬authorized(user, action, doc) → Error("Not authorized")
  if ¬precondition(action, doc)     → Error("Invalid state")
  else → (transform(S, action, doc, params), log(action, user, doc))
```

**Command Table:**

| Command | Precondition | Transformation | Side Effects |
|---------|--------------|----------------|--------------|
| `create` | type valid | M[new_id] := initial_meta | A[id] += CREATE, W[user] += id |
| `checkout` | ¬checked_out | checked_out := true, responsible_user := user | copy to workspace |
| `checkin` | checked_out ∧ owner | update content | A += CHECKIN, may revert status |
| `route --review` | status ∈ {DRAFT, ...} | status := IN_*_REVIEW, assignees := [qa] | T[qa] += task |
| `assign` | status = IN_*_REVIEW | assignees += users | T[users] += tasks |
| `review` | assigned ∧ IN_*_REVIEW | reviews[user] := outcome | A += REVIEW, T[user] -= task |
| `approve` | assigned ∧ IN_*_APPROVAL | if all_approved: bump version | A += APPROVE |
| `reject` | assigned ∧ IN_*_APPROVAL | status := *_REVIEWED | A += REJECT |
| `release` | PRE_APPROVED ∧ owner | status := IN_EXECUTION | A += RELEASE |
| `close` | POST_APPROVED ∧ owner | status := CLOSED | A += CLOSE |

## 6. Invariants (Always True)

```
INV-1: ∀doc: M[doc].checked_out ⟹ M[doc].responsible_user ≠ null
INV-2: ∀doc: M[doc].status = EFFECTIVE ⟹ M[doc].responsible_user = null
INV-3: ∀doc: A[doc] is append-only (entries never modified or deleted)
INV-4: ∀doc: M[doc].version matches "N.X" where N,X ∈ ℕ
INV-5: ∀doc: status transitions follow δ (no invalid edges)
INV-6: ∀user,doc: user ∈ T[user] for doc ⟺ user ∈ M[doc].pending_assignees
```

## 7. The Review Gate

```
canRouteApproval(doc) =
  M[doc].status ∈ {REVIEWED, PRE_REVIEWED, POST_REVIEWED}
  ∧ ∀u ∈ M[doc].pending_assignees: M[doc].reviews[u] = RECOMMEND
```

All reviewers must recommend before approval routing is permitted.

## 8. Version Arithmetic

```
bump_minor(v) = "N.(X+1)" where v = "N.X"
bump_major(v) = "(N+1).0" where v = "N.X"

On approval: version := bump_major(version)
On checkin (post-approval rework): version := bump_minor(version)
```

---

## Summary: The CLI in One Sentence

> **The QMS CLI is a guarded state machine where every command is an authorization check followed by a status transition with mandatory audit logging.**

Or more precisely:

```
∀ command invocation:
  Result = authorize(user, action, doc)
         ⨾ validate_precondition(status, action)
         ⨾ transform_state(S, action, params)
         ⨾ append_audit(action, user, doc)
```

---

## Visual: The Two Lifecycles

**Non-Executable (SOP, RS, RTM):**
```
DRAFT ──route──▶ IN_REVIEW ──all_reviewed──▶ REVIEWED ──route──▶ IN_APPROVAL ──all_approve──▶ APPROVED ──▶ EFFECTIVE
                     ▲                            │                    │
                     └────────────────────────────┴────────reject──────┘
```

**Executable (CR, INV, TP, ER, VAR):**
```
DRAFT ──▶ IN_PRE_REVIEW ──▶ PRE_REVIEWED ──▶ IN_PRE_APPROVAL ──▶ PRE_APPROVED
                                                                      │
                                                                   release
                                                                      ▼
CLOSED ◀── POST_APPROVED ◀── IN_POST_APPROVAL ◀── POST_REVIEWED ◀── IN_EXECUTION
                                    │                   │  ▲            ▲
                                    └───────reject──────┘  └───revert───┘
```

---

## Key Insight

The CLI is just **three things repeated**:
1. **Check authorization** (group + owner + assignment)
2. **Validate transition** (is this edge in the graph?)
3. **Apply transformation + log** (mutate state, append audit)
