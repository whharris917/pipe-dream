# Hypermedia, HATEOAS, and the Agent API: A Research Report

*Prepared for the Pipe Dream project, March 2026.*
*Context: Supporting the planned refactor of the Agent Portal API from single-endpoint action dispatch to resource-oriented, affordance-driven REST endpoints.*

---

## 1. The Hypermedia Problem

The "hypermedia problem" is a two-decade tension at the heart of REST.

When Roy Fielding defined REST in his 2000 doctoral dissertation, he described an architecture modeled on the web as it existed at the time: HTML documents exchanged over HTTP, with links and forms embedded in every response telling the client what it could do next. Hypermedia — links, forms, actions — was not a nice-to-have. It was the mechanism that allowed clients and servers to evolve independently. A browser doesn't need to know all of Wikipedia's URLs in advance; it follows links.

Then JSON happened. The industry adopted the vocabulary of REST ("resources," "endpoints," "HTTP methods") but dropped the constraint that made it work: hypermedia. JSON has no native concept of links between resources. What emerged was something closer to RPC-over-HTTP: clients hardcode URLs from documentation, construct requests from out-of-band knowledge, and break when the server changes. Fielding himself noted the irony — "REST" came to mean the opposite of what he described.

HATEOAS (Hypermedia as the Engine of Application State) was the formal name for the missing constraint. It says: every API response must include the set of actions currently available to the client, expressed as hypermedia controls. The client doesn't need prior knowledge of the API's URL structure. It reads the response, discovers what it can do, and acts.

The industry largely rejected HATEOAS for human-consumed APIs, for understandable reasons:

- **Human developers don't follow links.** They read documentation, hardcode endpoints, and move on. The dynamic discovery that HATEOAS provides is overhead they don't need.
- **JSON isn't a natural hypermedia.** There's no standard way to represent links in JSON. Competing formats (HAL, JSON-LD, Hydra, Siren, Collection+JSON) fragmented the ecosystem.
- **No generic client emerged.** The dream of a "browser for APIs" — a single client that could navigate any HATEOAS API — never materialized. Every API required custom integration regardless.
- **Tooling was absent.** Frameworks and client libraries optimized for hardcoded endpoints, not dynamic link traversal.

The result: 20+ years of APIs that are structurally incapable of telling their clients what to do next. The client must already know.

---

## 2. Why AI Agents Change Everything

The arguments against HATEOAS assumed a human developer as the API consumer. AI agents invert every one of those assumptions.

**Agents don't read documentation once and hardcode.** They interact with APIs at runtime, repeatedly, across changing state. They need to know what's available *right now*, not what was documented six months ago.

**Agents benefit from constrained choice.** An LLM with access to 200 tools performs worse than one with access to the 5 tools relevant to its current state. Hypermedia naturally constrains the action space to what's currently valid — the proceed button only appears when prerequisites are met, the delete option only appears on resources that can be deleted.

**Agents can follow links.** The thing human developers refused to do — parse the response, discover the available actions, select one, act — is exactly how an LLM agent naturally operates. It reads structured output and decides what to do next. The dynamic discovery that was overhead for humans is the native interaction model for agents.

**Agents need the "why," not just the "how."** A traditional endpoint `POST /api/users` tells the agent the mechanism. A hypermedia affordance with a label, description, and body template tells the agent the intent: "Create a new user account — requires name and email." The semantic context that humans get from documentation, agents get from the affordance itself.

As Darrel Miller, partner API architect at Microsoft, put it: **"AI agents don't solve the hypermedia problem, but hypermedia does solve the AI agent problem of tool selection and efficiently maintaining context."**

Miller also observed that OpenAI's function calling descriptions are "effectively hypermedia affordances used by the LLM to do selection. The only missing piece is agents/tools using application state to determine the current set of relevant tools." In other words: the industry has already reinvented half of HATEOAS inside LLM tool-calling frameworks. The other half — tying affordance availability to application state — is what a proper hypermedia API provides.

Kevin Duffey, an independent API consultant, expressed the shift directly: "I genuinely believe HATEOAS was just waiting for the right technology. Had we had powerful AI like LLMs and frameworks like the Model Context Protocol two decades ago, the entire API design philosophy might be radically different today."

---

## 3. GRAIL: Goal-Resolution through Affordance-Informed Logic

Mike Amundsen — author of multiple O'Reilly books on API design and a leading voice in the hypermedia community — has built a framework called GRAIL that demonstrates what hypermedia-driven agent interaction looks like in practice.

### The Core Loop

GRAIL gives an agent two things: a **goal** and an **environment**. The environment is not a script or a workflow. It is a collection of affordances — things that may or may not be possible depending on current conditions.

The agent does not plan. It does not decompose the goal into steps. It attempts the goal immediately.

If the attempt succeeds, it's done. If it fails, the server's response explains *why* — it returns the unmet preconditions as other affordances the agent can attempt. The agent pushes the original goal onto a stack, resolves the precondition, and retries.

**Example:** The agent is told "Update the user's email." It invokes `updateEmail`. The server blocks the action: the user isn't authenticated. The response includes an `authenticate` affordance. The agent authenticates, retries `updateEmail`, and succeeds.

The workflow — authenticate, then update — was never designed. It was **discovered** by the agent through interaction with the environment. As Amundsen writes: "Designed workflows anticipate the future. Discovered workflows reflect the present."

### Why This Matters

GRAIL's key insight is that **the environment, not the agent, holds the procedural knowledge.** The server knows what preconditions exist. The server knows what actions are available in each state. The agent's job is not to reason about the full state space — it's to read the affordances and navigate.

This has direct implications for reliability. An agent that follows affordances cannot attempt an invalid action (the affordance isn't there). It cannot skip a required step (the precondition blocks it). It cannot get stuck in an unexpected state (the environment always tells it what's possible). The failure mode is not "the agent hallucinated a plan" — it's "the agent couldn't find an affordance," which is a tractable, debuggable problem.

Amundsen frames this as a deliberate rejection of the "reasoning" paradigm: "Instead of pretending the LLM can reason, GRAIL strips away unnecessary options and asks the agent to simply follow the affordances — the actions that are currently possible given the current state."

### Affordances Before Understanding

In a February 2026 post, Amundsen connected this to neuroscience research showing that humans detect navigational affordances — viable routes of movement — before they consciously interpret a scene. The visual system's first output is not "what am I looking at?" but "what can I do here?"

His conclusion for API design: "Instead of training agents to reason first and act later, we should train them to detect and categorize navigational affordances first. What actions are available? Which are blocked? Which are conditional? Which disappear once taken?"

This maps directly to the pattern we've already built: the Agent Portal's GET response is a Field of View containing the current state and the set of affordances available right now. The agent reads the affordances, picks one, acts, and reads the new affordances.

---

## 4. The Emerging Consensus

Across the sources surveyed, a consistent set of principles is forming around agent-ready API design:

### 4.1 Affordances Must Be In-Band

Affordances — the available actions — must be part of the API response, not external documentation. The agent should be able to operate from a single entry point without any prior knowledge of the API's URL structure. Every response tells the agent what it can do next.

> "Schemas explain how to talk; hypermedia explains what to do." — Mike Amundsen

### 4.2 State Constrains the Action Space

The set of available affordances must reflect the current application state. An order that hasn't been paid can't be shipped. A CR that hasn't had its required fields filled can't proceed. The API response only includes actions that are currently valid. This is both a usability feature (the agent can't attempt invalid actions) and a safety feature (the server controls what's possible).

### 4.3 Affordances Must Be Self-Describing

Each affordance should carry enough information for the agent to act without external context: a human-readable label (what it does), the HTTP method and URL (how to invoke it), the body template (what to send), and any constraints on valid values (options for constrained fields). The affordance is a complete instruction.

### 4.4 Consistency Reduces Agent Cognitive Load

Every inconsistency in how an API presents itself is something the agent must learn to handle. Consistent patterns for pagination, error reporting, field types, and action shapes allow the agent to reuse interaction strategies across different parts of the API.

### 4.5 Errors Are Affordances Too

When an action fails, the error response should guide the agent toward resolution — not just report the failure. GRAIL demonstrates this: a blocked action returns the preconditions that must be satisfied, expressed as affordances the agent can attempt. The error *is* the next step.

### 4.6 The API Is the Control Surface

For AI safety and observability, hypermedia-driven APIs have a structural advantage: the server explicitly controls what the agent can do at every step. There is no moment where the agent is operating from a hallucinated plan with no server-side validation. Every action the agent takes was offered by the server.

> "Systems that clearly expose their affordances are not just easier to use, they are easier to observe and supervise." — Mike Amundsen

---

## 5. How Our Agent Portal Aligns

The Agent Portal's existing design already implements most of these principles. The planned endpoint refactor strengthens the alignment.

### What We Already Have

| Principle | Current Implementation |
|-----------|----------------------|
| In-band affordances | GET returns `affordances[]` with label, method, URL, body template |
| State-constrained actions | Proceed gate appears only when required fields are set; visibility rules hide irrelevant fields |
| Self-describing affordances | Labels include current value; `options` list for constrained types (as of today's commit) |
| Structured feedback | POST returns `{attempted_action, outcome, effects}` — the agent knows exactly what changed |
| Error-as-guidance | Error responses use the same shape: `{attempted_action, outcome: {error: "..."}, effects: {}}` |

### What the Endpoint Refactor Adds

**Current:** All actions go through `POST /agent/create-cr` with an action discriminator in the body:
```json
{"action": "set_field", "field": "affects_code", "value": true}
```

**Proposed:** Each action has its own URL. The affordance is a literal HTTP instruction:
```json
{
  "label": "Set Code Impact (current: false)",
  "method": "POST",
  "url": "/agent/create-cr/affects_code",
  "body": {"value": "<value>"},
  "options": [true, false]
}
```

This change aligns with the consensus in three specific ways:

1. **The affordance becomes a complete HTTP request template.** Method + URL + body. The agent fills in `<value>` from `options` and sends. No interpretation of action types, no dispatch grammar, no translation layer. This is the HATEOAS ideal: the hypermedia control *is* the instruction.

2. **The URL carries semantic meaning.** `POST /agent/create-cr/affects_code` is self-documenting in access logs, debugging tools, and monitoring dashboards. The server can validate per-field without dispatch logic. Each endpoint knows its type and constraints.

3. **Bodyless actions become natural.** `POST /agent/create-cr/proceed` with no body. The URL *is* the action. This eliminates the awkward `{"action": "proceed"}` body for actions that have no parameters.

### What We Don't Yet Have (Future Considerations)

- **Entry-point discovery:** A true HATEOAS API would let the agent start from a single root URL and discover all workflows. Currently, the agent needs to know `/agent/create-cr` as its entry point.
- **Cross-workflow linking:** When the CR creation workflow completes, the response could include an affordance linking to the newly created CR's review workflow. Currently, workflows are isolated.
- **Semantic descriptions beyond labels:** Standards like Hydra or JSON-LD could provide richer machine-readable metadata about what each affordance means. For now, labels and instructions serve this purpose adequately.

These are natural extensions, not blockers. The endpoint refactor establishes the structural foundation that makes them possible.

---

## 6. Conclusion

The planned refactor from single-endpoint action dispatch to resource-oriented affordance-driven endpoints is not just a local improvement to our API shape. It aligns the Agent Portal with the emerging consensus on how APIs should be designed for AI agent consumption:

- HATEOAS, the REST constraint that the industry rejected for 20 years, is being recognized as the natural interaction model for autonomous agents.
- The GRAIL framework demonstrates that affordance-driven navigation produces more reliable agent behavior than pre-planned workflows.
- Leading voices in the API design community (Amundsen, Miller, Duffey, Swiber) are converging on the principle that APIs must embed discoverable, state-constrained affordances in every response.
- Our existing design already implements the core pattern. The endpoint refactor makes each affordance a literal, self-contained HTTP instruction — the simplest possible interface between an agent and a server.

---

## Sources

- [HATEOAS: The API Design Style That Was Waiting for AI](https://nordicapis.com/hateoas-the-api-design-style-that-was-waiting-for-ai/) — Nordic APIs, November 2025
- [Hypermedia is the missing control surface for AI](https://mamund.substack.com/p/hypermedia-is-the-missing-control) — Mike Amundsen, February 2026
- [Don't design workflows, discover them](https://mamund.substack.com/p/dont-design-workflows-discover-them) — Mike Amundsen, January 2026
- [Why I keep talking about affordances](https://mamund.substack.com/p/why-i-keep-talking-about-affordances) — Mike Amundsen, February 2026
- [Stop Calling It Reasoning](https://mamund.substack.com/p/stop-calling-it-reasoning) — Mike Amundsen
- [Preparing Your APIs for AI Agents](https://assets.treblle.com/ebooks/preparing-your-apis-for-ai-agents.pdf) — Treblle / Mike Amundsen
- [GRAIL framework (source code)](https://github.com/mamund/grail-public) — Mike Amundsen
- [How To Prepare Your API for AI Agents](https://thenewstack.io/how-to-prepare-your-api-for-ai-agents/) — The New Stack
- [Designing Agent-Ready APIs in the Real World](https://agrawal-pulkit.medium.com/designing-agent-ready-apis-in-the-real-world-86d8a9128a45) — Pulkit Agrawal
- [Affordance Representation and Recognition for Autonomous Agents](https://arxiv.org/html/2510.24459v1) — arXiv, October 2025
- [Signifiers as a First-class Abstraction in Hypermedia Multi-Agent Systems](https://www.southampton.ac.uk/~eg/AAMAS2023/pdfs/p1200.pdf) — AAMAS 2023
- [Modern API Design Best Practices for 2026](https://www.xano.com/blog/modern-api-design-best-practices/) — Xano
- [Pragmatic REST: APIs without hypermedia and HATEOAS](https://www.ben-morris.com/pragmatic-rest-apis-without-hypermedia-and-hateoas/) — Ben Morris (the counter-argument)
- [How Did REST Come To Mean The Opposite of REST?](https://htmx.org/essays/how-did-rest-come-to-mean-the-opposite-of-rest/) — htmx essays
- [APIs in the age of AI: Echoes of the past, whispers of the future](https://www.cutover.com/blog/apis-in-the-age-of-ai) — Cutover
- [AI at TPAC 2025](https://www.w3.org/blog/2025/ai-at-tpac-2025/) — W3C
