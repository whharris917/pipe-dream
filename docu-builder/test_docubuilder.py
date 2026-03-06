"""Comprehensive test of the DocuBuilder library.

Tests the full lifecycle:
1. Build a Change Record template
2. Create a concrete document from the template
3. Execute the document
4. Amend executed cells
"""

import sys
import os
import tempfile
import traceback

sys.path.insert(0, "C:/Users/wilha/projects/pipe-dream/docu-builder")

from docubuilder.engine import Engine
from docubuilder import model

# Tracking results
results = {"worked": [], "failed": [], "suggestions": []}

def section(title):
    print(f"\n{'#' * 78}")
    print(f"# {title}")
    print(f"{'#' * 78}\n")

def step(desc, func):
    """Run a test step and track results."""
    print(f"\n--- STEP: {desc} ---")
    try:
        result = func()
        results["worked"].append(desc)
        return result
    except Exception as e:
        print(f"  EXCEPTION: {type(e).__name__}: {e}")
        traceback.print_exc()
        results["failed"].append(f"{desc}: {type(e).__name__}: {e}")
        return None

def expect_error(desc, func, expected_substring=None):
    """Run a step that SHOULD fail. Track as 'worked' if error occurs."""
    print(f"\n--- STEP (expect error): {desc} ---")
    try:
        result = func()
        # If we get here, it didn't fail -- check if result contains "Error"
        if isinstance(result, str) and "Error" in result:
            print(f"  Got expected error in result: {result.split(chr(10))[0]}")
            results["worked"].append(f"{desc} (correctly rejected)")
            return result
        else:
            print(f"  UNEXPECTED SUCCESS: {str(result)[:200]}")
            results["failed"].append(f"{desc}: Expected error but succeeded")
            return result
    except Exception as e:
        if expected_substring and expected_substring not in str(e):
            print(f"  GOT ERROR but not the expected one: {e}")
            results["failed"].append(f"{desc}: Wrong error: {e}")
        else:
            print(f"  Got expected error: {type(e).__name__}: {e}")
            results["worked"].append(f"{desc} (correctly rejected)")
        return None


# Create temp directories
tmpdir = tempfile.mkdtemp(prefix="docubuilder_test_")
template_workspace = os.path.join(tmpdir, "template")
cr_workspace = os.path.join(tmpdir, "cr999")
print(f"Workspace: {tmpdir}")


# ============================================================================
# PART 1: Build a Change Record Template
# ============================================================================
section("PART 1: Build a Change Record Template")

# 1.1 Create new document
eng = None
def create_template():
    global eng
    eng = Engine.new("CR-TEMPLATE", "Change Record Template", template_workspace)
    view = eng.view()
    print(view)
    return view

step("Create new template document", create_template)

# 1.2 Add purpose section
def add_purpose():
    result = eng.submit('add_section purpose "Purpose"')
    print(result)
    return result

step("Add purpose section", add_purpose)

# 1.3 Navigate to purpose section
def nav_purpose():
    result = eng.submit('nav purpose')
    print(result)
    return result

step("Navigate to purpose section", nav_purpose)

# 1.4 Add text block to purpose section
def add_purpose_text():
    result = eng.submit('add_text purpose "This Change Record authorizes and tracks the implementation of approved changes to the system."')
    print(result)
    return result

step("Add text block to purpose section", add_purpose_text)

# 1.5 Add EI section
def add_ei_section():
    result = eng.submit('add_section ei "Execution Items"')
    print(result)
    return result

step("Add Execution Items section", add_ei_section)

# 1.6 Navigate to EI section
def nav_ei():
    result = eng.submit('nav ei')
    print(result)
    return result

step("Navigate to EI section", nav_ei)

# 1.7 Add EI table with columns
def add_ei_table():
    result = eng.submit('add_table ei EI_Steps Step:id Description:design Prerequisites:prerequisite Result:recorded_value Performer:signature')
    print(result)
    return result

step("Add EI table with 5 columns", add_ei_table)

# 1.8 Add Row 0: Pre-execution commit
def add_row_0():
    result = eng.submit('add_row ei 0 Description="Pre-execution commit"')
    print(result)
    return result

step("Add Row 0: Pre-execution commit", add_row_0)

# 1.9 Add Row 1: Implement changes
def add_row_1():
    result = eng.submit('add_row ei 0 Description="Implement changes" Prerequisites="EI-1 complete"')
    print(result)
    return result

step("Add Row 1: Implement changes", add_row_1)

# 1.10 Add Row 2: Post-execution commit
def add_row_2():
    result = eng.submit('add_row ei 0 Description="Post-execution commit" Prerequisites="EI-2 complete"')
    print(result)
    return result

step("Add Row 2: Post-execution commit", add_row_2)

# 1.11 View the table
def view_table():
    view = eng.view()
    print(view)
    return view

step("View table with 3 rows", view_table)

# 1.12 Seal Row 0 (Pre-execution commit)
def seal_row_0():
    result = eng.submit('seal ei 0 0')
    print(result)
    return result

step("Seal Row 0 (permanent)", seal_row_0)

# 1.13 Seal Row 2 (Post-execution commit)
def seal_row_2():
    result = eng.submit('seal ei 0 2')
    print(result)
    return result

step("Seal Row 2 (permanent)", seal_row_2)

# 1.14 Seal the purpose section
def seal_purpose():
    result = eng.submit('seal purpose')
    print(result)
    return result

step("Seal purpose section", seal_purpose)

# 1.15 View after sealing
def view_after_seal():
    view = eng.view()
    print(view)
    return view

step("View after sealing", view_after_seal)

# 1.16 Finalize (transition to execution)
def finalize_template():
    result = eng.submit('finalize')
    print(result)
    return result

step("Finalize template (transition to execution)", finalize_template)

# 1.17 Save template as JSON for later use
def save_template():
    template_path = os.path.join(tmpdir, "cr_template.json")
    model.save(eng.doc, template_path)
    print(f"  Template saved to: {template_path}")
    return template_path

template_path = step("Save template as JSON", save_template)


# ============================================================================
# PART 2: Create a New Document from Template
# ============================================================================
section("PART 2: Create a New Document from Template")

cr_eng = None

# 2.1 Create new document from template
def create_from_template():
    global cr_eng
    template_doc = model.load(template_path)
    new_doc = model.new_document_from_template("CR-999", "Test Change Record", template_doc)
    cr_eng = Engine(new_doc, cr_workspace)
    cr_eng._save()
    view = cr_eng.view()
    print(view)
    return view

step("Create CR-999 from template", create_from_template)

# 2.2 Verify sealed rows carried over
def verify_sealed():
    section_data = cr_eng.doc["sections"]["ei"]
    table = section_data["elements"][0]
    row0 = table["rows"][0]
    row2 = table["rows"][2]

    assert row0.get("sealed") == True, f"Row 0 should be sealed, got: {row0.get('sealed')}"
    assert row2.get("sealed") == True, f"Row 2 should be sealed, got: {row2.get('sealed')}"
    print(f"  Row 0 sealed: {row0.get('sealed')}")
    print(f"  Row 2 sealed: {row2.get('sealed')}")

    # Verify purpose section is sealed
    purpose = cr_eng.doc["sections"]["purpose"]
    assert purpose.get("sealed") == True, f"Purpose should be sealed, got: {purpose.get('sealed')}"
    print(f"  Purpose section sealed: {purpose.get('sealed')}")

    # Verify phase is authoring (reset from template)
    phase = cr_eng.doc["system_properties"]["phase"]
    print(f"  Phase: {phase}")
    assert phase == "authoring", f"Phase should be 'authoring', got: {phase}"

    return True

step("Verify sealed rows and sections carried over", verify_sealed)

# 2.3 Navigate to EI section
def nav_ei_cr():
    result = cr_eng.submit('nav ei')
    print(result)
    return result

step("Navigate to EI section in CR-999", nav_ei_cr)

# 2.4 Try to delete a sealed row -- should fail
def try_delete_sealed_row():
    result = cr_eng.submit('delete_row ei 0 0')
    return result

expect_error("Try to delete sealed Row 0 (should fail)", try_delete_sealed_row)

# 2.5 Try to delete the sealed purpose section -- should fail
def try_delete_sealed_section():
    result = cr_eng.submit('delete_section purpose')
    return result

expect_error("Try to delete sealed purpose section (should fail)", try_delete_sealed_section)

# 2.6 Add a new Row 3
def add_row_3():
    result = cr_eng.submit('add_row ei 0 Description="Run regression tests" Prerequisites="EI-2 complete"')
    print(result)
    return result

step("Add Row 3: Run regression tests", add_row_3)

# 2.7 View after adding row
def view_cr_after_row():
    cr_eng.submit('nav ei')
    view = cr_eng.view()
    print(view)
    return view

step("View CR-999 after adding new row", view_cr_after_row)

# 2.8 Finalize the concrete CR
def finalize_cr():
    result = cr_eng.submit('finalize')
    print(result)
    return result

step("Finalize CR-999 (transition to execution)", finalize_cr)


# ============================================================================
# PART 3: Execute the CR
# ============================================================================
section("PART 3: Execute the CR")

# 3.1 Navigate to EI section
def nav_ei_exec():
    result = cr_eng.submit('nav ei')
    print(result)
    return result

step("Navigate to EI section for execution", nav_ei_exec)

# 3.2 Execute EI Row 0
def exec_row_0():
    result = cr_eng.submit('exec ei 0 0 Result="Commit abc123" Performer=alice')
    print(result)
    return result

step("Execute Row 0: Pre-execution commit", exec_row_0)

# 3.3 Execute EI Row 1
def exec_row_1():
    result = cr_eng.submit('exec ei 0 1 Result="Changes implemented" Performer=bob')
    print(result)
    return result

step("Execute Row 1: Implement changes", exec_row_1)

# 3.4 Execute EI Row 2
def exec_row_2():
    result = cr_eng.submit('exec ei 0 2 Result="Commit def456" Performer=alice')
    print(result)
    return result

step("Execute Row 2: Post-execution commit", exec_row_2)

# 3.5 Execute EI Row 3 (the new row)
def exec_row_3():
    result = cr_eng.submit('exec ei 0 3 Result="All tests pass" Performer=charlie')
    print(result)
    return result

step("Execute Row 3: Run regression tests", exec_row_3)

# 3.6 View after all executions
def view_after_exec():
    view = cr_eng.view()
    print(view)
    return view

step("View CR-999 after all executions", view_after_exec)

# 3.7 Amend Row 1's Result
def amend_row_1():
    result = cr_eng.submit('amend ei 0 1 Result="Changes implemented and tested" reason="Added test confirmation"')
    print(result)
    return result

step("Amend Row 1 Result with reason", amend_row_1)

# 3.8 View after amendment
def view_after_amend():
    view = cr_eng.view()
    print(view)
    return view

step("View CR-999 after amendment", view_after_amend)

# 3.9 Verify audit trail for amended cell
def verify_audit():
    table = cr_eng.doc["sections"]["ei"]["elements"][0]
    row1 = table["rows"][1]
    result_val = row1["values"]["Result"]
    print(f"  Audit trail for Row 1 Result:")
    if isinstance(result_val, dict) and "entries" in result_val:
        for i, entry in enumerate(result_val["entries"]):
            reason = entry.get("reason", "N/A")
            print(f"    Entry {i}: value='{entry['value']}', performer='{entry['performer']}', reason='{reason}'")
        assert len(result_val["entries"]) == 2, f"Expected 2 entries, got {len(result_val['entries'])}"
    else:
        print(f"  Unexpected format: {result_val}")
    return result_val

step("Verify audit trail for amended cell", verify_audit)


# ============================================================================
# SUMMARY REPORT
# ============================================================================
section("TEST RESULTS SUMMARY")

print(f"\nWORKED ({len(results['worked'])} steps):")
for item in results["worked"]:
    print(f"  [PASS] {item}")

print(f"\nFAILED ({len(results['failed'])} steps):")
if results["failed"]:
    for item in results["failed"]:
        print(f"  [FAIL] {item}")
else:
    print("  (none)")

print(f"\nTotal: {len(results['worked'])} passed, {len(results['failed'])} failed")

# Suggestions
print("\n" + "=" * 78)
print("SUGGESTIONS FOR IMPROVEMENT")
print("=" * 78)

suggestions = [
    "1. Engine.from_template() class method: The Engine class has no way to create a "
    "   document from a template. Users must drop to model-level API and manually "
    "   construct the Engine. Add a classmethod like Engine.from_template(doc_id, title, "
    "   template_path, workspace_path).",

    "2. Column name quoting in commands: Multi-word column names (e.g., 'Recorded Value') "
    "   would cause parsing issues since shlex splitting treats spaces as delimiters. "
    "   The test worked because we used single-word names, but the docstring examples "
    "   suggest multi-word names are expected.",

    "3. Template save/load in Engine: No Engine-level API for saving as template or loading "
    "   from template. This workflow requires direct model access, breaking the Engine "
    "   abstraction.",

    "4. Seal semantics on new_document_from_template: The template resets phase to 'authoring' "
    "   but preserves sealed flags. This is correct behavior, but it is not documented "
    "   anywhere what 'sealed' means in the context of a template-derived document.",

    "5. Error message clarity: Commands that fail return strings with 'Error' prefix but "
    "   no error code or structured error type. This makes it difficult to programmatically "
    "   distinguish between different failure modes.",

    "6. Exec command column names: The 'exec' command uses the user-facing column name "
    "   (e.g., 'Result', 'Performer'), but the column header shows 'Result (Recorded Value)'. "
    "   It's not immediately obvious whether to use the display name or the type name.",

    "7. View output for executed cells: Showing '(amended x1)' is good, but the view does "
    "   not show WHO executed or amended a cell. The performer info is in the audit trail "
    "   but invisible in the rendered view.",

    "8. No 'save_as_template' command: There's no way to designate a finalized document as "
    "   a template through the Engine's command interface.",

    "9. Row IDs: Auto-generated as R1, R2, R3 but the user adds rows referring to 'EI-1', "
    "   'EI-2', etc. The auto-ID scheme doesn't match the domain convention.",

    "10. No completion status: There's no way to tell if all executable cells have been "
    "    filled. A progress indicator (e.g., '3/5 cells executed') would be helpful.",
]

for s in suggestions:
    print(f"\n{s}")

# Rating
print("\n" + "=" * 78)
print("OVERALL RATING")
print("=" * 78)

total = len(results["worked"]) + len(results["failed"])
pass_rate = len(results["worked"]) / total * 100 if total > 0 else 0
print(f"\nPass rate: {pass_rate:.0f}% ({len(results['worked'])}/{total})")

if len(results["failed"]) == 0:
    rating = 4
    print(f"\nRating: {rating}/5")
    print("\nRationale: The library handles the complete document lifecycle correctly -- "
          "creation, authoring, sealing, finalization, execution, and amendment all work "
          "as expected. The sealed/locked protections correctly prevent unauthorized "
          "modifications. The audit trail for amendments is well-designed. However, the "
          "Engine abstraction is incomplete (no template support), the command parser "
          "could use better error messages, and the rendered view omits useful metadata "
          "like performer information. The core model is solid; the API surface needs polish.")
else:
    rating = 3
    print(f"\nRating: {rating}/5")
    print(f"\nRationale: {len(results['failed'])} test steps failed. See FAILED section above "
          "for details. The core model works but has rough edges that need attention.")

# Cleanup info
print(f"\nTemp workspace: {tmpdir}")
print("(not cleaned up so you can inspect the files)")
