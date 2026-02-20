# `qms interact` Command Design

## Concept

`qms interact DOC_ID` is the single entry point for working with incrementally-built documents. The bare command emits status and guidance. Flags perform actions. Every invocation is stateless — the document tracks its own cursor, progress, and response history.

**Prompt-before-response rule:** The system will not accept a response to a prompt it has not presented. Each `--respond` output includes the next prompt inline, creating a forced dialogue. The agent reads the prompt as part of the previous command's output, then responds.

**Persistent help footer:** Every output ends with a reminder of available commands. The agent never needs to recall syntax from memory.

## Bare Command (The "Poke")

```
$ qms --user claude interact CR-090-VR-001

CR-090-VR-001 | VR | IN_EXECUTION
Progress: 5/18 prompts filled
Cursor: pre_conditions

--- Prompt: pre_conditions ---

Describe the state of the system BEFORE verification begins. A person
with terminal access but no knowledge of this project must be able to
reproduce these conditions.

Include as applicable: branch and commit checked out, services running
(which, what ports), container state, non-default configuration, data
state, relevant environment details (OS, Python version, etc.).

---
To respond:   qms --user claude interact CR-090-VR-001 --respond "value"
From file:    qms --user claude interact CR-090-VR-001 --respond --file path
To amend:     --goto <prompt_id>
To add steps: --reopen <loop_name> --reason "why"
Other:        --progress | --compile
```

## Flags

### --respond "value"

Respond to the current prompt. Records the response, advances the cursor, and **presents the next prompt** in the same output.

```
$ qms --user claude interact CR-090-VR-001 --respond "CR-090"

Recorded: parent_doc_id = CR-090
  — claude, 2026-02-20 10:30

--- Prompt: related_eis ---

Which execution item(s) in the parent document does this VR
verify? (e.g., EI-3, or EI-3 and EI-4)

---
To respond:   qms --user claude interact CR-090-VR-001 --respond "value"
From file:    qms --user claude interact CR-090-VR-001 --respond --file path
To amend:     --goto <prompt_id>
To add steps: --reopen <loop_name> --reason "why"
Other:        --progress | --compile
```

For gates (yes/no flow-control prompts):

```
$ qms --user claude interact CR-090-VR-001 --respond yes

Gate: more_steps → yes
Loop: steps continuing (iteration 2)

--- Prompt: step_action (Step 2) ---

What action are you about to perform?

---
To respond:   qms --user claude interact CR-090-VR-001 --respond "value"
From file:    qms --user claude interact CR-090-VR-001 --respond --file path
To amend:     --goto <prompt_id>
To add steps: --reopen <loop_name> --reason "why"
Other:        --progress | --compile
```

For prompts with contextual interpolation (the prompt references a previous response):

```
$ qms --user claude interact CR-090-VR-001 --respond "Stop MCP server and re-check health status"

Recorded: step_action (Step 2) = Stop MCP server and re-check health status
  — claude, 2026-02-20 10:38

--- Prompt: step_expected (Step 2) ---

You said you're about to: "Stop MCP server and re-check health status"

Before you execute — what do you expect to observe?

---
To respond:   qms --user claude interact CR-090-VR-001 --respond "value"
From file:    qms --user claude interact CR-090-VR-001 --respond --file path
To amend:     --goto <prompt_id>
To add steps: --reopen <loop_name> --reason "why"
Other:        --progress | --compile
```

### --respond --file path

Respond with file contents. For terminal output, log excerpts, or multi-line content.

```
$ qms --user claude interact CR-090-VR-001 --respond --file /tmp/step1-output.txt

Recorded: step_observed (Step 1) [from file: /tmp/step1-output.txt, 14 lines]
  — claude, 2026-02-20 10:35

--- Prompt: step_outcome (Step 1) ---

Did the observed output match your expected outcome? State Pass or
Fail. If Fail, briefly note the discrepancy.

---
To respond:   qms --user claude interact CR-090-VR-001 --respond "value"
From file:    qms --user claude interact CR-090-VR-001 --respond --file path
To amend:     --goto <prompt_id>
To add steps: --reopen <loop_name> --reason "why"
Other:        --progress | --compile
```

### --accept

Accept the default value for prompts that have one (e.g., `default: today`, `default: current_user`). Errors if no default exists for the current prompt.

```
$ qms --user claude interact CR-090-VR-001 --accept

Recorded: date = 2026-02-20 (default: today)
  — claude, 2026-02-20 10:31

--- Prompt: objective ---

State what CAPABILITY is being verified — not what specific mechanism
is being tested. Frame the objective broadly enough that you naturally
check adjacent behavior during the procedure.

Good: "Verify that service health monitoring detects running and
       stopped services correctly"
Avoid: "Verify the health check endpoint returns 200"

---
To respond:   qms --user claude interact CR-090-VR-001 --respond "value"
From file:    qms --user claude interact CR-090-VR-001 --respond --file path
To amend:     --goto <prompt_id>
To add steps: --reopen <loop_name> --reason "why"
Other:        --progress | --compile
```

### --progress

Show fill status of all prompts. Includes the help footer.

```
$ qms --user claude interact CR-090-VR-001 --progress

CR-090-VR-001 | VR | IN_EXECUTION | 14/18

  [x] parent_doc_id     CR-090
  [x] related_eis        EI-3
  [x] date               2026-02-20
  [x] objective          Verify that service health monitoring...
  [x] pre_conditions     Branch: main @ c1477f8. Services: QMS...
      --- loop: steps (2 iterations, closed) ---
      Step 1:
  [x]   step_action.1    Run health check against running service
  [x]   step_expected.1  TCP connect succeeds, service reported...
  [x]   step_detail.1    python -c "import socket; s = socket...
  [x]   step_observed.1  Connection to localhost:8000 succeeded...
  [x]   step_outcome.1   Pass
      Step 2:
  [x]   step_action.2    Stop MCP server and re-check
  [x]   step_expected.2  TCP connect fails, service reported as...
  [x]   step_detail.2    docker-compose stop qms-mcp && python...
  [x]   step_observed.2  Connection to localhost:8000 refused...
  [x]   step_outcome.2   Pass
      --- end loop ---
> [ ] summary_outcome    (current)
  [ ] summary_narrative
  [ ] performer
  [ ] performed_date

---
To respond:   qms --user claude interact CR-090-VR-001 --respond "value"
From file:    qms --user claude interact CR-090-VR-001 --respond --file path
To amend:     --goto <prompt_id>
To add steps: --reopen steps --reason "why"
Other:        --compile
```

### --goto prompt_id

Move cursor to a previously-completed prompt for amendment. Presents the current value and amendment prompt. After the amendment `--respond`, cursor returns to where it was and presents the prompt that was pending.

```
$ qms --user claude interact CR-090-VR-001 --goto objective

Cursor detour: summary_outcome → objective
Return position saved: summary_outcome

--- Prompt: objective (AMENDMENT) ---

Current value:
  "Verify that the health check endpoint returns 200"
  — claude, 2026-02-20 10:31

Provide an amended response with --reason explaining the change.

---
To amend:     qms --user claude interact CR-090-VR-001 --respond "new value" --reason "why"
To cancel:    qms --user claude interact CR-090-VR-001 --cancel-goto
Other:        --progress | --compile

$ qms --user claude interact CR-090-VR-001 \
    --respond "Verify that service health monitoring detects running and stopped services" \
    --reason "Broadened scope per VR evidence standards"

Amended: objective
  1. ~~Verify that the health check endpoint returns 200~~
     — claude, 2026-02-20 10:31
  2. Verify that service health monitoring detects running and stopped services
     — claude, 2026-02-20 11:15 | Amended: Broadened scope per VR evidence standards

Cursor returned: objective → summary_outcome

--- Prompt: summary_outcome ---

Considering all steps above, what is the overall outcome? Pass if
all steps passed and no side effects were observed. Fail if any step
failed or unexpected side effects occurred.

---
To respond:   qms --user claude interact CR-090-VR-001 --respond "value"
From file:    qms --user claude interact CR-090-VR-001 --respond --file path
To amend:     --goto <prompt_id>
To add steps: --reopen steps --reason "why"
Other:        --progress | --compile
```

### --reopen loop_name --reason "why"

Re-enter a closed loop. Presents the first prompt of the new iteration. After the loop's gate re-closes, cursor returns and presents the prompt that was pending.

```
$ qms --user claude interact CR-090-VR-001 \
    --reopen steps --reason "Additional scenario: verify behavior with invalid port"

Loop reopened: steps (was 2 iterations, resuming at 3)
Cursor detour: summary_outcome → step_action (Step 3)
Return position saved: summary_outcome

--- Prompt: step_action (Step 3) ---

What action are you about to perform?

---
To respond:   qms --user claude interact CR-090-VR-001 --respond "value"
From file:    qms --user claude interact CR-090-VR-001 --respond --file path
To amend:     --goto <prompt_id>
Other:        --progress | --compile
```

### --compile

Generate the compiled document.

```
$ qms --user claude interact CR-090-VR-001 --compile

Compiled to: .claude/users/claude/workspace/CR-090-VR-001.md
Prompts filled: 18/18
Amendments: 1 (objective)
Loop reopenings: 1 (steps, +1 iteration)
```

### --cancel-goto

Cancel a `--goto` detour without amending. Returns cursor to saved position.

## Enforcement Rules

1. **Prompt-before-response:** `--respond` is rejected if the current prompt has not been presented in a prior `interact` output. Error message re-presents the prompt.
2. **Sequential only:** There is no flag to skip a prompt or jump ahead. Forward progress requires responding to each prompt in order.
3. **Amendments require reason:** `--respond` during a `--goto` detour requires `--reason`. Rejected without it.
4. **Reopens require reason:** `--reopen` requires `--reason`. Rejected without it.

## Typical Agent Session

```
# Orient — presents first prompt
qms --user claude interact CR-090-VR-001

# Each --respond records answer AND presents next prompt
qms --user claude interact CR-090-VR-001 --respond "CR-090"
qms --user claude interact CR-090-VR-001 --respond "EI-3"
qms --user claude interact CR-090-VR-001 --accept
qms --user claude interact CR-090-VR-001 --respond "Verify that service health monitoring detects running and stopped services correctly"
qms --user claude interact CR-090-VR-001 --respond --file /tmp/preconditions.txt

# Step 1 — each respond shows next prompt; agent reads before answering
qms --user claude interact CR-090-VR-001 --respond "Run health check against running MCP service"
qms --user claude interact CR-090-VR-001 --respond "TCP connect succeeds, service reported as alive"
qms --user claude interact CR-090-VR-001 --respond --file /tmp/step1-cmd.txt
qms --user claude interact CR-090-VR-001 --respond --file /tmp/step1-output.txt
qms --user claude interact CR-090-VR-001 --respond "Pass"
qms --user claude interact CR-090-VR-001 --respond yes

# Step 2
qms --user claude interact CR-090-VR-001 --respond "Stop MCP server and re-check"
qms --user claude interact CR-090-VR-001 --respond "TCP connect fails, service reported as down"
qms --user claude interact CR-090-VR-001 --respond --file /tmp/step2-cmd.txt
qms --user claude interact CR-090-VR-001 --respond --file /tmp/step2-output.txt
qms --user claude interact CR-090-VR-001 --respond "Pass"
qms --user claude interact CR-090-VR-001 --respond no

# Summary
qms --user claude interact CR-090-VR-001 --respond "Pass"
qms --user claude interact CR-090-VR-001 --respond --file /tmp/summary.txt

# Signature
qms --user claude interact CR-090-VR-001 --accept
qms --user claude interact CR-090-VR-001 --accept

# Compile
qms --user claude interact CR-090-VR-001 --compile
```

24 commands for a 2-step VR (1 orient + 22 respond/accept + 1 compile).
Every --respond output contains the next prompt. The agent reads what
the system presents, then responds to it. No skipping forward. Help
footer on every output.

## Help Output

```
$ qms --user claude interact --help

Usage: qms --user USER interact DOC_ID [OPTIONS]

  Guided form-fill for incrementally-built documents. The bare command
  shows the current prompt. Each --respond records an answer and presents
  the next prompt. The document tracks its own progress — call bare at
  any time to re-orient.

Arguments:
  DOC_ID                     Document to interact with (must be IN_EXECUTION)

Responding:
  --respond VALUE            Respond to the current prompt
  --respond --file PATH      Respond with file contents (for multi-line output)
  --accept                   Accept default value for current prompt
  --reason TEXT              Required with --respond during amendments

Navigation:
  --goto PROMPT_ID           Amend a previous response (detour + return)
  --cancel-goto              Cancel an amendment detour without changes
  --reopen LOOP --reason WHY Re-enter a closed loop to add iterations

Status:
  --progress                 Show all prompts with fill status
  --compile                  Generate compiled document from responses

Rules:
  - A prompt must be presented before it can be responded to
  - Forward progress is sequential — no skipping prompts
  - Amendments append (original preserved with strikethrough)
  - All responses are timestamped with author identity

Examples:
  # Start or re-orient
  qms --user claude interact CR-090-VR-001

  # Respond to current prompt
  qms --user claude interact CR-090-VR-001 --respond "Pass"

  # Respond with terminal output from file
  qms --user claude interact CR-090-VR-001 --respond --file /tmp/output.txt

  # Accept a default (e.g., today's date)
  qms --user claude interact CR-090-VR-001 --accept

  # Amend a previous response
  qms --user claude interact CR-090-VR-001 --goto objective
  qms --user claude interact CR-090-VR-001 --respond "new value" --reason "why"

  # Add more steps to a closed loop
  qms --user claude interact CR-090-VR-001 --reopen steps --reason "why"

  # View progress
  qms --user claude interact CR-090-VR-001 --progress

  # Compile final document
  qms --user claude interact CR-090-VR-001 --compile
```
