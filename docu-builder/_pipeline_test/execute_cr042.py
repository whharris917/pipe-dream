"""
Execute CR-042 using the file-based checkout/edit/checkin workflow.
"""
import sys
import os

sys.path.insert(0, "C:/Users/wilha/projects/pipe-dream/docu-builder")
from docubuilder import Engine

WS = "C:/Users/wilha/projects/pipe-dream/docu-builder/_pipeline_test/cr042-ws"
DOC_PATH = os.path.join(WS, "document.txt")


def read_doc():
    """Read and return the current document.txt contents."""
    with open(DOC_PATH) as f:
        return f.read()


def write_command(cmd):
    """Find the >> prompt line and write the command there."""
    with open(DOC_PATH) as f:
        lines = f.read().split("\n")
    found = False
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().startswith(">>"):
            lines[i] = ">> " + cmd
            found = True
            break
    if not found:
        raise RuntimeError("Could not find >> prompt in document.txt")
    with open(DOC_PATH, "w") as f:
        f.write("\n".join(lines))


def do_command(eng, cmd):
    """Write a command to document.txt and checkin. Returns the status message."""
    write_command(cmd)
    status = eng.checkin()
    print(f"  CMD: {cmd}")
    print(f"  STATUS: {status}")
    print()
    return status


# ============================================================
# Step 1: Load the document
# ============================================================
print("=" * 60)
print("STEP 1: Load the document")
print("=" * 60)
eng = Engine.load(WS)
print(f"  Engine loaded from {WS}")
print()

# ============================================================
# Step 2: Checkout to ensure document.txt is current
# ============================================================
print("=" * 60)
print("STEP 2: Checkout")
print("=" * 60)
eng.checkout()
print("  Checkout complete")
print()

# Read document after checkout
print("--- document.txt after checkout ---")
print(read_doc())
print("--- end ---")
print()

# ============================================================
# Step 3: view_all to see what needs to be executed
# ============================================================
print("=" * 60)
print("STEP 3: view_all")
print("=" * 60)
do_command(eng, "view_all")

# Read the rendered view
print("--- document.txt after view_all ---")
print(read_doc())
print("--- end ---")
print()

# ============================================================
# Step 4: Navigate to the ei section
# ============================================================
print("=" * 60)
print("STEP 4: Navigate to ei section")
print("=" * 60)
do_command(eng, "nav ei")

print("--- document.txt after nav ei ---")
print(read_doc())
print("--- end ---")
print()

# ============================================================
# Step 5: Execute each row (0-5)
# ============================================================
print("=" * 60)
print("STEP 5: Execute rows 0-5")
print("=" * 60)

exec_data = [
    (0, 'Result="Commit a1b2c3d"', 'Performer="alice"'),
    (1, 'Result="Dark mode implemented"', 'Performer="bob"'),
    (2, 'Result="Commit e4f5g6h"', 'Performer="alice"'),
    (3, 'Result="CSS variables updated"', 'Performer="bob"'),
    (4, 'Result="Toggle switch added"', 'Performer="carol"'),
    (5, 'Result="47 tests passing"', 'Performer="carol"'),
]

for row_idx, result, performer in exec_data:
    print(f"--- Executing row {row_idx} ---")
    cmd = f"exec ei 0 {row_idx} {result} {performer}"
    do_command(eng, cmd)

# ============================================================
# Step 6: view_all to see completed document
# ============================================================
print("=" * 60)
print("STEP 6: view_all (completed)")
print("=" * 60)
do_command(eng, "view_all")

print("--- document.txt after all executions ---")
print(read_doc())
print("--- end ---")
print()

# ============================================================
# Step 7: Amend row 1
# ============================================================
print("=" * 60)
print("STEP 7: Amend row 1")
print("=" * 60)
cmd = 'amend ei 0 1 Result="Dark mode implemented and accessibility reviewed" reason="Added accessibility confirmation"'
do_command(eng, cmd)

# ============================================================
# Step 8: Print the final document.txt
# ============================================================
print("=" * 60)
print("STEP 8: Final document.txt")
print("=" * 60)

# Navigate to view_all for the full picture
do_command(eng, "view_all")

print("--- FINAL document.txt ---")
final = read_doc()
print(final)
print("--- END ---")
