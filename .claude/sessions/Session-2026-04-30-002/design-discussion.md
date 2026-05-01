# Razem, MCP, and the QMS: Architectural Framing and Long-Term Vision

*Written 2026-05-01 in Session-2026-04-30-002 after a long discussion between the Lead and claude. This document captures the framings that emerged from that discussion as a reference for future sessions. It is a synthesis, not a controlled QMS artifact — the Lead has not signed off on every word, and the framings should be expected to evolve.*

---

## 1. Purpose

Capture the architectural vocabulary, framings, and long-term vision that emerged in this session's discussion. The animating goal of the framings is **generative**: a good framing should make whole classes of downstream design questions answer themselves, while clearly relocating the residual questions to a place where they can be answered with their own (more local) framings.

---

## 2. Core framings

These are the rules. Each is short, operationally testable, and forecloses many design choices.

### 2.1 Razem builds UIs for MCP servers

Razem is **general-purpose** and **domain-agnostic**. It does not know what a QMS is. It is best understood not as an "API wrapper" but as an **interface generator for MCP servers**. Given an MCP server (any MCP server), Razem renders its tool/resource/prompt surface as a UI that both an agent and a human can drive — through the same component tree, projected as JSON for agents and as HTML for humans.

The QMS is **one** MCP server among many possible ones. The QMS website is a Razem deployment configured to point at the QMS MCP server. Razem itself contains zero QMS-specific code.

### 2.2 MCP is the boundary

The MCP server defines the boundary of what is "part of" the system. Anything reachable through MCP is in scope; anything not reachable through MCP is implementation detail. Storage formats, internal data structures, and back-end choices live behind the MCP boundary and are invisible to consumers.

This is true whether the consumer is an agent calling tools or a human clicking affordances in the rendered UI.

### 2.3 The parity rule (no human-only features)

**Humans can only do what agents can do, full stop.** The MCP surface is the union of capabilities; the rendered UI exposes that union and nothing more. There is no admin override, no expert mode, no human-only escape hatch.

Three consequences:

- The UI is a **faithful witness** to the agent's surface. If the form is awkward, the awkwardness is exactly what the agent encounters. If the validation error is confusing, the agent gets the same confusion. The UI becomes a debugger for the MCP server — every piece of human friction is a signal about agent friction.
- The UI is a **demand-shaping mechanism on the MCP**. If a human reaches for an affordance that doesn't exist, the right move is to add it to the MCP (which extends the agent's capability too), never to bolt it onto the UI as a human-only feature. UI growth and agent-capability growth are the same arrow.
- It is also a **tactile empathy interface**. A chat client gives the human fluent natural-language access to the agent's tools, but the *agent* is doing the calling — the human describes intent, not surface. With Razem-on-MCP, the human is rendering the literal tool surface and clicking affordances, sharing the agent's vantage point.

### 2.4 Documentation lives in the interface

The MCP server's tool descriptions, JSON Schema field labels, examples, validation messages, and state-conditional help text *are* the documentation. They are rendered inline by Razem alongside the affordances they describe. There is no separate "manual" to be consulted; the page is self-describing for both audiences.

A practical leverage point: **MCP tool description quality directly determines both the agent and human experience.** The same description serves both audiences, so investing in good descriptions doubles the return.

### 2.5 The Quality Manual splits

Under these framings, the Quality Manual stops being a single artifact and splits into two distinct things:

- **Procedural content** (what fields, in what order, with what validation, when each state transition is valid) → moves into Razem **page seeds** as form labels, help text, validation messages, Visibility conditions, derivations.
- **Policy content** (why these procedures exist, what governance values they encode, how the system should evolve) → stays as a **design document for the humans building the QMS-MCP itself**. This becomes a meta-artifact, not a runtime reference for agents.

The split corresponds exactly to the MCP-vs-Razem boundary.

---

## 3. Architectural consequences

These follow from the core framings.

### 3.1 MCP is catalog-shaped, not HATEOAS-shaped

MCP is not designed with HATEOAS principles in mind. It exposes a flat catalog of tools, resources, and prompts. Tool responses are structured data with no next-action hints, no state-precondition info, no application-state-machine controls.

This is deliberate: MCP assumes a smart-LLM client that can reason over tool descriptions and infer next actions. The hypermedia-controls-in-responses pattern that classical HATEOAS uses to drive a dumb client isn't necessary when the client can think.

### 3.2 Razem adds the application-state-machine layer that MCP omits

Razem's component model — affordances bound to URLs, state-conditional visibility, sibling-bound derivations, progressive disclosure — is exactly the application-state-machine layer that classical HATEOAS provides and MCP does not.

So Razem's role isn't translating one format to another. It's **introducing structure that MCP itself doesn't carry.**

### 3.3 The off-MCP procedural interior is where most labor lives

Every controlled workflow has the same skeleton:

- **MCP boundary call** (e.g., `qms_create`) — discrete state transition
- **Off-MCP procedural interior** (drafting the document, populating sections, judging what to write) — the bulk of the actual work
- **Next MCP boundary call** (e.g., `qms_checkin`)

If MCP is the nodes, off-MCP is the edges. The edges hold most of the labor. Razem's job is to make those edges first-class.

### 3.4 Page seeds are the procedural + HATEOAS layer

Combining 3.1–3.3: a Razem **page seed** encodes the application-state-machine and the procedural interior for a workflow. The seed declares:

- What fields appear, organized in what containers (Tabs, Sequence, Group)
- What guidance / help text / examples render alongside each field
- What validation applies and when each affordance is enabled
- What MCP calls dispatch on each Action submission
- How responses bind into the store and feed downstream affordances

Page seeds are the *high-leverage authoring artifact*. They are where institutional knowledge — TEMPLATE-CR section structure, SOP-002 authoring guidance, EI table conventions, review judgment criteria — gets materialized in renderable, agent-and-human-usable form.

**Authoring a seed is, in a real sense, authoring a procedure.**

---

## 4. What the framings answer

A good framing earns its keep by making questions trivial. Below are worked examples.

### 4.1 Worked example: "Do CRs live as `.md` files on disk, or natively as rendered Razem-store pages?"

The framings answer **part** of this:

- **Razem doesn't care.** Razem renders whatever MCP returns; storage is invisible. (From 2.2.)
- **No "view source markdown" or "edit the .md file directly" workflow is permitted.** Either of those would be a human-only feature: the agent has no raw-markdown primitive in MCP. Forbidden by 2.3.
- The hybrid in which `.md` files exist on disk *and* are user-facing through git/PR-diff/hand-edit is foreclosed. Either `.md` is **invisible plumbing** (canonical but never user-touched) or it is **promoted to MCP surface** (`qms_get_raw_markdown(doc_id)` returns a string, Razem renders it as a `<pre>` block, agent and human both see the same string).

What the framings deliberately **don't** answer: which of those two surviving options is correct. That question — should the QMS MCP server treat `.md` files or instance stores as canonical? — is a **QMS-internal** question, governed by QMS-specific values (auditability without the MCP layer running, git-diffability for hand review during edit, etc.).

The framings relocate the question to a clean place. They don't dissolve it.

### 4.2 Other questions the framings make trivial

- *Should Razem have CR-specific components?* — No. Razem is general-purpose; CRs are a QMS concept. (From 2.1.)
- *Should the human have an admin override?* — No. (From 2.3.)
- *Where does QMS documentation live?* — In MCP tool descriptions and Razem seed content, rendered inline. Not in a separate manual. (From 2.4.)
- *Can a human bypass MCP by editing files directly?* — No. (From 2.3.)
- *If a human-only need surfaces, what's the move?* — Add it to the MCP, never the UI alone. (From 2.3 + 2.2.)
- *Should a Razem page hardcode QMS concepts?* — No. Page seeds wire generic Razem components to MCP calls. (From 2.1.)
- *Should the rendered UI expose tool names (e.g., "this calls `qms_create`")?* — Available, probably not mandatory. UX choice, not architectural.

### 4.3 The meta-pattern

A good framing **partitions decisions into the ones it forces and the ones it cleanly hands off to a different (lower) framing.** The MCP-Razem framings answer the cross-cutting questions and identify which residual questions need their own (QMS-internal) framings. They don't try to be a single rule that answers everything.

---

## 5. Concrete artifacts in the current codebase

### 5.1 The QMS MCP server (`qms-cli/qms_mcp/`)

A FastMCP server that is structurally a thin shell over `qms-cli`. Each tool builds an argv list, runs `python qms-cli/qms.py --user <resolved> <args>` as a subprocess, and returns captured stdout+stderr as a string.

**Tool surface (21 tools, organized by REQ category):**

- Read/query (REQ-MCP-002): `qms_inbox`, `qms_workspace`, `qms_status`, `qms_read`, `qms_history`, `qms_comments`.
- Document lifecycle (REQ-MCP-003): `qms_create`, `qms_checkout`, `qms_checkin`, `qms_cancel`.
- Workflow (REQ-MCP-004): `qms_route`, `qms_assign`, `qms_review`, `qms_approve`, `qms_reject`, `qms_withdraw`.
- Execution (REQ-MCP-005): `qms_release`, `qms_revert`, `qms_close`.
- Interactive authoring (REQ-INT-022 / REQ-MCP-007): `qms_interact`. (See §5.3.)
- Administrative (REQ-MCP-006): `qms_fix`.

**Transports:** `stdio` (default), `streamable-http` (recommended for remote, with `stateless_http=True`), `sse` (deprecated).

**Identity resolution (REQ-MCP-015 / REQ-MCP-016):**

- *Trusted mode:* stdio or HTTP without `X-QMS-Identity` header; `user` parameter is taken at face value.
- *Enforced mode:* HTTP with `X-QMS-Identity` header (set by trusted infra); identity must match `user` param or call is rejected.
- *Identity collision prevention:* in-memory registry with 90-second TTL prevents two containers from claiming the same identity.

**What the MCP server deliberately does NOT do:**

- No structured response shapes — tool returns are prose strings (whatever qms-cli prints). A consumer rendering `qms_status` has to either trust the human-readable text or implement a string parser. This is a real friction point for Razem-on-MCP, and a structured-output variant per tool would help.
- No introspection — no tool exposes "what document types exist," "what fields does TEMPLATE-CR have," or "what's the state machine."
- No next-action hints in responses — every tool returns just the action's result.

### 5.2 The `cr-create` scaffold (Session-2026-04-29-002)

The first real Razem page seed for an off-MCP procedure: CR authoring. Captures the pre-approved sections of TEMPLATE-CR (sections 1–9 plus 12 References) using TextForm, ChoiceForm, ListForm, TableForm with `fixed_columns`, Group, Tabs, Visibility, InfoDisplay, and a stub Action.

The Submit Action is honest about being a stub: its `action_fn` returns the qms-cli command sequence (`qms create CR --title "..."` → checkout → write content → checkin) that *would* run once Razem gains an MCP-call primitive.

This scaffold sits in exactly the right architectural slot: it encodes the procedural layer for CR authoring. When the MCP-call primitive lands, the stub becomes functional with very little additional design work. The seed was always correct; only the action layer was missing.

### 5.3 `qms_interact` as Razem's primordial idea

`qms_interact` provides template-driven CLI prompting for document authoring: presents prompts, records responses, navigates between prompts, reopens loops, shows progress, compiles markdown preview. It's the most complex tool in the MCP surface by far.

The structural insight embedded in `qms_interact` is the right one: the procedural interior between `qms_create` and `qms_checkin` needs *guidance*, not just freeform markdown editing. So `qms_interact` recognized the procedural-layer problem and built a CLI-prompt-shaped solution to it.

Under the framings articulated here, `qms_interact` is a category error: it puts procedural-authoring scaffolding *inside* MCP, where MCP-the-protocol assumes a smart-LLM client that can drive boundary tools without help. The discomfort of `qms_interact` being an outlier on the tool list (much more complex than any other tool, with a flag soup) was always a signal — under the framings, the discomfort is *because* it's procedural-layer code wearing a boundary-tool costume.

The trajectory:

1. Recognize the procedural-layer problem inside the only available framework (MCP) → `qms_interact` born.
2. Generalize the structural insight beyond one doc-type, beyond the CLI, beyond QMS specifically → Razem born.
3. Articulate the boundary that was implicit in the generalization → §2 of this document.
4. Retire the original incarnation because the framework that grew from its insight has subsumed and surpassed it.

This is the classic "concrete tool → abstract framework → original tool gets superseded by its own generalization" arc. Hypercard → web. Specific shell utilities → pipe-and-filter. **`qms_interact` → Razem.**

When Razem-on-MCP is end-to-end functional, `qms_interact` should be deprecated and eventually removed from the MCP surface.

---

## 6. The RazemSphere horizon

Speculative but informs current architectural choices.

If Razem becomes popular, people add their own MCP servers to a "RazemSphere" — an internet just for agents (and humans, via parity). What's actually new about this:

- The pre-MCP web was built for humans and retrofitted for agents (scraping, screen-reading, brittle automation). MCP is the first protocol that's natively agent-shaped — typed tools, semantic descriptions, machine-readable schemas as a first-class artifact.
- "An internet for agents" isn't a metaphor stretched onto the existing web; it's pointing at something MCP genuinely enables that nothing previously did.
- Razem-as-uniform-renderer-on-top is then the human-accessibility layer for that agent-native internet.

What this opens up:

- **Linkability** — Razem-rendered MCP affordances have stable URLs that can be shared, embedded, handed to other agents. "URLs of the agent web."
- **Composition** — one MCP tool's response feeding another's input, rendered by a single Razem page that fans out across multiple servers. The web's hyperlink superpower applied to tool calls.
- **Auth and trust** — the hard part. Browsers handle auth, sandboxing, and same-origin isolation transparently for the human web. RazemSphere would inherit those problems plus credential delegation when an agent acts on behalf of a human against a third-party server.
- **Discovery** — no MCP server directory exists at scale today. Whether to build a registry into Razem itself or assume third parties will is an architectural choice; minimum-viable in Razem with richer directories built on top is one defensible answer.

Implication for current architecture: design Razem from the start with no QMS-specific assumptions. The QMS-on-Razem deployment becomes the **reference implementation** of an MCP+Razem deployment, demonstrating the pattern that scales to RazemSphere.

---

## 7. The long-term vision: Agent Portal as runtime environment

The endpoint of the framings:

A Claude Code session begins with a CLAUDE.md that contains a minimal explanation of what the QMS is and a directive to go to the Agent Portal and log in. Once the agent logs in, everything they can do — and all related procedures — is presented on their personal home page. Documents, session notes, and other artifacts that today live as files on disk progressively migrate into the Portal.

### 7.1 What stays in CLAUDE.md no matter how thin it gets

A few things don't fit on a form, even in the long-run vision:

- **Disposition** — agency-and-initiative norms, push-back-when-you-disagree expectation, no-flattery rule. These are about *how* to act, not *what* to do; they can't be rendered as affordances.
- **The pointer to SELF.md** — and whether SELF.md stays as a file or also moves into the Portal is its own question. SELF.md is free-form self-authored identity content; it might be the one thing that stays as a file precisely because it's not procedural.
- **The pointer to the Portal** — login URL, identity selection guidance, fallback if the Portal is unavailable.
- **The recursive-governance-loop framing**, possibly. Or this becomes a Portal page that the home page links to.

Minimum viable CLAUDE.md is probably 200–500 tokens. Everything else moves into the Portal.

### 7.2 The Portal becomes a runtime dependency

Today, CLAUDE.md + qms-cli + `.md` files all work even with zero Portal infrastructure. In the vision, the Portal being up is a precondition for the agent functioning at all. That's the same trade-off any developer-of-cloud-services accepts (GitHub being down degrades work) but it's a real shift from the current local-first posture.

Until the Portal hits production reliability, the file-and-CLI fallback paths probably need to remain functional in parallel.

### 7.3 Session notes in the Portal

Moving session notes into the Portal turns them from freeform markdown into governed artifacts — they can have structure (Current State, Progress, Blocking, Next), versioning, a render that supports the recovery pattern. It also makes them potentially review-eligible in a way they aren't today.

Whether that's a feature or a footgun depends on what behaviors it creates. Probably worth keeping notes private to the agent + Lead even after they live in the Portal.

### 7.4 What about Flow State (the application code)?

The Portal handles **QMS-side activities** (governance, authoring, review, evidence). Flow State coding still happens in editors and terminals — the IDE handles code, the Portal handles governance. The transition between "I'm coding Flow State" and "I'm authoring the CR that governs this code change" is Portal-mediated, but neither replaces the other.

Clean separation: **Portal for governance, IDE for code, nothing else needs a permanent home.**

---

## 8. Migration phases

The vision is far off, but every intermediate decision can be evaluated against it.

- **Phase 0** (current): file-and-CLI canonical; Portal doesn't exist; Razem is alpha-quality with no MCP-call primitive.
- **Phase 1** (post-MCP-call-primitive + cr-create-functional): Portal exists for SOME workflows. CR authoring happens via Portal; review still via subagent + qms-cli; everything else via existing means.
- **Phase 2** (more page seeds): inbox, workspace, status, review, approval all in Portal. CLAUDE.md starts shrinking. `qms_interact` retired.
- **Phase 3** (session notes, documentation in Portal): CLAUDE.md is minimal. Quality Manual procedural content lives in seeds and inline help. SELF.md may or may not have moved.
- **Phase 4** (full vision): the agent logs in and the home page is the entire surface.

Each phase is independently valuable; commitment to the endpoint isn't required to start. But the framings tell you the endpoint, and that lets every intermediate decision be evaluated against "does this move us toward Portal-as-environment, or does it accumulate debt that'll have to be undone?"

---

## 9. Invariants to preserve across all phases

These must stay true at every intermediate state, or the architecture drifts:

1. **MCP remains the boundary.** No Portal-only escape hatches. No human-only features bolted on without a corresponding MCP capability.
2. **Parity is preserved.** Whatever the Portal exposes to humans is exactly what the agent can do via MCP.
3. **Razem stays domain-agnostic.** No QMS-specific code in Razem. Page seeds are the locus of QMS-specific knowledge.
4. **Procedural content lives in seeds, not in MCP.** When a seed is built, the procedural intent moves out of any MCP-side scaffolding (e.g., `qms_interact`) and into the seed.
5. **MCP responses converge on structured (or at least consistently-parseable) shapes.** Today they're prose. Migration toward structured outputs makes Razem rendering robust.

---

## 10. Open questions

Things the framings don't answer; collected here so they can get their own (QMS-internal) framings later.

- **Document storage canonicality.** `.md` files on disk vs. Razem instance stores. (See §4.1.) Driven by QMS-internal values about auditability, git-diffability, and what survives the MCP layer being down.
- **Structured MCP outputs vs. prose-with-parsing.** Whether the QMS MCP server should return structured JSON for tools like `qms_status` (cleaner for Razem rendering, expands MCP scope) or keep returning prose with Razem implementing per-tool parsers (keeps MCP minimal, pushes complexity into seeds).
- **MCP-call primitive design in Razem.** A new Action variant is the obvious shape, but the details — how does it declare which server, how does response binding work, how are errors surfaced, how do streaming responses behave — are open.
- **Auto-generation vs. hand-curation of seeds.** A starter seed can probably be generated from an MCP tool's JSON Schema. Workflows that span multiple tools can't. The boundary between "auto-generated starting point" and "hand-curated seed" needs articulation.
- **Auth/identity in RazemSphere.** Today's MCP identity machinery (`X-QMS-Identity` header, instance lock) is QMS-specific. A general Razem-on-MCP solution needs a uniform credential layer.
- **Discovery in RazemSphere.** Whether Razem ships a registry, or assumes third parties will build one. Personal taste leans toward minimum-viable in Razem.
- **SELF.md's home.** Stays as a file (because it's identity-not-procedure)? Or moves into the Portal? Both have arguments.
- **Whether recursive-governance content lives in the Portal or stays in CLAUDE.md.** It's conceptual rather than procedural, but conceptual content in the Portal would feel different from procedural content there.

---

**END OF DOCUMENT**
