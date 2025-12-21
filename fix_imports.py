import os
import re

# This mapping defines where the modules have moved to.
# Key: Old module name (filename without .py)
# Value: New absolute package path
MODULE_MAP = {
    # App
    "app_controller": "app.app_controller",
    "flow_state_app": "app.flow_state_app",
    
    # Core
    "config": "core.config",
    "definitions": "core.definitions",
    "file_io": "core.file_io",
    "session": "core.session",
    "sound_manager": "core.sound_manager",
    "utils": "core.utils",
    
    # Engine
    "compiler": "engine.compiler",
    "physics_core": "engine.physics_core",
    "simulation": "engine.simulation",
    
    # Model
    "constraints": "model.constraints",
    "geometry": "model.geometry",
    "properties": "model.properties",
    "simulation_geometry": "model.simulation_geometry",
    "sketch": "model.sketch",
    "solver": "model.solver",
    
    # UI
    "input_handler": "ui.input_handler",
    "renderer": "ui.renderer",
    "tools": "ui.tools",
    "ui_manager": "ui.ui_manager",
    "ui_widgets": "ui.ui_widgets",
    
    # UI Folly (Assuming these are self-contained or referenced)
    "folly_app": "ui_folly.folly_app",
    "folly_assets": "ui_folly.folly_assets",
    "folly_main": "ui_folly.folly_main",
    "folly_synth": "ui_folly.folly_synth",
    "folly_ui": "ui_folly.folly_ui",
}

def fix_imports_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    changes_made = False

    for line in lines:
        original_line = line
        
        # 1. Handle "from X import Y"
        # Regex looks for: from <module> import ...
        match_from = re.match(r'^(\s*)from\s+(\w+)\s+(import.*)', line)
        if match_from:
            indent, module, rest = match_from.groups()
            if module in MODULE_MAP:
                new_module = MODULE_MAP[module]
                line = f"{indent}from {new_module} {rest}\n"
        
        # 2. Handle "import X"
        # We change "import config" -> "import core.config as config"
        # This preserves code usage like "config.SCREEN_WIDTH" without refactoring the whole file.
        match_import = re.match(r'^(\s*)import\s+(\w+)(\s*)$', line)
        if match_import:
            indent, module, trailing = match_import.groups()
            if module in MODULE_MAP:
                new_module = MODULE_MAP[module]
                line = f"{indent}import {new_module} as {module}{trailing}\n"

        # 3. Handle "import X as Y"
        match_import_as = re.match(r'^(\s*)import\s+(\w+)\s+as\s+(\w+)', line)
        if match_import_as:
            indent, module, alias = match_import_as.groups()
            if module in MODULE_MAP:
                new_module = MODULE_MAP[module]
                line = f"{indent}import {new_module} as {alias}\n"

        if line != original_line:
            changes_made = True
            print(f"   Refactored: {original_line.strip()}  ->  {line.strip()}")
            
        new_lines.append(line)

    if changes_made:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    return False

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Scanning for python files in: {root_dir}")
    
    count = 0
    for subdir, dirs, files in os.walk(root_dir):
        # Skip the .git folder and __pycache__
        if '.git' in subdir or '__pycache__' in subdir:
            continue
            
        for file in files:
            if file.endswith('.py') and file != 'fix_imports.py':
                filepath = os.path.join(subdir, file)
                print(f"Checking {file}...")
                if fix_imports_in_file(filepath):
                    count += 1
                    
    print(f"\nDone! Updated imports in {count} files.")

if __name__ == "__main__":
    main()