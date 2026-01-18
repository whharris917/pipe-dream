# QMS CLI Testing Strategy

## Two-Tier Test Architecture

The qms-cli qualification employs a two-tier testing strategy that balances traceability with maintainability.

### Tier 1: Qualification Tests (Behavioral)

**Purpose:** Prove the system works as users expect. These tests are mapped to requirements in the RTM and serve as formal verification evidence.

**Characteristics:**
- Workflow-level scope (e.g., "CR Full Lifecycle")
- Execute actual CLI commands
- Verify observable outcomes (files exist, status changes, output correct)
- Multiple requirements verified per test
- Inline `[REQ-XXX]` markers for traceability
- RTM maps each requirement to specific file:line

**Location:** `qms-cli/tests/qualification/`

**Example:**
```python
def test_cr_full_lifecycle(qms_module, temp_project):
    """Walk a CR through its complete lifecycle."""

    # [REQ-DOC-001] [REQ-DOC-004] Create CR
    run("qms --user claude create CR --title 'Test CR'")
    assert exists("QMS/CR/CR-001/CR-001-draft.md")

    # [REQ-WF-008] [REQ-META-004] Release transitions to IN_EXECUTION
    run("qms --user claude release CR-001")
    assert status("CR-001") == "IN_EXECUTION"
    assert meta("CR-001")["execution_phase"] == "post_release"
```

### Tier 2: Unit Tests (Diagnostic)

**Purpose:** Diagnose *why* something broke when qualification tests fail. These are developer tools, not formal verification evidence.

**Characteristics:**
- Function/module-level scope
- Test internal components in isolation
- Fast execution, narrow focus
- Not mapped in RTM
- Help pinpoint root cause of failures

**Location:** `qms-cli/tests/` (existing structure)

**Example:**
```python
def test_release_transition():
    """Verify workflow engine handles release correctly."""
    engine = get_workflow_engine()
    result = engine.get_transition(
        current_status=Status.PRE_APPROVED,
        action=Action.RELEASE,
        is_executable=True
    )
    assert result.to_status == Status.IN_EXECUTION
```

## Diagnosis Workflow

When a qualification test fails:

1. **Qualification test output** tells you *what* requirement is broken:
   ```
   FAILED test_cr_full_lifecycle - line 45
   AssertionError: status is "PRE_APPROVED", expected "IN_EXECUTION"
   ```

2. **Unit tests** tell you *where* in the code the problem is:
   ```
   test_workflow.py::test_release_transition .......... PASSED
   test_workflow.py::test_get_transition_pre_approved . FAILED  ← root cause
   test_qms_meta.py::test_update_meta_release ......... PASSED
   ```

3. **Fix** the specific component, then verify the qualification test passes.

## Regression Protection

After each future CR:
- **Unit tests** catch component-level regressions early in development
- **Qualification tests** provide final verification that requirements still hold

Both tiers run in CI. Unit test failures block merge. Qualification test failures indicate a requirement has been broken.

## Test Environment Isolation

Both tiers use the `temp_project` fixture from `conftest.py` to create isolated temporary QMS structures. No test modifies the production QMS.

## RTM Mapping Format

The RTM maps requirements to qualification tests at line-level granularity:

| REQ ID | Test File | Test Function | Lines | Assertion |
|--------|-----------|---------------|-------|-----------|
| REQ-WF-008 | test_cr_lifecycle.py | test_cr_full_lifecycle | 43-45 | `assert status == "IN_EXECUTION"` |
| REQ-META-004 | test_cr_lifecycle.py | test_cr_full_lifecycle | 43-46 | `assert execution_phase == "post_release"` |

Unit tests are not included in the RTM — they exist purely for diagnostic purposes.
