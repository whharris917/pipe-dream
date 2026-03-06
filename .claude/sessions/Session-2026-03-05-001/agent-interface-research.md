# Research Synthesis: Best Practices for AI Agent Interaction Surfaces

*Session-2026-03-05-001 | Compiled from 3 research agents + targeted SWE-agent deep dive*

---

## 1. The SWE-agent ACI Concept (NeurIPS 2024)

The most directly relevant research for our design. SWE-agent introduced the concept of **Agent-Computer Interfaces (ACIs)** — purpose-built interfaces for LLM agents, analogous to how GUIs are purpose-built for humans.

### 1.1 The Core Framing

> "LM agents represent a new category of end users with their own needs and abilities" requiring "specially-built interfaces."

Just as humans benefit from IDEs over raw terminals, LLM agents benefit from interfaces designed for their specific capabilities and limitations. The paper draws an explicit parallel between Human-Computer Interaction (HCI) and Agent-Computer Interaction (ACI), arguing that **interface design is as important as model capability** for agent performance.

**Quantitative proof:** SWE-agent with its custom ACI solved **10.7 percentage points** more instances than the same model with only a default Linux shell. The ACI — not the model — was the primary differentiator.

### 1.2 Three Design Principles

**Principle 1: Simple and Clear Actions**
- Commands should have few options and concise documentation
- Complex bash commands with dozens of flags are hard for agents
- Simplifying commands reduces the need for demonstrations or fine-tuning

**Principle 2: Efficient Actions**
- Important operations should be consolidated into as few actions as possible
- Each action should make meaningful progress toward a goal in a single step
- File navigation and editing should be single commands, not multi-step bash pipelines

**Principle 3: Informative Feedback**
- High-quality feedback provides substantive information about the current environment state and the effect of the agent's recent actions
- Feedback should NOT include unnecessary details
- Empty output gets explicit acknowledgment: "Your command ran successfully and did not produce any output" (prevents ambiguity between failure and legitimate empty results)

### 1.3 Interface Components

**File Viewer:**
- Displays exactly **100 lines** at a time (empirically optimized)
- Annotated with line numbers and ellipsis markers for unseen content
- Navigation: `scroll_down`, `scroll_up`, `goto` commands
- Replaces raw `cat` — prevents dumping entire files into context

**File Editor:**
- Edits performed on explicit, user-specified line ranges
- **Linting guardrail:** A code linter runs on every edit submission; syntactically invalid changes are automatically rejected, forcing the agent to fix errors immediately
- Provides immediate feedback showing the result of the edit

**Search/Navigation:**
- Custom commands: `find_file`, `search_file`, `search_dir`
- Search results capped at **50 hits** maximum to prevent context overflow
- Results are summarized: "list each file that had at least one match" — no verbose context around matches
- Excessive contextual detail proved counterproductive

**Context Management:**
- The most recent **5 steps** are shown in full (action + observation)
- All older observations are **collapsed to a single line each** — retaining the action taken but removing the output
- This preserves the plan/action chain-of-thought while eliminating stale file content
- Canonicalized, explicit format for recent action/observation pairs

### 1.4 The Agent's Action Format

Each agent step is an atomic **{thought, command}** pair:
- The agent first reasons in natural language ("thought")
- Then issues a single command
- The ACI translates the command into an environmental action and returns an observation

This two-part structure separates reasoning from action, aligning with the "Let Me Speak Freely" finding that reasoning quality degrades when constrained to structured formats.

### 1.5 Ablation Study Results

| Component Removed | Performance Drop |
|---|---|
| Full ACI → Shell only | **-10.7 pp** |
| No edit command (use shell editing) | **-7.7 pp** |
| No linter guardrail | **-3.0 pp** |

The file editor was the single most impactful component. The linting guardrail — which prevents the agent from introducing broken syntax — was the second most impactful. Context management and search were also significant contributors to the overall 10.7pp gain.

### 1.6 Key Takeaway for Our Design

The ACI is NOT the engine. It is a purpose-built rendering layer between the engine and the agent. The same underlying capability (editing files) can be presented through a shell (`sed`, `awk`, `echo >>`) or through a designed interface (`edit 15:20 <content>`), and the difference in agent performance is enormous. **Interface design is the primary lever for agent effectiveness.**

---

## 2. Structured Output: What Format Works Best

### 2.1 The Headline Finding: Format Constraints Hurt Reasoning

"Let Me Speak Freely?" (Tam et al., EMNLP 2024) demonstrated **10-15% performance degradation** on reasoning tasks when models were locked into JSON mode vs. free-form generation. Classification/extraction tasks showed no degradation.

**Implication:** When a node requires the agent to REASON (root cause analysis, hypothesis formation, decision-making), don't force structured output during generation. When a node requires the agent to CLASSIFY or FILL FIELDS (enum selection, data entry), structured output is fine.

### 2.2 The Two-Step Pattern

The winning approach across multiple papers (CRANE at ICLR 2025, the G&O method, Instructor library):

1. **Reason freely** in natural language
2. **Then format** the output into the required structure

CRANE achieved **up to 10 percentage point accuracy improvement** over both pure constrained decoding AND standard unconstrained decoding.

### 2.3 Format Accuracy Rankings

**For input data (what the agent reads):**
- YAML was strongest for 2 of 3 models tested on nested structures
- YAML outperformed XML by **17.7 percentage points** (GPT-5 Nano)
- XML requires **80% more tokens** than Markdown for the same data
- Claude specifically performs well with XML-tagged sections

**For output data (what the agent produces):**
- Tool/function calling is **50% more robust** than raw JSON mode (less variation from schema changes)
- `strict: true` mode (OpenAI, Anthropic) achieves **99%+ schema adherence**

### 2.4 Field Naming Is Critical

The Instructor library found that renaming fields swung accuracy from **4.5% to 95%**. Specific findings:
- Adding a "reasoning" field to the schema increased accuracy by **60%** on GSM8k
- Field ordering matters (Python dict ordering affects output quality)
- Negative examples are important for defining boundaries

### 2.5 Key Takeaway for Our Design

- Present state to the agent in **YAML or Markdown** (token-efficient, high accuracy)
- For slot-filling, use **tool/function calling** (robust, schema-enforced)
- Include a **free-form reasoning slot** on nodes that require judgment — don't make every slot an enum
- **Name slots carefully** — the slot name IS the primary context the LLM uses
- Include **slot-level hints** (the `hint` field in prototype-2 is validated by this research)

---

## 3. How Agent Frameworks Present State

### 3.1 The Industry Convergence

All major frameworks have converged on a common agent loop:

```
Gather context (read/search) → Think (natural language) → Act (function call) → Observe (structured result) → Verify → Repeat
```

### 3.2 State Management Patterns

| Framework | State Model |
|---|---|
| **LangGraph** | Typed schema (TypedDict/Pydantic) with explicit reducer functions for parallel merge |
| **CrewAI** | Role + current task + upstream outputs (implicit in task chain) |
| **AutoGen** | Conversation history IS the state |
| **Semantic Kernel** | Deprecated explicit planners in favor of native function calling — "the LLM IS the planner" |
| **Claude Agent SDK** | Each agent step is a function call with typed input/output; sub-agents provide context isolation |
| **OpenAI Agents SDK** | Structured output as first-class API feature; state chaining built in |

**The trend:** Moving AWAY from conversation-as-state (AutoGen model) and TOWARD typed state schemas (LangGraph model). The agent sees a defined schema of "where things stand," not just the last N messages.

### 3.3 Coding Agent State Presentation

| Agent | What It Sees |
|---|---|
| **SWE-agent** | 100-line file window + last 5 action/observation pairs + collapsed history |
| **Aider** | Repository map via AST (PageRank-ranked symbols, ~8.5-13k tokens) |
| **Claude Code** | Layered system prompts + tool results as structured blocks + memory files |
| **Copilot Workspace** | Spec (current vs desired) → Plan (file-level actions) → Diffs |
| **Kiro** | Requirements (EARS notation) → Architecture → Implementation tasks (dependency-sequenced) |
| **OpenHands** | Event stream of past actions/observations; agent emits Python code as actions |

**Kiro is the closest analog to our system** — it enforces a structured pipeline where the agent sees requirements with acceptance criteria, then a system design, then discrete implementation tasks ordered by dependency. This is essentially a workflow.

---

## 4. Context Window Management

### 4.1 The Headline Finding: Less Is More

**Anthropic's own research:** "A focused 300-token context often outperforms an unfocused 113,000-token context."

**JetBrains (NeurIPS 2025):** Simple observation masking (just hiding old observations) is **as effective as LLM summarization** while being **52% cheaper**. In 4 of 5 test settings, masking was cheaper AND performed equal or better.

### 4.2 The Dominant Pattern: Progressive Disclosure

Show metadata first, details on demand. Applied universally:

- **Meta-Tool Pattern** (SynapticLabs): Two meta-tools (search_tools, call_tool) replace loading all tool definitions upfront. **85-95% token savings.**
- **Aider's repo map:** Agent sees ranked function signatures, not raw files. Loads full files only when needed.
- **Will Larson's file handling:** Always include metadata (file ID, name, size); agent uses `peek`/`load` to get details.
- **SWE-agent:** 100-line windows, 50-hit search caps, 5-step observation history.

### 4.3 The Four Strategies (Anthropic)

1. **Write:** Save information outside the context window for later retrieval
2. **Select:** Pull only relevant information into context at each step
3. **Compress:** Summarize or reduce information before adding to context
4. **Isolate:** Split context across multiple agents, each with narrow scope

### 4.4 Letta's Kernel Context Model

Treats the context window like an OS manages RAM:
- **Kernel context** (mutable agent state) is always in-context
- **Message buffer** has configurable size; old messages are summarized or evicted
- **Archival memory** stores overflow, retrievable via search tools
- The agent has **explicit tools to manage its own memory**

### 4.5 Key Takeaway for Our Design

- Show the agent **only the current node** (its slots, prompt, context) + a compact summary of progress
- The full graph is available on demand but NOT shown by default
- Completed nodes are **collapsed to outcomes** (slot values only, no prompts/context)
- The agent never needs to see the engine internals (graph structure, edge conditions)
- Use **tool calls** for navigation (inspect a specific node, view progress, see what's ready)

---

## 5. Workflow Engine Task Presentation Spectrum

### 5.1 Full-DAG Engines: The Executor Sees Only Its Task

Temporal, Airflow, and Prefect all share a key architectural trait: the **executor sees only its own task**, not the full DAG. In Temporal, a Worker polls a Task Queue and receives either a Workflow Task (with event history for replay) or an Activity Task (with only the activity's input parameters, attempt number, and heartbeat details). An Activity **cannot** access the Workflow's event history directly. In Airflow, each task runs as an isolated process receiving a `TaskInstance` object with metadata and XCom for inter-task data passing. Prefect differs: an entire flow runs in a single process, so tasks share Python state — but each task still receives only its explicit parameters via `prefect.runtime` context.

**The convergence:** Even in systems where the full DAG is visible to *operators* (dashboards, monitoring), the **executor** receives a scoped view: its inputs, its metadata, its tools. The DAG is an orchestration concern, not an execution concern.

### 5.2 Electronic Batch Records: The Gold Standard for Compliance

EBR systems in pharma/biotech represent the opposite extreme: **strict one-step-at-a-time execution with zero forward visibility**. The operator sees only the current step's work instructions, data entry fields, and required acknowledgments. Step N cannot begin until Step N-1 has all required data entered, validated, and confirmed. Key enforcement mechanisms:

- Mandatory data fields that **block advancement**
- Electronic signatures at critical steps
- Real-time equipment integration for automatic data logging
- "Review by exception" that flags deviations

The Master Batch Record (MBR) defines the recipe; the EBR is the execution instance. This is the closest existing paradigm to what we're building: a **system-enforced sequential workflow** where the executor fills slots and advances, with validation gates preventing progression on invalid data.

### 5.3 BPMN Engines: The "Full Form Per Task" Model

BPMN engines (Camunda, Flowable) sit in the middle. When a process reaches a **user task** node, execution stops and a task instance appears in a tasklist. The user sees:

- The task's **form** (work instructions + data capture fields)
- Assignment information, due/follow-up dates, priority
- Task headers (static metadata from the process definition)

Forms are defined declaratively — Camunda uses JSON form definitions linked via `formId`, Flowable uses a `fields` array (each with id, name, type, required, placeholder). Supported types span text, numeric, checkbox, date, dropdown, radio, people selectors, and file upload. Critically, the user sees **only their assigned task**, not the broader process model.

**Flowable's outcome mechanism** is notable: forms can define `outcomes` (approve/reject), stored as variables (`form_<id>_outcome`) that enable conditional routing downstream. This maps directly to our Edge `when` conditions.

### 5.4 Key Takeaway for Our Design

The spectrum from Temporal (scoped task view) to EBR (locked-step, zero forward visibility) to BPMN (form-per-task with outcomes) validates our architecture. Our engine should present like an EBR with BPMN's form semantics: **one node at a time, with typed slots as the form, and slot values driving edge conditions**. The agent never needs to see the graph.

---

## 6. Declarative Forms and the Schema Bridge

### 6.1 The Three-Layer Separation

All major form libraries (RJSF, SurveyJS, Formio) share the same core principle: separate **what** data to collect from **how** to render it.

- **React JSON Schema Form (RJSF):** JSON Schema (fields, types, constraints) + uiSchema (rendering hints) + formData (current values). The same schema can be rendered as HTML for humans or serialized as a text prompt for an AI agent.
- **SurveyJS:** JSON declarative model + business logic engine (`survey-core`) + rendering as a separate concern. Every object supports `toJSON()`/`fromJSON()`.
- **Formio:** `components` array in JSON — each with type, label, key, validation rules, and conditional visibility.

### 6.2 JSON Schema as the Universal Bridge

The key insight: **JSON Schema already bridges forms and LLM structured output.** OpenAI's Structured Outputs and Anthropic's tool use both accept JSON Schema to constrain output. The translation is direct:

| Form Concept | HTML Rendering | AI Agent Rendering |
|---|---|---|
| `{type: "string", title: "Batch Number", required: true}` | `<input>` element | Text instruction + schema-constrained output |
| `{type: "string", enum: ["Pass", "Fail"]}` | `<select>` dropdown | Enum constraint in tool parameter |
| Validation rules | Client-side JS | Schema enforcement (`strict: true`) |
| Conditional visibility | Show/hide DOM elements | Dynamic `required_slots` list |

**Schema-based prompting** formalizes this further: rather than natural-language instructions, the task is expressed as a JSON schema for both input and output, exploiting the fact that LLMs trained on code recognize formal specifications naturally.

### 6.3 Key Takeaway for Our Design

Our Slot definitions **are** a form schema. The engine's rendering layer translates `Slot {name, type, required}` to either a text prompt (for AI agents) or a form field (for future human UIs) — the same data model serves both. This validates the decision to make Slot the primitive rather than "prompt" or "field."

---

## 7. Conversational Slot-Filling

### 7.1 Rasa's Form Abstraction

In Rasa, a **form** is a loop that repeatedly prompts until all required slots are filled. The mapping to our primitives is direct:

| Rasa Concept | Our Concept |
|---|---|
| Form | Node |
| Slot (with type + extraction) | Slot (with type + writable) |
| `required_slots` list | Node's writable slots |
| `utter_ask_<slot>` template | Slot hint / node prompt |
| `validate_<slot>` method | Slot type constraint + edge `when` |
| `requested_slot` tracker | Engine's "current frontier" |

### 7.2 Validation and Re-prompting

Rasa validates each slot via custom `validate_<form_name>` actions. When validation fails, the method sets the slot to `None`, which **invalidates it and triggers re-prompting**. This is the conversational equivalent of SWE-agent's linting guardrail: immediate rejection of invalid input forces correction before advancing.

### 7.3 Progressive Disclosure via Dynamic Slots

Rasa achieves progressive disclosure by overriding `required_slots()`: based on previously filled values, the form dynamically adds or removes slots. This maps to our **conditional edge activation** — downstream nodes (and their slots) only become visible when their incoming edges evaluate to true.

### 7.4 Interruption Handling

Rasa supports mid-form interruptions: the user asks an off-topic question, the system handles it, then returns to the form without losing state. For our engine, this maps to the agent using **navigation tools** (inspect a node, check progress) without abandoning the current node's partially-filled state.

### 7.5 Key Takeaway for Our Design

A workflow node with typed slots **is** a Rasa form. The engine should support: (1) slot-level validation with re-prompting, (2) conditional slot activation based on prior values, and (3) state preservation during agent "interruptions" (tool use, navigation queries).

---

## 8. The Agentic UX Landscape

### 8.1 The Dominant Pattern: Function-Calling with Schema Contracts

The 2025-2026 consensus for presenting work to LLM agents is **function-calling with JSON Schema contracts**. Agents receive explicitly parameterized tool definitions specifying accepted parameters and expected results. The task anatomy follows five stages: Inputs (objectives, constraints) -> Plan (tasks with dependencies) -> Tools (APIs with parameters) -> Outputs (structured artifacts) -> Verification (schema validation).

### 8.2 CrewAI: The Closest Production Analog

CrewAI provides the most explicit "task presentation" model for LLM agents. Each Task has:

- `description`: Natural language instructions (our node prompt)
- `expected_output`: Completion criteria (our slot definitions)
- `context`: Upstream task outputs that feed this task (our completed predecessor nodes)
- `tools`: Available capabilities
- `output_pydantic`/`output_json`: Schema-validated structured output (our Slot types)
- `guardrail`: Validation function with retry logic (default 3 retries)
- `human_input=True`: Human-in-the-loop review

This is essentially the **EBR/form paradigm translated for AI**: the agent receives a step description, required output schema, available tools, and context from prior steps.

### 8.3 Workflow Automation Platforms and AI Nodes

**n8n** is the most AI-native automation platform, with an AI Agent node supporting multiple agent types (Conversational, ReAct, Plan and Execute, SQL, Tools Agent), sub-nodes for model selection, memory systems, vector stores, and tool definitions. The key architectural insight is **mixing deterministic automation steps with AI decisions** — you can place human-in-the-loop approval nodes, error handling, and conditional branching around AI steps. Zapier offers simpler GPT integration (prompt-in, text-out) with no agentic behavior. Make provides moderate agent support with conditional branching.

### 8.4 Three Agentic UX Patterns

Research has crystallized three UX patterns for AI agent interaction:

1. **Collaborative/Chat**: Bidirectional conversation for exploratory tasks where neither the user nor LLM knows the exact goal upfront
2. **Embedded**: AI invisibly integrated into existing workflows (Copilot autocomplete, Notion Autofill) — the "task" is inferred from context
3. **Asynchronous**: Background agents performing long-horizon tasks independently, requiring novel review UIs

The prediction is that chat-based interfaces will shrink to under 20% of agentic UX, with embedded and async patterns dominating. **Our engine operates in the async pattern** — the agent works through a workflow independently, with human review at stage gates.

### 8.5 Key Takeaway for Our Design

CrewAI's task model validates our architecture almost exactly: description + output schema + upstream context + validation = our Node + Slots + completed predecessors + Edge conditions. The key differentiator is that we operate in the **async/embedded** UX pattern (agent works through the workflow, human reviews at gates), not the collaborative chat pattern. This means our rendered view should be optimized for **autonomous progression**, not conversational back-and-forth.

---

## 9. Implications for Our Engine's Rendered View

### 9.1 What the Agent Should See at Each Step

Based on the research, the optimal rendered view for a workflow node is:

```
[PROGRESS: 4/12 nodes complete | 2 ready | Branch: main path]

## Current: Observe and Document Symptoms (node: diagnostic.observe)

Gather all observable facts about the problem. Do not jump to conclusions.

### Provide:
- symptoms (text, required): What symptoms are present?
- onset (text, required): When did the problem start?
- affected_systems (text, optional): What systems or components are affected?
```

Key properties:
- **Compact progress indicator** (not the full graph)
- **Current node prompt** as natural language (the system → agent content)
- **Slots listed with names, types, and hints** (the agent → system expectation)
- **No engine internals** (no edge conditions, no graph structure, no node IDs unless needed)

### 9.2 What the Agent Should Do

The interaction should be **tool/function calling**, not freeform text parsing:

```
respond(
  symptoms="The application crashes on startup with a segfault...",
  onset="First reported 2026-03-04 after the v2.3 deploy",
  affected_systems="The auth service and all downstream API consumers"
)
```

This leverages the finding that tool calling is 50% more robust than JSON mode, and that `strict: true` gives 99%+ schema adherence.

### 9.3 Design Principles (Derived from Research)

| # | Principle | Source |
|---|---|---|
| 1 | **Show only the current frontier** — not the whole graph | Anthropic context engineering, SWE-agent 100-line windows |
| 2 | **Use natural language for prompts, structured calls for responses** | "Let Me Speak Freely" two-step pattern |
| 3 | **Include a reasoning slot for judgment-heavy nodes** | Instructor library (+60% accuracy from chain-of-thought field) |
| 4 | **Name slots as if they were the entire prompt** | Instructor library (4.5% → 95% from field naming alone) |
| 5 | **Provide informative feedback after each response** | SWE-agent Principle 3 |
| 6 | **Cap output length aggressively** | SWE-agent 50-hit cap, progressive disclosure pattern |
| 7 | **Collapse completed nodes to outcomes** | SWE-agent history compression (5 recent, rest collapsed) |
| 8 | **Validate immediately, reject invalid responses** | SWE-agent linting guardrail (-3pp without it) |
| 9 | **One action per step** | SWE-agent atomic {thought, command} pairs |
| 10 | **Make empty/error states explicit** | SWE-agent "command ran successfully with no output" |

---

## 10. Sources

### Papers
- Tam et al., "Let Me Speak Freely?" (EMNLP Industry 2024) — [arXiv:2408.02442](https://arxiv.org/abs/2408.02442)
- Yang et al., "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering" (NeurIPS 2024) — [arXiv:2405.15793](https://arxiv.org/abs/2405.15793)
- "CRANE: Reasoning with constrained LLM generation" (ICLR 2025) — [arXiv:2502.09061](https://arxiv.org/abs/2502.09061)
- "JSONSchemaBench" (Jan 2025) — [arXiv:2501.10868](https://arxiv.org/abs/2501.10868)
- "Grammar-Aligned Decoding" (NeurIPS 2024)
- "The Complexity Trap" (NeurIPS DL4Code Workshop 2025) — [arXiv:2508.21433](https://arxiv.org/abs/2508.21433)
- "StructEval" (TMLR 2025) — [arXiv:2505.20139](https://arxiv.org/abs/2505.20139)
- "Tokenomics" (Jan 2026) — [arXiv:2601.14470](https://arxiv.org/abs/2601.14470)
- "Difficulty-Aware Agent Orchestration" (Sep 2025) — [arXiv:2509.11079](https://arxiv.org/abs/2509.11079)
- "CoALA: Cognitive Architectures for Language Agents" — [arXiv:2309.02427](https://arxiv.org/abs/2309.02427)
- DSPy (Stanford NLP, ICLR 2024) — [dspy.ai](https://dspy.ai/)

### Workflow Engines & EBR
- [Temporal Workers Documentation](https://docs.temporal.io/workers)
- [Temporal Activity Definition](https://docs.temporal.io/activity-definition)
- [Airflow Tasks Documentation](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/tasks.html)
- [Prefect Runtime Context](https://docs.prefect.io/v3/develop/runtime-context)
- [Siemens Opcenter Execution Pharma (EBR)](https://plm.sw.siemens.com/en-US/opcenter/execution/pharma/)
- [SimplerQMS: Electronic Batch Records](https://simplerqms.com/electronic-batch-records/)
- [Camunda User Tasks Documentation](https://docs.camunda.io/docs/components/modeler/bpmn/user-tasks/)
- [Flowable Form Introduction](https://www.flowable.com/open-source/docs/form/ch06-Form-Introduction)

### Declarative Forms & Schema
- [RJSF Documentation](https://rjsf-team.github.io/react-jsonschema-form/docs/)
- [SurveyJS Architecture Guide](https://surveyjs.io/documentation/surveyjs-architecture)
- [Formio JSON Schema Wiki](https://github.com/formio/formio.js/wiki/Form-JSON-Schema)
- [PromptLayer: JSON Schema for Structured Outputs](https://blog.promptlayer.com/how-json-schema-works-for-structured-outputs-and-tool-integration/)
- [Opper: Schema Based Prompting](https://opper.ai/blog/schema-based-prompting)

### Conversational AI / Slot-Filling
- [Rasa Forms Documentation](https://legacy-docs-oss.rasa.com/docs/rasa/forms/)
- [Rasa Learning Center: Custom Forms](https://learning.rasa.com/archive/conversational-ai-with-rasa/custom-forms/)

### Agentic UX
- [CrewAI Tasks Documentation](https://docs.crewai.com/en/concepts/tasks)
- [n8n AI Agent Integrations](https://n8n.io/integrations/agent/)
- [Agentic UX & Design Patterns (Calibre Labs)](https://blog.calibrelabs.ai/p/agentic-ux-and-design-patterns)
- [The Agentic Era of UX (UX Collective)](https://uxdesign.cc/the-agentic-era-of-ux-4b58634e410b)
- [AI Agents in Production: What Actually Works in 2026](https://47billion.com/blog/ai-agents-in-production-frameworks-protocols-and-what-actually-works-in-2026/)

### Industry / Blog Posts (Agent Interfaces)
- [Anthropic: Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [SWE-agent ACI documentation](https://github.com/SWE-agent/SWE-agent/blob/main/docs/background/aci.md)
- [Instructor: Bad Schemas Could Break Your LLM Structured Outputs](https://python.useinstructor.com/blog/2024/09/26/bad-schemas-could-break-your-llm-structured-outputs/)
- [ImprovingAgents: Which Nested Data Format Do LLMs Understand Best?](https://www.improvingagents.com/blog/best-nested-data-format/)
- [ImprovingAgents: Which Table Format Do LLMs Understand Best?](https://www.improvingagents.com/blog/best-input-data-format-for-llms/)
- [SynapticLabs: The Meta-Tool Pattern](https://blog.synapticlabs.ai/bounded-context-packs-meta-tool-pattern)
- [Letta: Context Engineering](https://docs.letta.com/guides/agents/context-engineering)
- [Will Larson: Building an Internal Agent — Progressive Disclosure](https://lethain.com/agents-large-files/)
- [JetBrains: Cutting Through the Noise](https://blog.jetbrains.com/research/2025/12/efficient-context-management/)
- [Kiro: Spec-Driven Development](https://kiro.dev/blog/kiro-and-the-future-of-software-development/)
- [Martin Fowler: Spec-Driven Development Tools](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)
- [Google: Architecting Efficient Context-Aware Multi-Agent Framework](https://developers.googleblog.com/architecting-efficient-context-aware-multi-agent-framework-for-production/)
- [Aider: Building a Better Repository Map](https://aider.chat/2023/10/22/repomap.html)
