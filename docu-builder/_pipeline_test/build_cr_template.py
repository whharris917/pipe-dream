"""
Build a Change Record template using DocuBuilder's checkout/edit/checkin workflow.

This script uses the file-based workflow (read document.txt, edit the >> line,
call eng.checkin()) -- NOT submit().
"""

import sys
import os

sys.path.insert(0, "C:/Users/wilha/projects/pipe-dream/docu-builder")
from docubuilder import Engine

WORKSPACE = "C:/Users/wilha/projects/pipe-dream/docu-builder/_pipeline_test/cr-template-ws"
DOC_PATH = os.path.join(WORKSPACE, "document.txt")
TEMPLATE_OUT = "C:/Users/wilha/projects/pipe-dream/docu-builder/_pipeline_test/cr-template.json"

os.makedirs(WORKSPACE, exist_ok=True)


def read_doc():
    """Read and return the current document.txt content."""
    with open(DOC_PATH) as f:
        return f.read()


def write_command(command: str):
    """Find the >> prompt line in document.txt and write the command there."""
    with open(DOC_PATH) as f:
        lines = f.read().split("\n")
    found = False
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().startswith(">>"):
            lines[i] = f">> {command}"
            found = True
            break
    if not found:
        raise RuntimeError("No >> prompt found in document.txt!")
    with open(DOC_PATH, "w") as f:
        f.write("\n".join(lines))


def do_command(eng, command: str, description: str):
    """Execute a single command through the file-based workflow."""
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"COMMAND: {command}")
    print(f"{'='*60}")

    # 1. Write command to the >> prompt line in document.txt
    write_command(command)

    # 2. Checkin: parses the command, executes it, auto-checks-out next rendition
    status = eng.checkin()
    print(f"STATUS: {status}")
    return status


# ========================================================================
# Step 1: Create the Engine (auto-checks-out first rendition)
# ========================================================================
print("Creating new document...")
eng = Engine.new("CR-TMPL", "Change Record Template", WORKSPACE)

# Read the initial checkout to confirm it worked
print("\n--- INITIAL document.txt ---")
initial = read_doc()
print(initial)

# ========================================================================
# Step 2: Add the "header" section
# ========================================================================
do_command(eng, 'add_section header Header', 'Add header section')

# ========================================================================
# Step 3: Add text to the header section
# ========================================================================
do_command(eng, 'add_text header "Change Record Template - Fill in purpose before finalizing"',
           'Add header text')

# ========================================================================
# Step 4: Add the "ei" section titled "Execution Items"
# ========================================================================
do_command(eng, 'add_section ei "Execution Items"', 'Add ei section')

# ========================================================================
# Step 5: Add the EIs table with the specified columns
# ========================================================================
do_command(eng,
           'add_table ei EIs Step:id Description:design Prerequisites:prerequisite Result:recorded_value Performer:signature id_prefix=EI-',
           'Add EIs table')

# ========================================================================
# Step 6: Navigate to ei section to see the table
# ========================================================================
do_command(eng, 'nav ei', 'Navigate to ei section')

# ========================================================================
# Step 7: Add Row 0: Description="Pre-execution commit"
# ========================================================================
do_command(eng, 'add_row ei 0 Description="Pre-execution commit"',
           'Add row 0: Pre-execution commit')

# ========================================================================
# Step 8: Seal row 0
# ========================================================================
do_command(eng, 'seal ei 0 0', 'Seal row 0')

# ========================================================================
# Step 9: Add Row 1: Description="Implement changes" Prerequisites="EI-1 complete"
# ========================================================================
do_command(eng, 'add_row ei 0 Description="Implement changes" Prerequisites="EI-1 complete"',
           'Add row 1: Implement changes')

# ========================================================================
# Step 10: Add Row 2: Description="Post-execution commit" Prerequisites="EI-2 complete"
# ========================================================================
do_command(eng, 'add_row ei 0 Description="Post-execution commit" Prerequisites="EI-2 complete"',
           'Add row 2: Post-execution commit')

# ========================================================================
# Step 11: Seal row 2
# ========================================================================
do_command(eng, 'seal ei 0 2', 'Seal row 2')

# ========================================================================
# Step 12: Seal the header section
# ========================================================================
do_command(eng, 'seal header', 'Seal header section')

# ========================================================================
# Step 13: View all sections to see full state
# ========================================================================
do_command(eng, 'view_all', 'View all sections')

# ========================================================================
# Step 14: Save as template
# ========================================================================
do_command(eng, f'save_template {TEMPLATE_OUT}', 'Save as template')

# ========================================================================
# Final: Print the final document.txt
# ========================================================================
print("\n" + "=" * 60)
print("FINAL document.txt")
print("=" * 60)
final = read_doc()
print(final)

# Verify the template file exists
if os.path.exists(TEMPLATE_OUT):
    print(f"\nTemplate saved successfully to: {TEMPLATE_OUT}")
    print(f"File size: {os.path.getsize(TEMPLATE_OUT)} bytes")
else:
    print(f"\nWARNING: Template file not found at {TEMPLATE_OUT}")
