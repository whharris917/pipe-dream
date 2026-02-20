# `qms interact` Command Design

## Concept

`qms interact DOC_ID` is the single entry point for working with incrementally-built documents. The bare command emits status and guidance. Flags perform actions. Every invocation is stateless — the document tracks its own cursor, progress, and response history.

AI agents use this in a simple loop: call `interact` to see what's needed, call `interact --respond` to provide it, repeat.

## Bare Command (The "Poke")

```
$ qms --user claude interact CR-090-VR-001

CR-090-VR-001 | VR | IN_EXECUTION
Progress: 5/13 prompts filled
Cursor: pre_conditions

--- Prompt: pre_conditions ---

Describe the state of the system BEFORE verification begins. A person
with terminal access but no knowledge of this project must be able to
reproduce these conditions.

Include as applicable: branch and commit checked out, services running
(which, what ports), container state, non-default configuration, data
state, relevant environment details (OS, Python version, etc.).

--- Actions ---
  --respond "value"                      Respond to current prompt
  --respond --file path                  Respond with file contents
  --accept                               Accept default value (when available)
  --progress                             Show all prompts and fill status
  --goto <prompt_id>                     Move cursor to amend a previous response
  --reopen <loop_name> --reason "why"    Re-enter a closed loop
  --compile                              Generate compiled document
```

The output gives the agent everything it needs in one call:
- Where it is (cursor position, progress)
- What to do (the prompt guidance)
- How to do it (the available flag commands)

## Flags

### --respond "value"

Respond to the current prompt. Cursor auto-advances to the next prompt per the state machine.

```
$ qms --user claude interact CR-090-VR-001 --respond "Verify that service health monitoring detects running and stopped services"

Recorded: objective
Cursor advanced: objective → expected_outcome
```

For gates (yes/no flow-control prompts):

```
$ qms --user claude interact CR-090-VR-001 --respond yes

Gate: more_steps → yes
Loop: steps continuing (iteration 3)
Cursor advanced: more_steps → step_action
```

### --respond --file path

Respond with file contents. Essential for pasting terminal output, log excerpts, or any multi-line content.

```
$ qms --user claude interact CR-090-VR-001 --respond --file /tmp/health-check-output.txt

Recorded: step_observed (Step 2)
Cursor advanced: step_observed → more_steps
```

### --accept

Accept the default value for prompts that have one (e.g., `default: today`, `default: current_user`). Errors if no default exists.

```
$ qms --user claude interact CR-090-VR-001 --accept

Recorded: date = 2026-02-20 (default: today)
Cursor advanced: date → objective
```

### --progress

Show fill status of all prompts. Filled prompts show a truncated value. The current cursor position is marked.

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
```

### --goto prompt_id

Move cursor to a previously-completed prompt for amendment. The next `--respond` will append an amendment (not replace the original). After responding, cursor returns to where it was.

```
$ qms --user claude interact CR-090-VR-001 --goto objective

Cursor moved: positive_verification → objective (detour)
Return position saved: positive_verification

--- Prompt: objective (AMENDMENT) ---

Current value (2026-02-20 10:30, claude):
  Verify that the health check endpoint returns 200

Provide amended value, or call --respond to submit:
  --respond "new value" --reason "why"

$ qms --user claude interact CR-090-VR-001 \
    --respond "Verify that service health monitoring detects running and stopped services" \
    --reason "Broadened scope per VR evidence standards"

Amended: objective
  1. ~~Verify that the health check endpoint returns 200~~ — claude, 2026-02-20 10:30
  2. Verify that service health monitoring detects running and stopped services — claude, 2026-02-20 10:35 | Amended: Broadened scope per VR evidence standards
Cursor returned: objective → positive_verification
```

### --reopen loop_name --reason "why"

Re-enter a closed loop. Iteration counter continues. After the loop's gate closes again, cursor returns to where it was.

```
$ qms --user claude interact CR-090-VR-001 --reopen steps --reason "Additional scenario: verify behavior with invalid port"

Loop reopened: steps (was 2 iterations, resuming at 3)
Cursor moved: overall_outcome → step_action (detour)
Return position saved: overall_outcome

--- Prompt: step_action (Step 3) ---

What action are you performing in this step?
```

### --compile

Generate the compiled document. Can be called at any point — partial compilation is allowed (unfilled placeholders render as blanks or markers).

```
$ qms --user claude interact CR-090-VR-001 --compile

Compiled to: .claude/users/claude/workspace/CR-090-VR-001.md
Prompts filled: 18/18
Amendments: 1 (objective)
Loop reopenings: 1 (steps, +1 iteration)
```

## Typical Agent Session

An AI agent filling in a VR looks like this:

```
# Orient
qms --user claude interact CR-090-VR-001

# Identification
qms --user claude interact CR-090-VR-001 --respond "CR-090"
qms --user claude interact CR-090-VR-001 --respond "EI-3"
qms --user claude interact CR-090-VR-001 --accept                # date = today

# Objective
qms --user claude interact CR-090-VR-001 --respond "Verify that service health monitoring detects running and stopped services correctly"

# Pre-conditions
qms --user claude interact CR-090-VR-001 --respond --file /tmp/preconditions.txt

# Step 1: action → expected → detail → observed → outcome
qms --user claude interact CR-090-VR-001 --respond "Run health check against running MCP service"
qms --user claude interact CR-090-VR-001 --respond "TCP connect succeeds, service reported as alive"
qms --user claude interact CR-090-VR-001 --respond --file /tmp/step1-cmd.txt
qms --user claude interact CR-090-VR-001 --respond --file /tmp/step1-output.txt
qms --user claude interact CR-090-VR-001 --respond "Pass"
qms --user claude interact CR-090-VR-001 --respond yes           # more steps

# Step 2: action → expected → detail → observed → outcome
qms --user claude interact CR-090-VR-001 --respond "Stop MCP server and re-check"
qms --user claude interact CR-090-VR-001 --respond "TCP connect fails, service reported as down"
qms --user claude interact CR-090-VR-001 --respond --file /tmp/step2-cmd.txt
qms --user claude interact CR-090-VR-001 --respond --file /tmp/step2-output.txt
qms --user claude interact CR-090-VR-001 --respond "Pass"
qms --user claude interact CR-090-VR-001 --respond no            # no more steps

# Summary
qms --user claude interact CR-090-VR-001 --respond "Pass"
qms --user claude interact CR-090-VR-001 --respond --file /tmp/summary.txt

# Signature
qms --user claude interact CR-090-VR-001 --accept                # performer = current_user
qms --user claude interact CR-090-VR-001 --accept                # date = today

# Compile
qms --user claude interact CR-090-VR-001 --compile
```

That's 23 commands for a complete 2-step VR. Each step is a
self-contained unit: what I'm doing, what I expect, exactly how,
what I saw, did it match. The summary rolls it up.
