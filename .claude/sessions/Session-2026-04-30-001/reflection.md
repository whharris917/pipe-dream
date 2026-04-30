# Reflection: The QMS today, vs. what Razem-driven UI will let us do

*Written 2026-04-30 immediately after CR-111 closed. Draws on the lived experience of running CR-111 through three pre-review cycles, two SDLC document review cycles, and a post-review cycle — roughly 25 subagent spawns and 30+ qms-cli invocations across two sessions, plus the auto-mode-vs-subagent-permissions incident at the end.*

---

## 1. What CR-111 actually cost, mechanically

Now that the dust has settled, here's a faithful accounting of where the time and context budget went on a single document-only CR. This isn't a complaint — the work was good, and the QMS earned its keep — but it's worth being honest about the shape of the labor.

**Authoring** — me writing markdown by hand: about 15% of the effort. The CR template, the RS, the RTM, the EI evidence batches, the §11 Execution Summary, three revisions of the CR + one revision of the RTM, plus session notes. Each document required reasoning about structure (what goes in §5 vs §11), checking template conventions, hand-formatting tables.

**Orchestration of subagents** — spawning, prompting, waiting, parsing reports: about 50% of the effort. Each review cycle:

1. Spawn QA → wait ~2 minutes → read QA's report → note the assigned reviewers
2. Spawn each TU/BU in parallel as background tasks → wait for notifications → read each report → reason about what each reviewer said
3. If any reviewer requested updates: checkout, edit, checkin, re-route, repeat

For CR-111 alone: three pre-review cycles × 5 reviewers = 15 review-spawns. Then SDLC-FLOW-RS: 6 reviewers × 1 cycle = 6 spawns + 1 approval. SDLC-FLOW-RTM: 4 reviewers × 2 cycles = 8 spawns + 1 approval. Post-review: 5 reviewers + 1 approval. **Roughly 39 subagent spawns** to land one document-only adoption CR.

**Manual qms-cli invocations** — checkout, checkin, route, status, comments: about 15% of the effort. Each operation is a separate Bash call with a separate permission check, separate output to parse, separate state update to track in my head.

**Manual git operations** — staging, committing, pushing, tagging: about 5% of the effort. Less than I expected, partly because submodule pointers didn't change.

**Document state tracking in my head** — what version is each doc at? Who's still pending? Is the workspace file fresh? Is the audit log up to date? — about 10% of the effort. Constantly low-grade.

**Recovering from infrastructure quirks** — the auto-mode-vs-subagent-permissions incident, the YAML line-wrapping edit failure on the RTM frontmatter, the qms-cli versioning being weird about v0.1 vs v1.0 transitions: about 5% of the effort, but disproportionately stressful when it hits.

That distribution matters because it tells you what kind of tool will help, and what kind won't.

---

## 2. What Razem actually absorbs

The 50% spent on subagent orchestration is the largest single bucket and the one most cleanly addressable by a UI. Concretely:

**A `/cr/{id}/review` page** would replace the spawn-wait-read-spawn pattern with a single dashboard. The page lists pending reviewers, displays each comment as it arrives (via SSE — already a Razem primitive), shows running status (3 of 5 in), and surfaces a "Reroute for review" button with the revised draft pre-filled when a TU returns request-updates. I would still read each comment and decide on revisions, but the *spawning* and *waiting* would be replaced by a notification stream. That alone probably halves the per-cycle cost.

**A `/cr/{id}/edit` page** (CR-builder) would replace hand-authoring markdown. The 12-section CR template becomes a series of TextForm + ListForm + TableForm + Tabs components. The EI table is a TableForm with `fixed_columns`. The "5 domain groups" enumeration is a ChoiceForm. The "no `{{...}}` placeholders" check becomes structural — you can't submit until required fields are filled. Most importantly: the *shape* of a valid CR becomes machine-checkable, not just by-eye-reviewable. Today, QA spends review time verifying that frontmatter is present and sections are in the right order — that's the kind of work a form should never need a human for.

**A `/inbox` page** wired to real QMS state would replace `qms inbox`-via-bash for both me and the reviewer agents. The inbox surfaces the pending-action affordances directly — "Review CR-111", "Approve SDLC-FLOW-RS" — clickable, with the document pre-loaded. Today, every reviewer subagent spawn includes the boilerplate "check your inbox, perform your review independently, submit via the QMS CLI" and the agent has to figure out what to do; in the UI world, the affordances *are* the prompt.

**A `/cr/{id}/execute` page** would replace the EI table evidence batching. Each EI becomes a card with Pass/Fail toggles, an evidence text field, and a "performer/date" auto-fill. The contemporaneity rule (evidence written as work happens) becomes a UX feature: when you mark Pass, the date stamps automatically; when you reference a commit, the system can verify it exists. The chicken-and-egg of EI-10 (post-execution commit hash) becomes a structured "commit on submit" affordance instead of a manual two-pass dance.

**A `/release-tag` workflow** for the qualified-baseline tag (EI-8 in this CR) could be a single button that dispatches to the appropriate submodule, applies the annotated tag with a templated message naming the RS/RTM versions, and pushes — eliminating one of the more error-prone manual steps.

**Most importantly: a *terminal-execution primitive*** — the missing piece in Razem today, queued as the load-bearing engine work — would let any of the above pages actually mint real qms-cli operations. Without that primitive, every Razem page is a mockup. With it, the UI becomes a real authoring + orchestration surface.

---

## 3. What Razem genuinely does not absorb

This is the more important section, and it's the one I underweighted in yesterday's reflection.

**Reviewer judgment.** Every blocking finding from the CR-111 cycles came from a reviewer reading actual code and noticing it didn't match my prose. tu_ui catching the input-layer ordering, tu_scene catching the brush-operations exception, tu_sketch catching `DeleteEntityCommand`-doesn't-exist, tu_sim escalating the static-vs-tethered atom distinction to blocking on v0.2 even though they'd been content with the same gap on v0.1 — these are *judgment* calls, not procedure calls. A UI doesn't generate those; agents do, by reading code carefully.

**Factual verification.** The RTM is a verification document. Its job is to tell a future reader "this requirement is met by this code, here is why." Producing that document well requires someone (an agent) to actually look at the code, follow the imports, read the flow, and write prose that survives scrutiny. UI doesn't help with that — it might display the cited file, but it can't read it on the reviewer's behalf.

**The "is this true?" question.** A CR is fundamentally a claim about the world. The QMS process surfaces ways the claim might be false (and forces correction). The UI can speed up routing, but it cannot improve the *truthfulness* of the document. Truthfulness is a property of how carefully it was written and reviewed.

**Scope discipline.** "Don't silently expand scope during execution" is a procedural rule, but enforcing it requires a reviewer who notices when the executed work doesn't match the approved plan. UI can help by showing a diff between approved-EIs and executed-EIs, but the *call* on whether a divergence is acceptable belongs to a human or agent doing the reading.

**Process improvement from failure.** The recursive governance loop — process failures becoming inputs to process improvement via INVs and CAPAs — is the QMS's most valuable property. A UI doesn't drive this loop; *people noticing things* drives this loop. Razem can make those people more efficient, but the noticing is irreducible.

So: Razem absorbs the friction of *how documents move and get written*. The QMS itself — the *what* and *why* of document control — is unchanged.

---

## 4. The deeper structural shift

Today, the QMS workflow has the shape:

**Agent-as-orchestrator.** I am the only entity that can hold the entire workflow state in mind at once. I spawn subagents, parse their outputs, decide next steps, hand-edit documents, run qms-cli, commit and push. The QMS lives in files and audit logs, but the *agency* that makes those files move lives in my conversation context.

This is fragile in three specific ways:

1. **Context-budget bound.** This session paused at 83% on one CR yesterday, recovered today at the cost of a fresh context, and is now at maybe 70% having closed CR-111. Every CR consumes a meaningful fraction of a context window because I must hold the orchestration state in working memory. A multi-CR sprint requires multiple sessions, each with handoff overhead.

2. **Single-actor bound.** No one else can drive the QMS at the same time. If you wanted to invite a collaborator, or have a different agent (Codex, Gemini) handle one CR while I handle another, the QMS would be a bottleneck — both because they'd need to read CLAUDE.md and learn the qms-cli, and because we'd race on document state.

3. **Cache-bound.** Each subagent spawn from cold consumes minutes. Resuming via SendMessage isn't currently exposed. Sequential review cycles compound.

The Razem-driven future is **system-as-orchestrator**.

In that world: the QMS state lives in a database (effectively the existing `.meta` JSON files plus the document store), and the UI is the orchestrator. You (or me, or any agent, or all of us simultaneously) interact with the same shared state through the same forms. A reviewer agent's "submit review" is a POST to a Razem endpoint, not a bash call. The document workspace isn't a per-user directory; it's a checked-out document with a known owner. The inbox isn't "scan my user folder for tasks"; it's a query against the database.

The shift isn't *making me faster* — it's *removing me from the critical path*. That's a categorically different kind of leverage than UI polish.

---

## 5. The QMS as a knowledge-extraction machine

Something I noticed across CR-111's cycles that I want to name explicitly: **the QMS doesn't just govern documents; it produces knowledge about the system being documented.**

This week alone, the review process surfaced:

- The actual input-layer dispatch order (`System → Modal → Global → HUD`, not what CLAUDE.md said)
- The fact that `interaction_data` lives on Sketch, not Session, and that this is a known asymmetry no one had named
- The brush-operations exception to the Air Gap (a documented design decision in CLAUDE.md §3.3 that nobody had connected to the Air Gap requirement before)
- That `DeleteEntityCommand` doesn't exist; the actual class is `RemoveEntityCommand`
- That `Solver.solve()` is a dispatcher, not a peer of `solve_numba()`
- That tools mutate `sketch.interaction_data` directly, rendering `ToolContext.set_interaction_data` an unused facade
- That `integrate_n_steps` extends to line 251, not 180
- That the Compiler produces both static and tethered atoms — and that the module's "Data flow is ONE-WAY" docstring is stale because tethered atoms enable two-way coupling
- That `Scene.update()` has 8 phases, not the 5 in CLAUDE.md §7

That's a lot of latent knowledge surfaced from a "lightweight" adoption CR. None of it would have surfaced without the review cycle forcing reviewers to read code and write prose anchored to file paths and line numbers. *The discipline of writing inspection-based qualitative-proof RTM rows is the discipline of producing accurate documentation* — because the reviewers will catch you if it's wrong.

In a Razem-driven future, this property must be preserved. The temptation will be to auto-generate evidence (e.g., "we verified line 184 of scene.py mentions `execute()`, evidence row generated"). That's worse than useless — it produces a document that says nothing reviewable. The qualitative-proof model only works because a reviewer has to *read*, *think*, and *commit* to a claim.

What Razem can rightly automate: routing, status, structural validation, contemporaneity stamps, version bumping, cross-reference checking. What it must not automate: the prose itself, or the verdict.

---

## 6. The auto-mode incident as a portent

One concrete data point worth dwelling on. The CR was procedurally complete at the post-approval stage. All five post-reviewers had recommended. QA had verified compliance. The only thing left was a single `qms approve CR-111` command issued by the QA subagent. And it failed — twice — because of a permission inheritance quirk between the parent session's auto-mode and the subagent's tool prompts.

This is the kind of failure mode you don't see on the happy path; it shows up at the worst possible moment, in the middle of a system that requires multi-agent orchestration to function. We unblocked it in seconds (you exited auto mode and a fresh QA agent worked), but the lesson generalizes:

**The current QMS is one infrastructure quirk away from a stall, every time.** Subagent permissions, MCP server reliability, container health, the qms-cli versioning behavior, the audit log integrity, hooks that may or may not fire — each is a place where a transient failure can stop a CR mid-flight. Today we have me as the ad-hoc human-in-the-loop debugging these. In a multi-actor world without me, there has to be a system that handles them.

A web-based UI moves the QMS from "a constellation of CLI tools held together by an orchestrator" to "an application with state, error handling, and a request-response cycle." That's not just convenience; it's the difference between a process that works only when everything goes right, and a process that handles real-world friction.

---

## 7. Where this leaves the engine work

If everything above is right, then the order of operations for the engine track post-Flow-State should probably be:

1. **Terminal-execution primitive first.** It's the load-bearing piece. Without it, every UI page is a stub. It's also the smallest scope change that converts the Razem accumulation into real leverage.

2. **Inbox / Workspace pages second.** These have the highest activity-per-CR ratio (every CR uses them every cycle). They're also the simplest to build because the data model is small.

3. **CR-builder + CR review pages third.** Largest UI surface, but the cr-create scaffold from Session-002 already proves the form-composition primitives work. Review is essentially the same UI in reverse.

4. **Then everything else.** RTM authoring, evidence batching, post-review checklists, etc. — these are wins but smaller wins.

A genuine question worth answering before resuming engine work: **does the existing engine surface (26 component types, 7 themes, the workshop experiments) actually map onto the workflow pages we need, or have we accumulated a vocabulary that won't match the verbs?** The cr-create scaffold suggested it does — the Razem primitives composed into a real CR-authoring UI without obvious gaps. But it's worth a checkpoint after the next 1-2 real workflow pages land.

The strongest signal that the engine has reached usefulness will be the moment when *I would rather use the UI than the CLI for some operation*. Right now there's no such operation. After the terminal primitive + inbox + cr-create's Submit working for real, there will be at least one. That's the inflection point.

---

## 8. What Flow State gets out of all this

The chemical-engineering game itself — the actual reason this project exists — is now under formal SDLC governance. Every gameplay change, every new constraint type, every UI tweak, every persistence improvement will be a CR with a real qualified baseline. The first such CR will be slower than just `git commit` would be, because the process cost is real. But it will produce a system that has a *traceable history of intent* — what was changed, why, what it broke, how it was verified.

The previous five CRs that should have happened on Flow State during the genesis era didn't. So the system has accumulated technical debt that is documentation debt: behaviors that work but aren't anchored, design decisions that exist in code but not in any controllable document. Going forward, that debt stops accumulating. New behaviors get RS additions. New verifications get RTM additions. The qualified baseline advances commit by commit.

In the long run, the value of this isn't speed; it's *legibility*. A future me, or a different agent, or a collaborator can read SDLC-FLOW-RS and know what Flow State is supposed to be. That's a property the system didn't have yesterday, and does today.

---

## 9. The token-cost shift: progressive disclosure as the deepest gain

(Added after a Lead correction to the reflection above — promoting this to its own section because the previous version under-weighted it.)

Today, the QMS is a **high-prior-context system**. Every agent that participates in any role — initiator, reviewer, approver — must arrive *already knowing the QMS*. That's a substantial cognitive precondition:

- CLAUDE.md (~10k tokens) defines the orchestrator's identity and the operational principles
- The Quality Manual (`QMS-Policy`, `START_HERE`, `QMS-Glossary`, plus chapters `01-Overview` through `12-CLI-Reference`) is tens of thousands of additional tokens
- SOP-001 through SOP-007 each several thousand tokens
- Per-document-type templates (TEMPLATE-CR, TEMPLATE-VAR, TEMPLATE-VR, etc.)
- Per-role agent definitions in `.claude/agents/` (the QA agent's `qa.md` alone is several hundred lines, and the TUs are similar)

That's the *minimum* an agent needs to internalize before they can be useful. And it's not just the volume — it's the *judgment overhead* of holding the decision tree in working memory:

- "Is this a CR or a VAR?" (depends on whether work is in flight or after closure)
- "Type 1 or Type 2 VAR?" (depends on parent's ability to close before resolution)
- "Should this need a VR?" (depends on whether the EI involves behavioral verification)
- "INV-vs-VAR — is this systemic enough to investigate?" (depends on the failure pattern)
- "Does this CR need bu in the review team?" (depends on whether the change is user-facing)
- "Is §7.4/§7.5 in scope?" (depends on whether code is modified)
- "Does this need a TP child?" (depends on whether testing is structured-enough)

Each of these decisions is encoded in policy. The agent's job today is to *learn* the policy and *apply* it. That's the QMS asking each participant to be a student of itself.

**Razem inverts this.** With a progressively-disclosing UI:

- The agent doesn't *decide* "this should be a CR"; they click **Initiate Change Record** in the Agent Portal. The form *is* the encoding.
- The agent doesn't *recall* that §7.4/§7.5 are conditional on code modifications; the form asks "Is this CR modifying code?" and the conditional sections appear or don't.
- The agent doesn't *internalize* that VR is needed when EIs involve behavioral verification; the EI-builder has a "Requires VR" checkbox with help text inline.
- The agent doesn't *check* whether the CR is in IN_PRE_REVIEW or IN_PRE_APPROVAL before the next routing — the action menu shows only the affordances valid for the current state.
- The agent doesn't *figure out* the SOP for a failure scenario; when an EI fails, the UI offers "Create VAR" with the parent linkage prefilled and the Type 1 vs Type 2 toggle inline with explanatory text.

The agent provides **content**, not **form**. They make the *judgment calls that survive automation* — "is this the right requirement?", "does this evidence support this claim?", "is this scope expansion or scope drift?" — and nothing else. Everything procedural is the system's job.

### What this changes about who can participate

Today, the QMS effectively requires that every participant be Claude or one of the role-specific subagents (qa, tu_*, bu) whose `.md` definitions front-load the relevant context. New types of participants — a Codex agent, a Gemini agent, a smaller cheaper model, a one-off ad-hoc agent for a specific review, an *actual human collaborator* — can't easily plug in, because the prerequisite reading is too expensive (in tokens, time, or attention).

A starter pack of "you're working on a coding project; when the user requests a change, click 'Initiate CR' in the Agent Portal" is small enough that almost any agent can absorb it. The *workflow* progressively discloses everything else, exactly when it's relevant. This drops the bar from "expert who has read the manual" to "anyone capable of filling out forms based on prompts they're shown."

That has cascading consequences:

- **Pluralism.** The QMS becomes hospitable to multiple agents (different vendors, different sizes, different specializations) cooperating on the same project. Not just for parallelism, but for *diversity of perspective* during reviews.
- **Token economics inversion.** Today every QMS participation burns thousands of tokens on policy-recall before any productive work. With Razem, those tokens are freed for actual reasoning about the change. A QA review that takes 60K tokens today (re-read CLAUDE.md → re-read qa.md → re-read QMS-Policy → re-read relevant SOPs → finally read the document) might take 10K (read the document, click approve or request-updates with a comment).
- **Lower per-action overhead.** A reviewer agent today reconstructs procedural state at every spawn (where am I in the workflow, what action does the system want from me, what are the affordances). With Razem, the system *tells them* — the inbox surface is "Review CR-111 §X with these specific evidence rows highlighted."

### What this *doesn't* change

The reviewer's value still comes from reading code carefully and noticing things. tu_scene's catch on the brush-operations exception this session was a connection between two pieces of context (CLAUDE.md §3.3 documents the time-travel snapshot pattern; REQ-FS-ARCH-001 claimed Air Gap was sole-gateway) that no naive form-driven flow would have surfaced. A pure form-disclosure model could *lower the floor* (more agents can participate) while *narrowing the ceiling* (deep contextual connections might not surface).

The right Razem design has to disclose **context** progressively too, not just **procedure**. When an agent reviews REQ-FS-ARCH-001's evidence row, the UI shouldn't only show the form fields — it should surface "linked design notes," "related CLAUDE.md sections," "git blame on the cited file," "prior reviews of this requirement." That's progressive disclosure of *the relevant background*, available on-demand without forcing the agent to load it up-front.

Same for code-reading. Razem can't *do* the code-reading, but it can *prepare* it — pre-fetch the cited file, anchor at the cited line range, show the surrounding function, link to the test file (when there is one). That converts "go grep and read" from an agent task to a sidebar.

### What this implies for CLAUDE.md and the Quality Manual

In the Razem-driven future, both shrink dramatically.

- CLAUDE.md becomes a *concepts document*: the recursive governance loop, the project's two intertwined objectives, the air gap principle, the "code is the design" SDLC posture. Things an agent should *understand* but never *recall procedurally*.
- The Quality Manual becomes the *spec for the UI*. The procedural content (when to create which document type, how the lifecycle progresses, what fields are required) becomes the form schema. The judgment-and-policy content (what counts as adequate evidence, how to choose between VAR types) becomes inline help text and decision aids surfaced at the relevant moments.
- The SOPs become the *behavior of the engine*. They don't go away; they move from "documents agents read" to "rules the system enforces."

The Quality Manual as it exists today is doing two jobs that should be separated: it's a *reference document for humans designing the system* (which it should remain), and it's a *runtime knowledge source agents must internalize before acting* (which Razem replaces). After Razem, the manual stays as the former; the latter dissolves.

### The deepest recasting

The final framing this corrects in the original reflection: I described the shift as **agent-as-orchestrator → system-as-orchestrator**, and that's right but not deep enough.

The deeper recasting is: **agents-as-students-of-the-system → agents-as-actors-in-the-system.** Today, every QMS participant is forced to be both a student and an actor in the same context window, which is why so much token budget goes to policy-recall rather than substantive work. Razem makes the system its own runtime: it knows the rules, applies them, surfaces only what an actor needs to act, and reserves agent attention exclusively for the irreducibly judgmental.

That's the gain. It's not "Claude is faster." It's "the QMS no longer requires a Claude-shaped student to function."

---

## TL;DR

The "old fashioned way" of running the QMS is roughly 50% subagent orchestration overhead, 30% authoring/state-tracking, 15% qms-cli invocations, and 5% real review value extraction. Razem-driven UI absorbs most of the first three categories cleanly. It cannot absorb reviewer judgment, factual verification, or the truthfulness of the documents themselves — those are properties of the QMS process, not the UI. The structural shift is bigger than "UI polish": it removes the orchestrator from the critical path, making the QMS multi-actor and multi-session instead of single-actor and stateful-in-conversation. The deepest gain is the *progressive disclosure inversion*: today every participant must be a student of the QMS before they can act in it; in the Razem-driven future, they're shown only what they need at each step, and only the irreducibly judgmental remains. That collapses the participant prerequisites from "expert who has read the manual" to "anyone capable of filling out forms on prompts the system surfaces" — opening the QMS to multiple agent types, cheaper models, and human collaborators without each having to absorb tens of thousands of tokens of procedural context first. The auto-mode incident is a small example of the class of friction the current system is brittle to. The terminal-execution primitive is the load-bearing missing piece.

Flow State is now legibly governed. That's the real win — not the process velocity.
