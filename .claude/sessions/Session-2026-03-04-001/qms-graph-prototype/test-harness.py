#!/usr/bin/env python3
"""
QMS Graph Test Harness - Automated testing of graph traversals.

Runs scripted scenarios through the graph engine and reports results.
Designed to be used both interactively and by AI agents for usability testing.

Usage:
  python test-harness.py                    # Run all tests
  python test-harness.py --scenario happy   # Run specific scenario
  python test-harness.py --list             # List available scenarios
  python test-harness.py --graph cr-lifecycle --describe  # Describe a graph
"""

import sys
import os
import json
from pathlib import Path

# Add parent to path for engine import
sys.path.insert(0, str(Path(__file__).parent))
from engine import Graph, Ticket, Evaluator, AutoRunner, load_graph, _summarize

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
DIM = "\033[2m"


# ---------------------------------------------------------------------------
# Test scenarios
# ---------------------------------------------------------------------------

SCENARIOS = {
    # === CR LIFECYCLE ===
    "cr-happy-path": {
        "description": "CR created, reviewed, approved, executed (all pass), post-reviewed, post-approved, closed",
        "graph": "cr-lifecycle",
        "responses": [
            {"title": "Add constraint solver caching"},                          # cr.start
            {"purpose": "Improve solver performance by caching constraint evaluations",
             "trigger": "feature", "trigger_reference": ""},                     # cr.purpose
            {"current_state": "Solver re-evaluates all constraints every frame",
             "proposed_state": "Solver caches unchanged constraints between frames",
             "affected_systems": "solver, sketch"},                              # cr.scope
            {"risk_level": "medium", "backwards_compatible": "yes",
             "impact_description": "Changes solver internals; external API unchanged"},  # cr.impact
            {"ei_description": "Implement constraint cache in solver.py",
             "ei_expected_outcome": "Cache hit rate >80% on static scenes",
             "ei_needs_vr": "yes"},                                              # cr.implementation-plan (EI-1)
            {"add_more": "yes"},                                                 # cr.add-more-eis
            {"ei_description": "Add cache invalidation on entity mutation",
             "ei_expected_outcome": "Cache correctly invalidates when entities move",
             "ei_needs_vr": "no"},                                               # cr.implementation-plan (EI-2)
            {"add_more": "no"},                                                  # cr.add-more-eis
            {"testing_approach": "Unit tests for cache hit/miss, integration test with 100-constraint scene",
             "test_plan_reference": ""},                                         # cr.testing-summary
            {"decision": "submit"},                                              # cr.draft-review
            # checkin-for-review (no schema)
            {"reviewers": "qa, tu_sketch"},                                      # cr.assign-reviewers
            {"all_recommend": "yes"},                                            # cr.wait-for-reviews
            # route-approval (no schema, gated)
            {"decision": "approve"},                                             # cr.approval-decision
            {"action": "release"},                                               # cr.pre-approved
            # release (no schema)
            {"ei_number": "EI-1", "actual_outcome": "Implemented cache; hit rate 92%",
             "evidence": "commit abc1234, pytest: 18 passed", "outcome": "pass"},  # cr.execute-ei
            {"more_eis": "yes"},                                                 # cr.more-eis
            {"ei_number": "EI-2", "actual_outcome": "Cache invalidation working",
             "evidence": "commit def5678, pytest: 22 passed", "outcome": "pass"},  # cr.execute-ei
            {"more_eis": "no"},                                                  # cr.more-eis
            {"scope_integrity_check": "all-eis-documented"},                     # cr.execution-complete
            {"all_recommend": "yes"},                                            # cr.post-review-wait
            # post-approval-route (no schema)
            {"decision": "approve"},                                             # cr.post-approval-decision
            {"action": "close"},                                                 # cr.post-approved
            {"children_status": "all-resolved"},                                 # cr.check-children
            # closed (terminal)
        ],
        "expected_state": "complete",
        "expected_min_steps": 20,
    },

    "cr-review-rejection-loop": {
        "description": "CR goes through review, gets request-updates, author revises, re-reviews, then approved",
        "graph": "cr-lifecycle",
        "responses": [
            {"title": "Fix input handler focus bug"},
            {"purpose": "Ghost inputs after modal close",
             "trigger": "defect", "trigger_reference": "INV-012"},
            {"current_state": "Focus state not reset on modal close",
             "proposed_state": "Reset interaction state on modal stack change",
             "affected_systems": "ui"},
            {"risk_level": "low", "backwards_compatible": "yes",
             "impact_description": "UI-only change, no data model impact"},
            {"ei_description": "Add reset_interaction_state call in push_modal/pop_modal",
             "ei_expected_outcome": "No ghost clicks after modal close",
             "ei_needs_vr": "yes"},
            {"add_more": "no"},
            {"testing_approach": "Manual verification + unit test for modal stack reset"},
            {"decision": "submit"},
            # checkin-for-review
            {"reviewers": "qa, tu_ui"},
            {"all_recommend": "no"},       # REVIEWER REQUESTS UPDATES
            {"revision_summary": "Added edge case handling for nested modals per tu_ui feedback"},
            # loops back to wait-for-reviews
            {"all_recommend": "yes"},      # All recommend on second pass
            # route-approval
            {"decision": "approve"},
            {"action": "release"},
            # release
            {"ei_number": "EI-1", "actual_outcome": "Implemented reset; tested with nested modals",
             "evidence": "commit aaa1111, manual test: no ghost clicks", "outcome": "pass"},
            {"more_eis": "no"},
            {"scope_integrity_check": "all-eis-documented"},
            {"all_recommend": "yes"},
            {"decision": "approve"},
            {"action": "close"},
            {"children_status": "all-resolved"},
        ],
        "expected_state": "complete",
    },

    "cr-ei-failure-with-var": {
        "description": "CR execution where an EI fails, triggering VAR creation",
        "graph": "cr-lifecycle",
        "responses": [
            {"title": "Migrate to Numba solver backend"},
            {"purpose": "Performance improvement for large constraint sets",
             "trigger": "feature"},
            {"current_state": "Python-only solver", "proposed_state": "Numba JIT solver",
             "affected_systems": "solver, solver_kernels"},
            {"risk_level": "high", "backwards_compatible": "yes",
             "impact_description": "Major internal refactor; external behavior unchanged"},
            {"ei_description": "Port constraint evaluation to Numba kernels",
             "ei_expected_outcome": "10x speedup on 50+ constraint scenes",
             "ei_needs_vr": "yes"},
            {"add_more": "yes"},
            {"ei_description": "Update solver.py to use Numba backend by default",
             "ei_expected_outcome": "F9 toggle works, default is Numba",
             "ei_needs_vr": "no"},
            {"add_more": "no"},
            {"testing_approach": "Benchmark suite + regression tests"},
            {"decision": "submit"},
            {"reviewers": "qa, tu_sketch, tu_sim"},
            {"all_recommend": "yes"},
            {"decision": "approve"},
            {"action": "release"},
            # EI-1 FAILS
            {"ei_number": "EI-1", "actual_outcome": "Only 4x speedup achieved, not 10x",
             "evidence": "benchmark results: 4.2x avg improvement", "outcome": "fail"},
            # Deviation handling
            {"var_type": "type-2", "var_title": "Solver speedup below target",
             "deviation_description": "Target was 10x, achieved 4.2x. Acceptable for initial release."},
            {"more_eis": "yes"},
            {"ei_number": "EI-2", "actual_outcome": "Toggle works correctly",
             "evidence": "commit bbb2222, manual test: F9 switches backends", "outcome": "pass"},
            {"more_eis": "no"},
            {"scope_integrity_check": "all-eis-documented"},
            {"all_recommend": "yes"},
            {"decision": "approve"},
            {"action": "close"},
            {"children_status": "all-resolved"},
        ],
        "expected_state": "complete",
    },

    "cr-approval-rejection": {
        "description": "CR gets rejected at pre-approval, author revises and re-routes without re-review",
        "graph": "cr-lifecycle",
        "responses": [
            {"title": "Update SOP-005 section references"},
            {"purpose": "SOP-005 references are out of date", "trigger": "process-improvement"},
            {"current_state": "SOP-005 references SOP-002 v1.0",
             "proposed_state": "SOP-005 references SOP-002 v2.0",
             "affected_systems": "qms, sops"},
            {"risk_level": "low", "backwards_compatible": "n/a",
             "impact_description": "Documentation-only change"},
            {"ei_description": "Update cross-references in SOP-005",
             "ei_expected_outcome": "All references point to current SOP versions",
             "ei_needs_vr": "no"},
            {"add_more": "no"},
            {"testing_approach": "Manual review of all cross-references"},
            {"decision": "submit"},
            {"reviewers": "qa"},
            {"all_recommend": "yes"},
            {"decision": "reject", "rejection_comment": "Missing SOP-003 reference update"},  # REJECTED
            {"revision_plan": "Add SOP-003 v2.1 reference update to scope",
             "needs_re_review": "no"},
            # Goes back to route-approval (not re-review)
            {"decision": "approve"},      # Approved on second try
            {"action": "release"},
            {"ei_number": "EI-1", "actual_outcome": "Updated all cross-references including SOP-003",
             "evidence": "commit ccc3333, diff shows 4 reference updates", "outcome": "pass"},
            {"more_eis": "no"},
            {"scope_integrity_check": "all-eis-documented"},
            {"all_recommend": "yes"},
            {"decision": "approve"},
            {"action": "close"},
            {"children_status": "all-resolved"},
        ],
        "expected_state": "complete",
    },

    # === REVIEW-APPROVAL ===
    "ra-happy-path": {
        "description": "Simple review-approval: all recommend, approver approves",
        "graph": "review-approval",
        "responses": [
            # ra.start (no schema)
            {"reviewers": "qa, tu_ui"},
            {"outcome": "recommend", "comment": "Looks good, well-structured change"},
            # route-approval (no schema, gated)
            {"decision": "approve"},
            # approved (terminal)
        ],
        "expected_state": "complete",
    },

    "ra-request-updates-loop": {
        "description": "Reviewer requests updates, author revises, then approved",
        "graph": "review-approval",
        "responses": [
            {"reviewers": "qa, tu_sim"},
            {"outcome": "request-updates", "comment": "Missing impact analysis for physics engine"},
            {"revision_summary": "Added detailed impact analysis for Verlet integration changes"},
            # Loops back to ra.start -> assign-reviewers -> collect-reviews
            {"reviewers": "qa, tu_sim"},
            {"outcome": "recommend", "comment": "Impact analysis is now adequate"},
            {"decision": "approve"},
        ],
        "expected_state": "complete",
    },

    "ra-rejection-with-re-review": {
        "description": "Approver rejects, author revises with re-review",
        "graph": "review-approval",
        "responses": [
            {"reviewers": "qa"},
            {"outcome": "recommend", "comment": "Acceptable"},
            {"decision": "reject", "rejection_comment": "Scope is too broad, split into two CRs"},
            {"revision_plan": "Narrowed scope to UI changes only; split physics into CR-XXX",
             "needs_re_review": "yes"},
            # Back to ra.start (full re-review)
            {"reviewers": "qa, tu_ui"},
            {"outcome": "recommend", "comment": "Scope is now appropriate"},
            {"decision": "approve"},
        ],
        "expected_state": "complete",
    },

    # === BUILD-TEMPLATE ===
    # === INV LIFECYCLE ===
    "inv-happy-path": {
        "description": "Investigation: deviation found, RCA performed, CAPAs defined, executed, approved, closed",
        "graph": "inv-lifecycle",
        "responses": [
            {"title": "Solver convergence failures on complex scenes", "deviation_type": "product"},
            {"triggering_event": "Solver fails to converge with >10 constraints",
             "discovery_method": "execution-failure", "related_documents": "CR-042"},
            {"expected_behavior": "Solver converges within 100 iterations",
             "actual_behavior": "Solver oscillates indefinitely with 12+ constraints",
             "timeline": "Discovered during CR-042 EI-3 execution on 2026-03-01"},
            {"facts": "Benchmark shows oscillation pattern at iteration 85-100 for 12+ constraints",
             "evidence_reviewed": "Solver logs, benchmark output, constraint graph visualization"},
            {"affected_systems": "solver, sketch", "severity": "major",
             "scope_of_impact": "All scenes with complex constraint chains"},
            {"analysis_method": "5-whys", "root_cause": "Constraint ordering creates cyclic dependencies",
             "contributing_factors": "No cycle detection in constraint graph",
             "analysis_detail": "Why oscillate? -> conflicting corrections. Why conflict? -> cyclic deps. Why cyclic? -> no ordering. Root: missing topological sort."},
            {"capa_type": "corrective", "description": "Add topological sort to constraint evaluation",
             "implementation": "Modify solver.py to sort constraints before evaluation",
             "requires_child_cr": "yes"},
            {"add_more": "yes"},
            {"capa_type": "preventive", "description": "Add cycle detection warning",
             "implementation": "Add constraint graph validation on entity creation",
             "requires_child_cr": "yes"},
            {"add_more": "no"},
            {"decision": "submit"},
            # checkin-route
            {"reviewers": "qa, tu_sketch"},
            {"all_recommend": "yes"},
            # route-approval
            {"decision": "approve"},
            # release
            {"capa_id": "CAPA-001", "action_taken": "Implemented topological sort in solver.py",
             "evidence": "CR-055 CLOSED, commit abc1234", "outcome": "pass",
             "child_cr_reference": "CR-055"},
            {"more": "yes"},
            {"capa_id": "CAPA-002", "action_taken": "Added cycle detection with warning",
             "evidence": "CR-056 CLOSED, commit def5678", "outcome": "pass",
             "child_cr_reference": "CR-056"},
            {"more": "no"},
            {"capa_integrity": "all-complete"},
            {"all_recommend": "yes"},
            # post-approval-route
            {"decision": "approve"},
            # close
        ],
        "expected_state": "complete",
        "expected_min_steps": 20,
    },

    "inv-capa-failure": {
        "description": "Investigation where a CAPA execution fails, creating a child VAR",
        "graph": "inv-lifecycle",
        "responses": [
            {"title": "Process bypass during CR-036 execution", "deviation_type": "procedural"},
            {"triggering_event": "Audit found EI executed without pre-approval",
             "discovery_method": "audit"},
            {"expected_behavior": "All EIs executed after CR approval",
             "actual_behavior": "EI-3 executed before pre-approval was obtained",
             "timeline": "Discovered during routine audit on 2026-02-20"},
            {"facts": "Commit timestamps show code changes before approval date",
             "evidence_reviewed": "Git log, audit trail, approval timestamp"},
            {"affected_systems": "qms", "severity": "critical",
             "scope_of_impact": "CR-036 execution integrity compromised"},
            {"analysis_method": "5-whys", "root_cause": "No automated gate enforcement for execution start",
             "analysis_detail": "Why executed early? No gate. Why no gate? CLI allowed checkout from DRAFT. Root: missing state enforcement."},
            {"capa_type": "corrective", "description": "Add state check to CLI checkout command",
             "implementation": "Update qms-cli checkout to reject from non-PRE_APPROVED states for EI execution",
             "requires_child_cr": "yes"},
            {"add_more": "yes"},
            {"capa_type": "preventive", "description": "Add pre-execution commit hook",
             "implementation": "Git hook verifies CR status before allowing execution commits",
             "requires_child_cr": "no"},
            {"add_more": "no"},
            {"decision": "submit"},
            {"reviewers": "qa"},
            {"all_recommend": "yes"},
            {"decision": "approve"},
            # CAPA-001 fails
            {"capa_id": "CAPA-001", "action_taken": "Attempted CLI update but broke existing workflow",
             "evidence": "pytest: 3 failures in checkout tests", "outcome": "fail"},
            {"var_title": "CLI checkout state enforcement broke existing tests",
             "deviation_description": "New state check blocks legitimate checkout scenarios"},
            {"more": "yes"},
            {"capa_id": "CAPA-002", "action_taken": "Implemented pre-execution commit hook",
             "evidence": "Hook installed, tested with 5 scenarios", "outcome": "pass"},
            {"more": "no"},
            {"capa_integrity": "all-complete"},
            {"all_recommend": "yes"},
            {"decision": "approve"},
        ],
        "expected_state": "complete",
    },

    # === DEVIATION HANDLING ===
    "dh-execution-failure-type2-var": {
        "description": "Execution failure creates Type 2 VAR (non-blocking)",
        "graph": "deviation-handling",
        "responses": [
            {"parent_doc": "CR-042", "deviation_description": "Performance target missed by 40%",
             "deviation_category": "execution-failure"},
            {"var_type": "type-2", "var_title": "Performance below target",
             "scope_handoff": "Performance optimization moved to VAR; core functionality delivered by parent CR"},
        ],
        "expected_state": "complete",
    },

    "dh-test-failure-creates-er": {
        "description": "Test step failure creates Exception Report",
        "graph": "deviation-handling",
        "responses": [
            {"parent_doc": "CR-042", "deviation_description": "Test step 3 failed: expected 60fps, got 45fps",
             "deviation_category": "test-failure"},
            {"parent_tp": "CR-042-TP-001", "failed_step": "Step 3: Frame rate verification",
             "failure_description": "Frame rate 45fps instead of target 60fps",
             "er_title": "Frame rate below threshold in benchmark"},
            {"root_cause": "Unoptimized rendering path for large particle counts",
             "resolution": "Implement batch rendering for particles",
             "re_execution_plan": "Re-run step 3 after optimization commit"},
        ],
        "expected_state": "complete",
    },

    "dh-systemic-creates-inv": {
        "description": "Process violation identified as systemic, creates Investigation",
        "graph": "deviation-handling",
        "responses": [
            {"parent_doc": "CR-050", "deviation_description": "Third instance of skipping post-review",
             "deviation_category": "process-violation"},
            {"is_systemic": "yes"},
            {"inv_title": "Repeated post-review bypass pattern"},
        ],
        "expected_state": "complete",
    },

    "dh-type1-var-blocking": {
        "description": "Execution failure creates Type 1 VAR (blocking parent)",
        "graph": "deviation-handling",
        "responses": [
            {"parent_doc": "CR-060", "deviation_description": "Core feature cannot be implemented as planned",
             "deviation_category": "scope-change"},
            {"var_type": "type-1", "var_title": "Fundamental approach change needed",
             "scope_handoff": "Original EI-2 scope transferred to VAR; parent retains EI-1 and EI-3"},
            {"acknowledged": "understood"},
        ],
        "expected_state": "complete",
    },

    # === CONDITIONAL REQUIRED (required_when) ===
    "cr-rejection-missing-comment": {
        "description": "Rejection without comment triggers required_when validation error",
        "graph": "cr-lifecycle",
        "responses": [
            {"title": "Test CR"},
            {"purpose": "Test", "trigger": "feature"},
            {"current_state": "A", "proposed_state": "B", "affected_systems": "ui"},
            {"risk_level": "low", "backwards_compatible": "yes", "impact_description": "none"},
            {"ei_description": "Do thing", "ei_expected_outcome": "Thing done", "ei_needs_vr": "no"},
            {"add_more": "no"},
            {"testing_approach": "Manual"},
            {"decision": "submit"},
            {"reviewers": "qa"},
            {"all_recommend": "yes"},
            {"decision": "reject"},  # Rejects WITHOUT rejection_comment — should trigger required_when error
            {"revision_plan": "fix it", "needs_re_review": "no"},
            {"decision": "approve"},
            {"action": "release"},
            {"ei_number": "EI-1", "actual_outcome": "Done", "evidence": "commit aaa", "outcome": "pass"},
            {"more_eis": "no"},
            {"scope_integrity_check": "all-eis-documented"},
            {"all_recommend": "yes"},
            {"decision": "approve"},
            {"action": "close"},
            {"children_status": "all-resolved"},
        ],
        "expected_state": "complete",
        "_expect_validation_errors": True,
    },

    # === BUILD-TEMPLATE ===
    "bt-inherited-template": {
        "description": "Build a template WITH inheritance from a base template",
        "graph": "build-template",
        "responses": [
            {"template_type": "Code Change Record"},                              # bt.start
            {"title": "Code CR Template"},                                        # bt.name
            {"inherit": "yes"},                                                   # bt.inherit -> select-base
            {"base_template": "code-cr-base"},                                    # bt.select-base
            {"step_name": "Implement Code Changes"},                              # bt.step-name
            {"performer": "initiator"},                                           # bt.step-performer
            {"evidence_description": "Commit hash and description",
             "evidence_required": True},                                          # bt.step-evidence
            {"has_gate": "yes", "gate_description": "CR must be released"},       # bt.step-gate
            {"has_hook": "yes", "hook_command": "git checkout -b feature",
             "hook_failure_mode": "log"},                                         # bt.step-hook
            {"add_another": "yes"},                                               # bt.add-another (loop)
            {"step_name": "Run Test Suite"},                                      # bt.step-name (#2)
            {"performer": "initiator"},                                           # bt.step-performer (#2)
            {"evidence_description": "pytest output with pass/fail counts",
             "evidence_required": True},                                          # bt.step-evidence (#2)
            {"has_gate": "no"},                                                   # bt.step-gate (#2)
            {"has_hook": "yes", "hook_command": "pytest --tb=short",
             "hook_failure_mode": "block"},                                       # bt.step-hook (#2)
            {"add_another": "no"},                                                # bt.add-another
            {"include_extension_point": True},                                    # bt.extension-point
            {"decision": "submit"},                                               # bt.review
        ],
        "expected_state": "complete",
    },

    "bt-revise-before-submit": {
        "description": "Build template, choose revise at review, then submit",
        "graph": "build-template",
        "responses": [
            {"template_type": "Audit"},                                           # bt.start
            {"title": "Audit Template"},                                          # bt.name
            {"inherit": "no"},                                                    # bt.inherit
            {"step_name": "Audit Checklist"},                                     # bt.step-name
            {"performer": "quality"},                                             # bt.step-performer
            {"evidence_description": "Completed checklist",
             "evidence_required": True},                                          # bt.step-evidence
            {"has_gate": "no"},                                                   # bt.step-gate
            {"has_hook": "no"},                                                   # bt.step-hook
            {"add_another": "no"},                                                # bt.add-another
            {"include_extension_point": False},                                   # bt.extension-point
            {"decision": "revise"},                                               # bt.review -> bt.step-name
            # After revise, goes to bt.step-name (redefine steps)
            {"step_name": "Pre-Audit Prep"},                                      # bt.step-name (#2)
            {"performer": "initiator"},                                           # bt.step-performer (#2)
            {"evidence_description": "Prep notes",
             "evidence_required": False},                                         # bt.step-evidence (#2)
            {"has_gate": "no"},                                                   # bt.step-gate (#2)
            {"has_hook": "no"},                                                   # bt.step-hook (#2)
            {"add_another": "yes"},                                               # bt.add-another (#2)
            {"step_name": "Audit Execution"},                                     # bt.step-name (#3)
            {"performer": "quality"},                                             # bt.step-performer (#3)
            {"evidence_description": "Completed checklist with findings",
             "evidence_required": True},                                          # bt.step-evidence (#3)
            {"has_gate": "yes", "gate_description": "Pre-audit prep must be complete"},
            {"has_hook": "no"},                                                   # bt.step-hook (#3)
            {"add_another": "no"},                                                # bt.add-another (#3)
            {"include_extension_point": True},                                    # bt.extension-point (#2)
            {"decision": "submit"},                                               # bt.review
        ],
        "expected_state": "complete",
    },

    # === STRESS TESTS ===
    "cr-scope-revision-full-cycle": {
        "description": "CR approved, then scope-revised back to draft, full re-cycle",
        "graph": "cr-lifecycle",
        "responses": [
            {"title": "Refactor compiler bridge"},
            {"purpose": "Simplify compiler interface", "trigger": "process-improvement"},
            {"current_state": "Complex compiler API", "proposed_state": "Simplified API",
             "affected_systems": "compiler, simulation"},
            {"risk_level": "high", "backwards_compatible": "no",
             "impact_description": "API change affects all callers"},
            {"ei_description": "Refactor compiler.py API", "ei_expected_outcome": "New API working",
             "ei_needs_vr": "yes"},
            {"add_more": "no"},
            {"testing_approach": "Full regression suite"},
            {"decision": "submit"},
            {"reviewers": "qa, tu_sim"},
            {"all_recommend": "yes"},
            {"decision": "approve"},
            # PRE_APPROVED but decide to scope-revise!
            {"action": "scope-revision"},
            {"revision_justification": "Need to add backwards compatibility shim for existing callers"},
            # Back to cr.purpose — full re-cycle
            {"purpose": "Simplify compiler + add compat shim", "trigger": "process-improvement"},
            {"current_state": "Complex compiler API", "proposed_state": "Simplified API with compat layer",
             "affected_systems": "compiler, simulation"},
            {"risk_level": "medium", "backwards_compatible": "yes",
             "impact_description": "API change with backwards compat shim"},
            {"ei_description": "Refactor compiler.py + add compat shim",
             "ei_expected_outcome": "New and old API both work",
             "ei_needs_vr": "yes"},
            {"add_more": "no"},
            {"testing_approach": "Full regression + compat tests"},
            {"decision": "submit"},
            {"reviewers": "qa, tu_sim"},
            {"all_recommend": "yes"},
            {"decision": "approve"},
            {"action": "release"},  # This time, release
            {"ei_number": "EI-1", "actual_outcome": "Refactored with compat shim",
             "evidence": "commit xyz, 45 tests pass", "outcome": "pass"},
            {"more_eis": "no"},
            {"scope_integrity_check": "all-eis-documented"},
            {"all_recommend": "yes"},
            {"decision": "approve"},
            {"action": "close"},
            {"children_status": "all-resolved"},
        ],
        "expected_state": "complete",
        "expected_min_steps": 30,
    },

    "inv-rca-revision-loop": {
        "description": "INV gets request-updates on RCA, author revises, then approved",
        "graph": "inv-lifecycle",
        "responses": [
            {"title": "Repeated test failures in CI", "deviation_type": "product"},
            {"triggering_event": "CI failing 3x in a row",
             "discovery_method": "monitoring"},
            {"expected_behavior": "CI green", "actual_behavior": "CI red",
             "timeline": "Last 3 commits all failed CI"},
            {"facts": "Flaky test detected", "evidence_reviewed": "CI logs"},
            {"affected_systems": "qms", "severity": "minor",
             "scope_of_impact": "CI reliability"},
            {"analysis_method": "5-whys", "root_cause": "Flaky test due to timing dependency",
             "analysis_detail": "Why fail? Timing. Why timing? No mock. Root: test relies on wall clock."},
            {"capa_type": "corrective", "description": "Fix flaky test",
             "implementation": "Mock time dependency", "requires_child_cr": "no"},
            {"add_more": "yes"},
            {"capa_type": "preventive", "description": "Add CI flake detection",
             "implementation": "Auto-retry + flake report", "requires_child_cr": "no"},
            {"add_more": "no"},
            {"decision": "submit"},
            {"reviewers": "qa"},
            {"all_recommend": "no"},  # REQUEST UPDATES
            {"revision_summary": "Strengthened RCA with 5-whys chain and added contributing factor analysis"},
            # loops back to wait
            {"all_recommend": "yes"},
            {"decision": "approve"},
            # release
            {"capa_id": "CAPA-001", "action_taken": "Mocked time in test",
             "evidence": "CI green for 10 consecutive runs", "outcome": "pass"},
            {"more": "yes"},
            {"capa_id": "CAPA-002", "action_taken": "Added flake detection script",
             "evidence": "Script deployed, 0 flakes detected in 24h", "outcome": "pass"},
            {"more": "no"},
            {"capa_integrity": "all-complete"},
            {"all_recommend": "yes"},
            {"decision": "approve"},
        ],
        "expected_state": "complete",
    },

    "bt-simple-template": {
        "description": "Build a simple 2-step template without inheritance",
        "graph": "build-template",
        "responses": [
            {"template_type": "Investigation"},                                   # bt.start
            {"title": "Standard Investigation Template"},                         # bt.name
            {"inherit": "no"},                                                    # bt.inherit
            {"step_name": "Root Cause Analysis"},                                 # bt.step-name
            {"performer": "initiator"},                                           # bt.step-performer
            {"evidence_description": "Detailed RCA using 5-Whys methodology",
             "evidence_required": True},                                          # bt.step-evidence
            {"has_gate": "no"},                                                   # bt.step-gate
            {"has_hook": "no"},                                                   # bt.step-hook
            {"add_another": "yes"},                                               # bt.add-another
            {"step_name": "CAPA Definition"},                                     # bt.step-name (#2)
            {"performer": "initiator"},                                           # bt.step-performer (#2)
            {"evidence_description": "At least one corrective and one preventive action",
             "evidence_required": True},                                          # bt.step-evidence (#2)
            {"has_gate": "yes", "gate_description": "RCA must be complete"},      # bt.step-gate (#2)
            {"has_hook": "no"},                                                   # bt.step-hook (#2)
            {"add_another": "no"},                                                # bt.add-another (#2)
            {"include_extension_point": True},                                    # bt.extension-point
            {"decision": "submit"},                                               # bt.review
        ],
        "expected_state": "complete",
    },
}


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

def run_scenario(name: str, scenario: dict, verbose: bool = True) -> dict:
    """Run a single test scenario. Returns result dict."""
    graph_dir = str(Path(__file__).parent / scenario["graph"])
    graph = Graph()
    graph.load_directory(graph_dir)

    runner = AutoRunner(graph, scenario["responses"], f"test-{name}")
    result = runner.run()

    # Check expectations
    passed = True
    failures = []

    expected_state = scenario.get("expected_state", "complete")
    if result["state"] != expected_state:
        passed = False
        failures.append(f"Expected state '{expected_state}', got '{result['state']}'")

    expected_min = scenario.get("expected_min_steps")
    if expected_min and result["steps"] < expected_min:
        passed = False
        failures.append(f"Expected at least {expected_min} steps, got {result['steps']}")

    expect_errors = scenario.get("_expect_validation_errors", False)
    if result["errors"] and not expect_errors:
        passed = False
        failures.extend(result["errors"])
    elif result["errors"] and expect_errors:
        # Expected validation errors — count as pass signal
        pass

    result["passed"] = passed
    result["failures"] = failures
    result["name"] = name
    result["description"] = scenario["description"]

    if verbose:
        status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
        print(f"  [{status}] {name}: {scenario['description']}")
        print(f"         Steps: {result['steps']}, State: {result['state']}")
        if failures:
            for f in failures:
                print(f"         {RED}! {f}{RESET}")
        if verbose and not passed:
            print(f"         {DIM}Log:{RESET}")
            for entry in result["log"][-5:]:
                print(f"           {DIM}{entry}{RESET}")
        print()

    return result


def describe_graph(graph_dir: str):
    """Print a human-readable description of a graph."""
    graph = Graph()
    graph.load_directory(graph_dir)

    print(f"\n{BOLD}Graph: {Path(graph_dir).stem}{RESET}")
    print(f"  Nodes: {len(graph.nodes)}")
    print(f"  Start: {graph.start_node.id if graph.start_node else 'None'}")

    errors = graph.validate()
    if errors:
        print(f"  {RED}Errors: {len(errors)}{RESET}")
        for e in errors:
            print(f"    - {e}")
    else:
        print(f"  {GREEN}Valid{RESET}")

    print(f"\n{BOLD}Nodes:{RESET}")
    for nid, node in graph.nodes.items():
        performer_tag = f" [{node.performer}]" if node.performer != "initiator" else ""
        terminal_tag = " [TERMINAL]" if node.terminal else ""
        wait_tag = " [WAIT]" if node.wait else ""
        gate_tag = " [GATED]" if node.gate else ""
        edge_count = len(node.edges)
        schema_fields = list(node.evidence_schema.keys()) if node.evidence_schema else []

        print(f"  {BOLD}{nid}{RESET}{performer_tag}{terminal_tag}{wait_tag}{gate_tag}")
        print(f"    Prompt: {node.prompt[:60]}")
        if schema_fields:
            print(f"    Fields: {', '.join(schema_fields)}")
        print(f"    Edges:  {edge_count} -> {', '.join(e.get('to','?') for e in node.edges)}")
        hook_phases = list(node.hooks.keys()) if node.hooks else []
        if hook_phases:
            print(f"    Hooks:  {', '.join(hook_phases)}")
        print()


def run_all(verbose: bool = True) -> dict:
    """Run all scenarios. Returns summary."""
    results = []
    for name, scenario in SCENARIOS.items():
        result = run_scenario(name, scenario, verbose)
        results.append(result)

    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])
    total = len(results)

    print(f"\n{'=' * 64}")
    if failed == 0:
        print(f"  {GREEN}{BOLD}ALL {total} SCENARIOS PASSED{RESET}")
    else:
        print(f"  {RED}{BOLD}{failed}/{total} SCENARIOS FAILED{RESET}")
    print(f"{'=' * 64}\n")

    return {"total": total, "passed": passed, "failed": failed, "results": results}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="QMS Graph Test Harness")
    parser.add_argument("--scenario", help="Run a specific scenario")
    parser.add_argument("--list", action="store_true", help="List available scenarios")
    parser.add_argument("--graph", help="Graph directory to describe")
    parser.add_argument("--describe", action="store_true", help="Describe a graph's structure")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    parser.add_argument("--dump", help="Dump results to JSON file")
    args = parser.parse_args()

    if args.list:
        print(f"\n{BOLD}Available scenarios:{RESET}\n")
        for name, scenario in SCENARIOS.items():
            graph = scenario["graph"]
            steps = len(scenario["responses"])
            print(f"  {BOLD}{name}{RESET} ({graph}, {steps} steps)")
            print(f"    {scenario['description']}\n")
        return

    if args.describe and args.graph:
        graph_dir = str(Path(__file__).parent / args.graph)
        describe_graph(graph_dir)
        return

    if args.scenario:
        if args.scenario not in SCENARIOS:
            print(f"Unknown scenario: {args.scenario}")
            print(f"Available: {', '.join(SCENARIOS.keys())}")
            sys.exit(1)
        result = run_scenario(args.scenario, SCENARIOS[args.scenario], not args.quiet)
        if args.dump:
            with open(args.dump, "w") as f:
                json.dump(result, f, indent=2, default=str)
        sys.exit(0 if result["passed"] else 1)

    # Run all
    summary = run_all(not args.quiet)
    if args.dump:
        with open(args.dump, "w") as f:
            json.dump(summary, f, indent=2, default=str)
    sys.exit(0 if summary["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
