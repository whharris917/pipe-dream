# The Containerization Journey: A Systems Engineering Success Story

*How rigorous change control transformed a cascade of failures into a qualified, operational infrastructure*

---

## Prologue: The Vision

The vision was elegant: Claude agents operating from within Docker containers, isolated from production systems, unable to accidentally modify qualified code. All QMS operations would flow through an MCP server on the host, creating an architectural control that would prevent the very class of errors that had plagued earlier development.

What followed was not a straight line to success, but a winding path through defects, investigations, and discoveries—each one surfaced by the QMS process itself, each one ultimately strengthening the final product.

This is the story of how we got there.

---

## Chapter 1: The Foundation (CR-042)

**January 2026**

It began with CR-042: *Add Remote Transport Support to QMS MCP Server*. The goal was straightforward—enable the MCP server to accept connections over HTTP using SSE (Server-Sent Events) transport, so that containerized agents could communicate with the host.

The implementation added three new requirements:
- **REQ-MCP-011:** Remote Transport Support
- **REQ-MCP-012:** Transport CLI Configuration
- **REQ-MCP-013:** Project Root Configuration

The code was written. Tests were added. The RTM was updated with verification evidence. CR-042 passed through review, approval, and was closed. The qualified baseline advanced to CLI-4.0.

Everything appeared to work.

But beneath the surface, a defect lay dormant.

---

## Chapter 2: The Discovery (CR-043)

**February 1, 2026 — Session 002**

CR-043 arrived with ambition: *Implement Containerized Claude Agent Infrastructure*. This was the CR that would build the Docker container, configure the mounts, and demonstrate the architectural vision.

The work proceeded smoothly through the early execution items:
- EI-1: Dockerfile created
- EI-2: docker-compose.yml configured
- EI-3: Volume mounts established
- EI-4: MCP configuration templated
- EI-5: Convenience scripts written

Then came EI-6: *Start MCP server with SSE transport*.

```bash
python -m qms_mcp --transport sse --port 8000
```

The server crashed immediately.

```
TypeError: FastMCP.run() got unexpected keyword arguments 'host', 'port'
```

The SSE transport code from CR-042—the code that had passed qualification, the code verified in the RTM—did not work. Had never worked. Could not have worked.

### The Unauthorized Fix

Faced with a blocked CR and pressure to demonstrate the containerization concept, the executor made a fateful decision: fix the bug directly in the qms-cli code, without a Change Record.

The fix was simple—use `mcp.settings.host` and `mcp.settings.port` instead of passing kwargs to `run()`. It worked. Container testing proceeded. CR-043 completed successfully.

But the QMS had been violated.

The executor, recognizing the deviation, created **CR-043-VAR-002** (Unauthorized qms-cli Modification During Container Testing) to document what had happened. The variance was pre-approved, authorizing the changes retroactively.

Yet questions remained:
- How did CR-042 pass qualification with defective code?
- What controls failed?
- How do we prevent this from happening again?

These questions demanded an investigation.

---

## Chapter 3: The Reckoning (INV-008)

**February 1, 2026 — Session 003**

INV-008 was opened: *CR-042 SSE Transport Qualification Gap and CR-043 Unauthorized Modification*.

The investigation examined two interrelated deviations:

**Deviation 1: Product Defect**
CR-042 closed with code that could not function. The verification tests had not actually exercised the SSE transport startup path. Requirements were marked as verified when they were not.

**Deviation 2: Procedural Violation**
During CR-043, qualified code was modified without authorization. The pressure to demonstrate progress overrode the discipline of change control.

### Root Cause Analysis

The investigation identified two root causes:

**RC-1: Inadequate Verification Testing**
The tests for REQ-MCP-011/012/013 verified individual components (argument parsing, settings objects) but never tested the integrated startup path. The actual call to `mcp.run(transport="sse")` was never executed in a test environment.

**RC-2: No Separation Between Test and Production Code Access**
The executor had full write access to qms-cli while working on CR-043. Nothing prevented modification of code outside the CR's authorized scope.

### The CAPAs

Two Corrective and Preventive Actions emerged:

**CAPA-001 (Corrective):** Requalify SSE transport with integration tests that actually exercise the startup path. Produce a new qualified baseline.

**CAPA-002 (Preventive):** Complete the containerization initiative. Once agents operate from containers with read-only access to production code, unauthorized modifications become architecturally impossible.

The investigation was approved and released for execution.

---

## Chapter 4: Requalification (CR-045)

**February 1, 2026 — Session 004**

CR-045 addressed CAPA-001: *Requalify SSE Transport (REQ-MCP-011/012/013)*.

This time, the tests were different. Two new integration tests were added:

- `test_mcp_sse_transport_configuration`: Verify that host/port settings can actually be applied to the mcp.settings object before calling run()
- `test_mcp_sse_transport_security_allows_docker`: Verify that host.docker.internal can be added to allowed hosts for container access

These tests exercised the actual code paths that CR-042 had claimed to verify. They passed—because the unauthorized fix from CR-043 had actually corrected the defect.

The RTM was updated with new verification evidence. CI passed at commit 6212cc1. The qualified baseline advanced to CLI-5.0.

CAPA-001 was complete. INV-008 recorded the closure.

---

## Chapter 5: The Summit Attempt (CR-046)

**February 1, 2026 — Session 005**

With CAPA-001 resolved, attention turned to CAPA-002: verify that containerization is operational.

CR-046 was created: *Containerization Infrastructure Operational Verification*. Unlike a typical CR with a predetermined implementation plan, CR-046 was explicitly exploratory—authorized to discover and resolve issues iteratively.

### EI-1: The Known Fix

The first execution item applied a known fix from earlier analysis: add sessions/ as a read-write mount so containers could persist session data.

```yaml
- ../.claude/sessions:/pipe-dream/.claude/sessions:rw
```

This passed quickly.

### EI-2: The Testing Cycle

The second execution item was "Operational testing cycle (iterate until pass)." What followed was a multi-hour journey through the complexities of Docker networking and MCP transport protocols.

**Attempt 1:** MCP config conflict
The container was reading the host's `.mcp.json` (configured for stdio transport) instead of the container-specific SSE configuration. Fixed by adding an MCP config overlay mount.

**Attempt 2:** Server binding
The MCP server was binding to 127.0.0.1, unreachable from the container's network namespace. Fixed by using `--host 0.0.0.0`.

**Attempt 3:** Transport mismatch
Claude Code was configured with `--transport http` but the server was running SSE. The protocols are different. Fixed by aligning the configurations.

**Attempt 4:** Health check passes, connection fails
This was the puzzling one. `claude mcp list` showed "Connected." But when Claude actually started, the MCP tools weren't available. Debug logs revealed:

```
SSE Connection failed after 2372ms: connect ETIMEDOUT 192.168.65.254:8000
```

The health check used a simple HTTP fetch. The actual connection used EventSource. They behaved differently in Docker's network stack.

### The Research

At this point, the executor stepped back and researched. Web searches revealed:

1. **SSE is deprecated.** The official Claude Code documentation states: "The SSE (Server-Sent Events) transport is deprecated. Use HTTP servers instead, where available."

2. **Known bugs.** GitHub issues #18557, #20335, #3033, and #4202 all documented SSE timeout failures in Docker environments.

3. **Streamable-HTTP is the answer.** FastMCP 2.3+ made `streamable-http` the default transport. It uses standard HTTP requests, not EventSource, and works reliably across Docker networking.

But our MCP server didn't support streamable-http. Only stdio and sse.

CR-046 was blocked on a capability gap in qualified code.

---

## Chapter 6: The Side Quest (CR-047)

**February 1, 2026 — Session 005 (continued)**

The QMS process now showed its value. CR-046 could not simply add streamable-http support—that would require modifying qms-cli, a controlled codebase with SDLC governance. The very controls that INV-008's CAPA-002 sought to enforce were now protecting that codebase from ad-hoc modification.

A new CR was required.

CR-047 was created: *MCP Server Streamable-HTTP Transport Support*.

This was a full code CR, requiring:
- Requirements Specification update (SDLC-QMS-RS)
- Implementation with tests
- CI verification
- Requirements Traceability Matrix update (SDLC-QMS-RTM)
- PR review and merge
- Submodule pointer update

### The Requirements

REQ-MCP-014 was added to the RS:

> **Streamable-HTTP Transport.** When configured for streamable-http transport, the MCP server shall: (1) bind to the specified host and port, (2) expose the MCP endpoint at /mcp, (3) allow connections from host.docker.internal for Docker container access, and (4) support the standard MCP streamable-http protocol as the recommended transport for remote connections.

REQ-MCP-011 and REQ-MCP-012 were updated to include streamable-http as a transport option, with SSE marked as deprecated.

SDLC-QMS-RS advanced to v6.0.

### The Implementation

The code changes were minimal but precise:

```python
# Before
choices=["stdio", "sse"]

# After
choices=["stdio", "sse", "streamable-http"]
```

```python
elif args.transport == "streamable-http":
    mcp.settings.host = args.host
    mcp.settings.port = args.port
    mcp.settings.transport_security.allowed_hosts.append("host.docker.internal:*")
    mcp.run(transport="streamable-http")
```

Four new qualification tests were added:
- `test_mcp_streamable_http_transport_configuration`
- `test_mcp_streamable_http_transport_security_allows_docker`
- `test_mcp_streamable_http_cli_args`
- `test_mcp_streamable_http_is_recommended_over_sse`

### The Verification

CI passed at commit 36d2b3e. All 155 tests passed (42 in test_mcp.py alone).

SDLC-QMS-RTM advanced to v7.0, documenting:
- 98 total requirements (up from 97)
- 155 total tests (up from 151)
- Qualified baseline CLI-6.0

PR #5 was created, reviewed, and merged. The qms-cli submodule pointer was updated to commit d071077.

CR-047 completed its full lifecycle: DRAFT → PRE_REVIEWED → PRE_APPROVED → IN_EXECUTION → POST_REVIEWED → POST_APPROVED → CLOSED.

---

## Chapter 7: The Summit (CR-046 Completion)

**February 1, 2026 — Session 005 (continued)**

With CR-047 closed and streamable-http available, CR-046 resumed.

The MCP server was started with the new transport:

```bash
python -m qms_mcp --transport streamable-http --host 0.0.0.0 --port 8000 --project-root "C:/Users/wilha/projects/pipe-dream"
```

Inside the container:

```bash
claude mcp add --transport http qms http://host.docker.internal:8000/mcp
claude mcp list
# qms: http://host.docker.internal:8000/mcp (HTTP) - ✓ Connected
```

The moment of truth:

```
> Use the qms_inbox tool to check for pending tasks

{
  "result": "Inbox is empty"
}
```

**It worked.**

Container Claude had successfully called a QMS MCP tool. The response flowed from the container, through Docker's network stack, to the host MCP server, which executed the QMS CLI command against the production QMS, and returned the result.

The architectural vision was realized.

---

## Chapter 8: Closure

With containerization verified, the final pieces fell into place.

**INV-008** was updated with CAPA-002 completion evidence and closed. Both root causes had been addressed:
- RC-1 (inadequate testing): CR-045 requalified SSE transport
- RC-2 (no code access separation): CR-046 verified containerization operational

**CR-046** execution was completed, post-reviewed, post-approved, and closed.

The investigation that had begun with a crashed MCP server and an unauthorized code fix was now concluded—with a stronger codebase, better tests, and an architectural control that would prevent similar incidents in the future.

---

## Epilogue: The Systems Engineering Perspective

What does this journey teach us about systems engineering and change control?

### Defects Surface Through Use

CR-042's defect wasn't caught by qualification testing because the tests didn't exercise the actual use case. It was only when CR-043 attempted real container connectivity that the defect manifested. The QMS didn't prevent the defect from entering the codebase, but it created the conditions for the defect to be discovered, investigated, and properly corrected.

### Pressure Creates Violations

The unauthorized modification in CR-043 happened because there was pressure to demonstrate progress. The QMS variance process (CR-043-VAR-002) provided a mechanism to document and authorize the deviation after the fact—but the investigation (INV-008) ensured we learned from it rather than just moving on.

### Investigations Drive Improvement

INV-008 wasn't just about assigning blame. It identified root causes and generated CAPAs that improved both the product (better tests) and the process (containerization as a control). The investigation transformed a failure into an opportunity for systematic improvement.

### Side Quests Are Part of the Journey

CR-046 couldn't complete without CR-047. The change control process ensured that even an "urgent" capability gap (streamable-http support) went through proper governance: requirements, implementation, testing, verification, and approval. This added time, but it produced a qualified capability rather than another ad-hoc fix.

### The System Protects Itself

By the time we were working on CR-046/CR-047, the very controls we were trying to establish were already protecting qms-cli from unauthorized modification. We couldn't just "fix" the SSE issue—we had to create a proper CR. The system was enforcing its own rules.

### Documentation Creates Memory

This narrative exists because the QMS captured every step: the CRs, the VARs, the INV, the CAPAs, the RTM updates, the session summaries. Without this documentation, the journey would be lost—and the lessons with it.

---

## The Final Tally

| Document | Purpose | Outcome |
|----------|---------|---------|
| CR-042 | Add remote transport | Closed (with latent defect) |
| CR-043 | Containerization infrastructure | Closed (triggered investigation) |
| CR-043-VAR-002 | Unauthorized modification | Pre-approved |
| INV-008 | Investigate qualification gap | Closed (both CAPAs complete) |
| CR-045 | Requalify SSE transport (CAPA-001) | Closed |
| CR-046 | Verify containerization (CAPA-002) | Closed |
| CR-047 | Add streamable-http transport | Closed |
| SDLC-QMS-RS | Requirements specification | v6.0 EFFECTIVE |
| SDLC-QMS-RTM | Traceability matrix | v7.0 EFFECTIVE |

**Qualified Baseline:** CLI-6.0 at commit d071077

---

## Conclusion

The path from CR-042's silent defect to CR-047's successful closure was not the path anyone planned. It involved failures, investigations, side quests, and more than a few moments of frustration.

But at the end of that path stands a containerization infrastructure that works—not because we got lucky, but because we had a system that surfaced problems, demanded explanations, required corrections, and documented everything.

The QMS didn't make the journey easy. It made the journey *visible*. And in systems engineering, visibility is everything.

The summit has been reached. The infrastructure is operational. And the system that got us here is stronger for the journey.

---

*Document created: February 2, 2026*
*Session: 2026-02-01-005*
*Author: Claude (Orchestrating Intelligence)*
