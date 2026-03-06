"""
CR-042 Test Script: Create a Change Record from template using
the file-based checkout/edit/checkin workflow.
"""
import sys
import os

sys.path.insert(0, "C:/Users/wilha/projects/pipe-dream/docu-builder")
from docubuilder import Engine

TEMPLATE = "C:/Users/wilha/projects/pipe-dream/docu-builder/_pipeline_test/cr-template.json"
WORKSPACE = "C:/Users/wilha/projects/pipe-dream/docu-builder/_pipeline_test/cr042-ws"
DOC_PATH = os.path.join(WORKSPACE, "document.txt")


def read_doc():
    with open(DOC_PATH) as f:
        return f.read()


def write_command(cmd):
    """Find the >> prompt line and write the command there."""
    with open(DOC_PATH) as f:
        lines = f.read().split("\n")
    found = False
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().startswith(">>"):
            lines[i] = f">> {cmd}"
            found = True
            break
    if not found:
        raise RuntimeError("No >> prompt found in document.txt")
    with open(DOC_PATH, "w") as f:
        f.write("\n".join(lines))


# ============================================================
# STEP 1: Create CR-042 from template
# ============================================================
print("=" * 70)
print("STEP 1: Create CR-042 from template")
print("=" * 70)

eng = Engine.from_template("CR-042", "Add Dark Mode to Dashboard", TEMPLATE, WORKSPACE)
print("Engine created. Reading initial document.txt...\n")
print(read_doc())

# ============================================================
# STEP 2: Verify sealed rows survived template instantiation
# ============================================================
print("\n" + "=" * 70)
print("STEP 2: Verify sealed rows survived")
print("=" * 70)

content = read_doc()
if "[SEALED]" in content:
    print("PASS: Sealed markers found in document.txt")
else:
    print("FAIL: No sealed markers found!")

if "Pre-execution commit" in content:
    print("PASS: Sealed row 0 (EI-1 'Pre-execution commit') survived")
else:
    print("FAIL: Sealed row 0 missing!")

if "Post-execution commit" in content:
    print("PASS: Sealed row 2 (EI-3 'Post-execution commit') survived")
else:
    print("FAIL: Sealed row 2 missing!")

# ============================================================
# STEP 3: Try to delete sealed row 0 (EI-1) -- expect failure
# ============================================================
print("\n" + "=" * 70)
print("STEP 3: Try to delete sealed row 0 (EI-1) -- should fail")
print("=" * 70)

write_command("delete_row ei 0 0")
result = eng.checkin()
print(f"Result: {result}")

if "error" in result.lower() or "sealed" in result.lower() or "cannot" in result.lower() or "locked" in result.lower():
    print("PASS: Deleting sealed row was correctly rejected")
else:
    print("UNEXPECTED: Deletion was not rejected as expected")

# Read current state to continue
content = read_doc()

# ============================================================
# STEP 4: Try to delete the sealed header section -- expect failure
# ============================================================
print("\n" + "=" * 70)
print("STEP 4: Try to delete sealed header section -- should fail")
print("=" * 70)

write_command("delete_section header")
result = eng.checkin()
print(f"Result: {result}")

if "error" in result.lower() or "sealed" in result.lower() or "cannot" in result.lower() or "locked" in result.lower():
    print("PASS: Deleting sealed section was correctly rejected")
else:
    print("UNEXPECTED: Deletion was not rejected as expected")

# Read current state
content = read_doc()

# ============================================================
# STEP 5: Add new rows to EI table
# ============================================================
print("\n" + "=" * 70)
print("STEP 5: Add new rows to EI table")
print("=" * 70)

# Row: Description="Update CSS variables" Prerequisites="EI-1 complete"
print("\nAdding row: Update CSS variables...")
write_command('add_row ei 0 Description="Update CSS variables" Prerequisites="EI-1 complete"')
result = eng.checkin()
print(f"Result: {result}")

# Row: Description="Add toggle switch" Prerequisites="EI-3 complete"
print("\nAdding row: Add toggle switch...")
write_command('add_row ei 0 Description="Add toggle switch" Prerequisites="EI-3 complete"')
result = eng.checkin()
print(f"Result: {result}")

# Row: Description="Run regression tests" Prerequisites="EI-4 complete"
print("\nAdding row: Run regression tests...")
write_command('add_row ei 0 Description="Run regression tests" Prerequisites="EI-4 complete"')
result = eng.checkin()
print(f"Result: {result}")

# ============================================================
# STEP 6: Use view_all to see the complete document
# ============================================================
print("\n" + "=" * 70)
print("STEP 6: view_all -- complete document")
print("=" * 70)

write_command("view_all")
result = eng.checkin()
print(f"Result: {result}")
print("\nFull document after view_all:\n")
print(read_doc())

# ============================================================
# STEP 7: Finalize the document
# ============================================================
print("\n" + "=" * 70)
print("STEP 7: Finalize the document")
print("=" * 70)

write_command("finalize")
result = eng.checkin()
print(f"Result: {result}")

# ============================================================
# FINAL: Print the final document.txt content
# ============================================================
print("\n" + "=" * 70)
print("FINAL: document.txt content after finalization")
print("=" * 70)
print(read_doc())
