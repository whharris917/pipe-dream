"""
Test the DocuBuilder prerequisite blocking system.
Uses file-based checkout/edit/checkin workflow (no submit()).
"""

import sys
import os
import shutil

sys.path.insert(0, "C:/Users/wilha/projects/pipe-dream/docu-builder")
from docubuilder import Engine

WORKSPACE = "C:/Users/wilha/projects/pipe-dream/docu-builder/_pipeline_test/prereq-ws"
DOC_PATH = os.path.join(WORKSPACE, "document.txt")


def read_doc():
    """Read and return the current document.txt content."""
    with open(DOC_PATH) as f:
        return f.read()


def write_command(cmd):
    """Write a command at the >> prompt line in document.txt."""
    with open(DOC_PATH) as f:
        lines = f.read().split("\n")
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().startswith(">>"):
            lines[i] = f">> {cmd}"
            break
    with open(DOC_PATH, "w") as f:
        f.write("\n".join(lines))


def print_table_portion(content, label):
    """Print just the table portion of the document output."""
    lines = content.split("\n")
    in_table = False
    table_lines = []
    for line in lines:
        # Table markers: lines with | or lines with Step, or progress lines
        if "|" in line or "Progress:" in line or "[Table" in line or "[BLOCKED]" in line:
            in_table = True
            table_lines.append(line)
        elif in_table and line.strip() == "":
            table_lines.append(line)
            in_table = False
        elif in_table:
            table_lines.append(line)

    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"{'='*70}")
    for line in table_lines:
        print(line)
    print(f"{'='*70}\n")


# ---------- Clean slate ----------
if os.path.exists(WORKSPACE):
    shutil.rmtree(WORKSPACE)
os.makedirs(WORKSPACE, exist_ok=True)

# ========== STEP 1: Create document ==========
print("STEP 1: Creating document CR-TEST 'Prerequisite Test'")
eng = Engine.new("CR-TEST", "Prerequisite Test", WORKSPACE)
status = "Document created"
print(f"  Result: {status}")

# ========== STEP 2: Add section "steps" titled "Test Steps" ==========
print("\nSTEP 2: Adding section 'steps' titled 'Test Steps'")
write_command('add_section steps "Test Steps"')
result = eng.checkin()
print(f"  Result: {result}")

# ========== STEP 3: Add table with columns ==========
print("\nSTEP 3: Adding table with columns Step:id, Task:design, Prereq:prerequisite, Result:recorded_value, Sign:signature")
write_command('add_table steps "Test Steps" Step:id Task:design Prereq:prerequisite Result:recorded_value Sign:signature id_prefix=S-')
result = eng.checkin()
print(f"  Result: {result}")

# ========== STEP 4: Add rows ==========
print("\nSTEP 4: Adding rows")

# Row 0: Task="Setup environment"
write_command('add_row steps 0 Task="Setup environment"')
result = eng.checkin()
print(f"  Row 0 (Setup environment): {result}")

# Row 1: Task="Run unit tests" Prereq="S-1 complete"
write_command('add_row steps 0 Task="Run unit tests" Prereq="S-1 complete"')
result = eng.checkin()
print(f"  Row 1 (Run unit tests): {result}")

# Row 2: Task="Run integration tests" Prereq="S-2 complete"
write_command('add_row steps 0 Task="Run integration tests" Prereq="S-2 complete"')
result = eng.checkin()
print(f"  Row 2 (Run integration tests): {result}")

# Row 3: Task="Deploy to staging" Prereq="S-3 complete"
write_command('add_row steps 0 Task="Deploy to staging" Prereq="S-3 complete"')
result = eng.checkin()
print(f"  Row 3 (Deploy to staging): {result}")

# ========== STEP 5: Finalize ==========
print("\nSTEP 5: Finalizing document")
write_command("finalize")
result = eng.checkin()
print(f"  Result: {result}")

# ========== STEP 6: Navigate to steps and read document.txt ==========
print("\nSTEP 6: Navigate to steps section and read document.txt")
write_command("nav steps")
result = eng.checkin()
print(f"  Nav result: {result}")

content = read_doc()
print_table_portion(content, "STEP 6: After finalize - Initial state")

# Analyze ready vs blocked
lines = content.split("\n")
for line in lines:
    if "S-" in line and "|" in line and "Step" not in line and "---" not in line:
        row_id = line.split("|")[1].strip() if "|" in line else "?"
        if "<<  >>" in line:
            marker = "READY (<<  >>)"
        elif "<< -- >>" in line:
            marker = "BLOCKED (<< -- >>)"
        elif "BLOCKED" in line:
            marker = "BLOCKED"
        else:
            marker = "OTHER"
        print(f"  {row_id}: {marker}")

# ========== STEP 7: Try to execute row 1 (S-2) before row 0 (S-1) is done ==========
print("\nSTEP 7: Attempting to execute S-2 (row 1) BEFORE S-1 (row 0) is complete")
write_command('exec steps 0 1 Result="All 42 unit tests pass" Sign="bob"')
result = eng.checkin()
print(f"  Result: {result}")

# ========== STEP 8: Execute row 0 (S-1) ==========
print("\nSTEP 8: Executing S-1 (row 0): Result='Environment ready' Sign='alice'")
write_command('exec steps 0 0 Result="Environment ready" Sign="alice"')
result = eng.checkin()
print(f"  Result: {result}")

# ========== STEP 9: Read document.txt again ==========
print("\nSTEP 9: Reading document.txt after S-1 completion")
# Navigate back to steps to see the table
write_command("nav steps")
result = eng.checkin()

content = read_doc()
print_table_portion(content, "STEP 9: After S-1 complete")

lines = content.split("\n")
for line in lines:
    if "S-" in line and "|" in line and "Step" not in line and "---" not in line:
        row_id = line.split("|")[1].strip() if "|" in line else "?"
        if "<<  >>" in line:
            marker = "READY (<<  >>)"
        elif "<< -- >>" in line:
            marker = "BLOCKED (<< -- >>)"
        elif "BLOCKED" in line:
            marker = "BLOCKED"
        else:
            marker = "COMPLETED"
        print(f"  {row_id}: {marker}")

# ========== STEP 10: Execute row 1 (S-2) ==========
print("\nSTEP 10: Executing S-2 (row 1): Result='All 42 unit tests pass' Sign='bob'")
write_command('exec steps 0 1 Result="All 42 unit tests pass" Sign="bob"')
result = eng.checkin()
print(f"  Result: {result}")

# ========== STEP 11: Execute row 2 (S-3) ==========
print("\nSTEP 11: Executing S-3 (row 2): Result='Integration tests pass' Sign='bob'")
write_command('exec steps 0 2 Result="Integration tests pass" Sign="bob"')
result = eng.checkin()
print(f"  Result: {result}")

# ========== STEP 12: Execute row 3 (S-4) ==========
print("\nSTEP 12: Executing S-4 (row 3): Result='Deployed to staging.example.com' Sign='carol'")
write_command('exec steps 0 3 Result="Deployed to staging.example.com" Sign="carol"')
result = eng.checkin()
print(f"  Result: {result}")

# ========== STEP 13: view_all and print final document.txt ==========
print("\nSTEP 13: view_all - Final document state")
write_command("view_all")
result = eng.checkin()

content = read_doc()
print_table_portion(content, "STEP 13: Final completed document")

# Also print full document for completeness
print("\n--- FULL FINAL DOCUMENT ---")
print(content)
print("--- END ---")

# ========== SUMMARY ==========
print("\n" + "=" * 70)
print("  SUMMARY")
print("=" * 70)
print("""
VISUAL DISTINCTION:
- <<  >>    = READY: empty executable cell, can be executed now
- << -- >>  = BLOCKED: prerequisite not met, cannot execute
- [BLOCKED] = Row-level blocking indicator
- Filled values (no markers) = COMPLETED cells

PREREQUISITE ENFORCEMENT:
- Step 7 tested executing S-2 before S-1 was complete.
  The system should have rejected this with an error.

OVERALL RATING: (see results above)
""")
