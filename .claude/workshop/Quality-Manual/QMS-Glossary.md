# QMS Glossary

All major QMS-related terms used across the Quality Management System.

---

| Term | Definition |
|------|------------|
| **ADD (Addendum Report)** | Child document created to correct or supplement a closed executable document; must reference a CLOSED parent. |
| **Administrator** | User group with all Initiator permissions plus administrative commands (e.g., fix). |
| **Adoption CR** | A Change Record that brings a new system from Genesis Sandbox into Production. |
| **Approval Gate** | System block on approval routing if any reviewer submitted request-updates; initiator must address changes and re-route for review. |
| **Archive** | Historical version storage at `.archive/{TYPE}/`; superseded versions are copied here with version suffix. |
| **Audit Trail** | Append-only event log stored in `.audit/` JSONL files; records all document lifecycle events. |
| **CAPA (Corrective and Preventive Action)** | A category of execution item within an INV; not a standalone document. |
| **CLOSED** | Terminal state for executable documents indicating execution is complete with no further action possible. |
| **Context** | Information passed to a subagent about the work to be performed. |
| **Controlled Document** | Any document managed under the QMS. |
| **Corrective Action** | Action to eliminate the cause of an existing deviation and/or remediate the consequences of the deviation having occurred. |
| **CR (Change Record)** | The controlled document authorizing a change; follows executable document workflow. |
| **Deviation** | Departure from approved procedure or expected product behavior. |
| **Draft** | A version under development, not yet approved. |
| **EFFECTIVE** | Status indicating a non-executable document is approved and in force. |
| **Editable Field** | A field in the executable block where execution work is recorded (e.g., execution details, evidence). |
| **ER (Exception Report)** | Child document for test execution failures within Test Protocols or Test Cases. |
| **Evidence** | Documentation proving completion of an execution item. |
| **Executable Block** | Section of an executable document where implementation work is recorded; contains static and editable fields. |
| **Executable Document** | A document that authorizes implementation activities (CR, INV, TP, ER, VAR, ADD, VR). |
| **Execution Branch** | A git branch used during CR execution phase for implementing approved changes. |
| **Execution Item (EI)** | Discrete unit of work within the executable block; tracked in table format with task description, outcome, and signature. |
| **Frontmatter** | Minimal YAML header in documents containing author-maintained fields (title, revision_summary). |
| **Genesis Sandbox** | A development environment for foundational work on new systems, outside QMS governance; uses `genesis/` branch pattern. |
| **Inbox** | Per-user directory at `.claude/users/{username}/inbox/` containing task files for assigned reviews and approvals. |
| **Initiator** | User group that can create and manage documents through workflow. |
| **INV (Investigation)** | An executable document for analyzing deviations; contains root cause analysis and CAPAs. |
| **Merge Gate** | Prerequisites that must be met before code is merged to main: all tests pass (CI-verified), RS is EFFECTIVE, RTM is EFFECTIVE. |
| **Metadata** | Workflow state stored in `.meta/` sidecar JSON files; managed entirely by the QMS CLI. |
| **Non-Executable Document** | A document that defines requirements or specifications (RS, RTM, SOP). |
| **Orchestrator** | The primary agent that spawns and coordinates subagents. |
| **Preventive Action** | Action to eliminate the cause of a potential future deviation; continuous improvement of the QMS. |
| **Procedural Deviation** | A problem with a procedure as approved, or with the actual use of a procedure. |
| **Product Deviation** | A problem with the product itself (e.g., code bug, design flaw). |
| **QA (Quality Assurance Representative)** | Member of the Quality group; mandatory reviewer and approver; assigns TUs to review teams. |
| **Qualified Commit** | The git commit hash representing the code state under which a System Release was qualified; must be CI-verified. |
| **Qualified State** | A system with approved RS, verified RTM, and code at a documented commit. |
| **Qualitative Proof** | Verification requiring intelligent judgment, documented as prose with code references; one of three RTM verification types. |
| **Quality** | User group that assigns reviewers, reviews, and approves documents. |
| **Responsible User** | The user who has checked out a document and owns its workflow; persists through the revision cycle until approval. |
| **RETIRED** | Terminal state indicating a document has been permanently archived and is no longer in use. |
| **Review Independence** | The principle that reviewers derive criteria from policy and their domain expertise, not from orchestrator instructions. |
| **Review Team** | QA plus any TUs assigned to a CR; remains consistent throughout the CR lifecycle. |
| **Reviewer** | User group that reviews and approves assigned documents. |
| **Root Cause** | Fundamental reason for a deviation. |
| **RS (Requirements Specification)** | SDLC document defining what a system shall do; contains requirements only. |
| **RTM (Requirements Traceability Matrix)** | SDLC document mapping requirements to code and verification evidence; proof that requirements are met. |
| **Scope Handoff** | Explicit specification of what the parent accomplished, what the child document absorbs, and confirmation no scope was lost. |
| **Sidecar File** | JSON metadata file in `.meta/` managed by the QMS CLI; stores workflow state separate from document content. |
| **Static Field** | A field in the executable block that is defined at document creation and is never editable (e.g., test step instructions). |
| **Subagent** | A spawned agent assigned a specific role (e.g., Quality agent, Reviewer agent). |
| **System** | A distinct codebase governed under the QMS (e.g., a web application, a CLI tool). |
| **System Release** | A versioned, qualified state of a system's code; format `{SYSTEM}-{MAJOR}.{MINOR}`. |
| **Task Outcome** | Pass or Fail designation for each execution item; Fail requires a VAR or ER attachment. |
| **Task Prompt** | The instruction provided when spawning a subagent. |
| **Terminal State** | A state from which no further transitions are possible (CLOSED, RETIRED). |
| **TP (Test Protocol)** | Optional child document of a CR detailing test procedures; follows its own executable workflow. |
| **TU (Technical Unit)** | Member of the Reviewer group; domain expert assigned by QA to review technical changes. |
| **Unit Test** | Automated, deterministic verification script; one of three RTM verification types. |
| **VAR (Variance Report)** | Child document created when execution cannot proceed as planned; encapsulates resolution work for non-test executable documents. Type 1 requires full closure; Type 2 requires pre-approval to unblock parent. |
| **Verification Record (VR)** | Pre-approved evidence form for structured behavioral verification; child of CR, VAR, or ADD; born IN_EXECUTION with no pre-review phase. |
| **Workspace** | Per-user directory at `.claude/users/{username}/workspace/` containing documents checked out by that user. |
