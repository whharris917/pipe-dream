"""Demo script: Create and execute a Test Protocol using docubuilder."""

import sys
import os

# Ensure the library is importable
sys.path.insert(0, os.path.dirname(__file__))

from docubuilder.engine import Engine

# --- 1. Create a new Test Protocol document ---
workspace = os.path.join(os.path.dirname(__file__), "_demo_workspace")
eng = Engine.new("TP-001", "Widget Power-Up Test Protocol", workspace)

print("=== STEP 1: Initial document ===")
print(eng.view())

# --- 2. Add a header section with a text block describing test purpose ---
print("=== STEP 2: Add header section ===")
result = eng.submit('add_section header "Test Purpose and Scope"')
print(result)

print("=== STEP 3: Add purpose text block ===")
result = eng.submit(
    'add_text header "This protocol verifies the power-up sequence of the Widget '
    'assembly. It confirms that startup voltage, LED indicators, and self-test '
    'diagnostics complete within specification. Acceptance criteria: all steps '
    'must pass for the unit to be released."'
)
print(result)

# --- 3. Add a steps section with a test steps table ---
print("=== STEP 4: Add steps section ===")
result = eng.submit('add_section steps "Test Steps"')
print(result)

# Navigate to the steps section
print("=== STEP 5: Navigate to steps section ===")
result = eng.submit('nav steps')
print(result)

# Add a table with columns: Step (id), Instructions (design),
# Expected Result (design), Actual Result (recorded_value), Pass/Fail (signature)
print("=== STEP 6: Add test steps table ===")
result = eng.submit(
    'add_table steps test_steps '
    'Step:id '
    'Instructions:design '
    '"Expected Result:design" '
    '"Actual Result:recorded_value" '
    '"Pass/Fail:signature" '
    'id_prefix=TS-'
)
print(result)

# Add three test step rows
print("=== STEP 7: Add test step rows ===")
result = eng.submit(
    'add_row steps 0 '
    'Instructions="Apply 12V DC to power input terminals" '
    '"Expected Result"="Voltage regulator output reads 5.0V +/- 0.1V"'
)
print(result)

result = eng.submit(
    'add_row steps 0 '
    'Instructions="Observe front-panel LED indicators" '
    '"Expected Result"="Green POWER LED illuminates within 2 seconds"'
)
print(result)

result = eng.submit(
    'add_row steps 0 '
    'Instructions="Monitor serial console for self-test output" '
    '"Expected Result"="Self-test reports ALL PASS within 10 seconds"'
)
print(result)

# --- 4. Lock the first step's instructions (row 0) ---
print("=== STEP 8: Lock first step row ===")
result = eng.submit('lock steps 0 0')
print(result)

# --- 5. Finalize the document (transition to execution) ---
print("=== STEP 9: Finalize document ===")
result = eng.submit('finalize')
print(result)

# --- 6. Execute: fill in actual results and signatures for each step ---
print("=== STEP 10: Execute step 1 ===")
result = eng.submit(
    'exec steps 0 0 '
    '"Actual Result"="Regulator output measured 5.01V" '
    '"Pass/Fail"="PASS -- J. Smith 2026-03-03"'
)
print(result)

print("=== STEP 11: Execute step 2 ===")
result = eng.submit(
    'exec steps 0 1 '
    '"Actual Result"="Green POWER LED lit in 1.3 seconds" '
    '"Pass/Fail"="PASS -- J. Smith 2026-03-03"'
)
print(result)

print("=== STEP 12: Execute step 3 ===")
result = eng.submit(
    'exec steps 0 2 '
    '"Actual Result"="Self-test reported ALL PASS in 7.2 seconds" '
    '"Pass/Fail"="PASS -- J. Smith 2026-03-03"'
)
print(result)

print("=== FINAL: Navigate to header to see full document ===")
result = eng.submit('nav header')
print(result)

print("\nDone. Workspace saved to:", workspace)
