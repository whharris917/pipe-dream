"""Engine -- the checkout/edit/checkin cycle for document authoring and execution.

The agent's interface is a text file in the workspace. The cycle is:

    1. checkout() writes a rendered text file to the workspace
    2. The agent reads the file, writes a command after the >> prompt
    3. checkin() reads the file, parses the command, executes it,
       and automatically writes the next rendition (auto-checkout)

Usage:
    from docubuilder import Engine

    # Create a new document -- auto-checks-out the first rendition
    eng = Engine.new("VER-001", "My Verification", "/path/to/workspace")

    # The agent reads /path/to/workspace/document.txt
    # The agent writes a command after the >> prompt, e.g.:
    #   >> add_section 1 "Purpose"
    # Then:
    result = eng.checkin()   # Parses command, executes, writes next rendition
    print(result)            # Status message

    # The agent reads the updated document.txt and repeats

Column types:
    Non-executable (set during authoring, frozen during execution):
        id, design, prerequisite, calculated
    Executable (filled during execution):
        recorded_value, signature, witness, choice_list
"""

import os
from docubuilder import model
from docubuilder.renderer import render
from docubuilder.commands import parse_and_execute

# Name of the rendered text file in the workspace
RENDITION_FILENAME = "document.md"


class Engine:
    """Manages the document lifecycle via a checkout/edit/checkin cycle.

    The workflow is:
        1. Create or load a document (auto-checks-out first rendition)
        2. Agent reads workspace/document.txt
        3. Agent writes command(s) after the >> prompt in document.txt
        4. checkin() parses and executes, then writes next rendition
        5. Repeat until done

    During authoring: add sections, text, tables, rows. Then 'finalize'.
    During execution: fill in executable cells with 'exec'. Amend with 'amend'.
    """

    def __init__(self, doc: dict, workspace_path: str, performer: str = "agent"):
        self.doc = doc
        self.workspace_path = workspace_path
        self.performer = performer
        self.current_section = None
        self.inspect_context = ""
        self._source_path = os.path.join(workspace_path, "source.json")
        self._rendition_path = os.path.join(workspace_path, RENDITION_FILENAME)

    @classmethod
    def new(cls, document_id: str, title: str, workspace_path: str,
            performer: str = "agent") -> "Engine":
        """Create a new blank document. Auto-checks-out the first rendition."""
        doc = model.new_document(document_id, title)
        engine = cls(doc, workspace_path, performer)
        engine._save()
        engine.checkout()
        return engine

    @classmethod
    def from_template(cls, document_id: str, title: str, template_path: str,
                      workspace_path: str, performer: str = "agent") -> "Engine":
        """Create a new document from a template. Auto-checks-out the first rendition."""
        template = model.load(template_path)
        doc = model.new_document_from_template(document_id, title, template)
        engine = cls(doc, workspace_path, performer)
        engine._save()
        engine.checkout()
        return engine

    @classmethod
    def load(cls, workspace_path: str, performer: str = "agent") -> "Engine":
        """Load an existing document and session state from workspace."""
        source_path = os.path.join(workspace_path, "source.json")
        doc = model.load(source_path)
        engine = cls(doc, workspace_path, performer)
        # Restore session state
        session_path = os.path.join(workspace_path, "session.json")
        if os.path.exists(session_path):
            import json
            with open(session_path) as f:
                session = json.load(f)
            engine.current_section = session.get("current_section")
        return engine

    def checkout(self, show_all: bool = False) -> str:
        """Write the current rendition to the workspace file.
        Returns the path to the rendition file."""
        content = render(self.doc, self.current_section, show_all=show_all,
                         inspect_context=self.inspect_context)
        os.makedirs(self.workspace_path, exist_ok=True)
        with open(self._rendition_path, "w", encoding="utf-8") as f:
            f.write(content)
        return self._rendition_path

    def checkin(self) -> str:
        """Read the workspace file, parse command(s) from the command zone,
        execute them, and auto-checkout the next rendition.
        Returns a status message."""
        if not os.path.exists(self._rendition_path):
            return "Error: No rendition file found. Call checkout() first."

        with open(self._rendition_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract command(s) from the command zone (after the >> prompt)
        commands = _extract_commands(content)
        if not commands:
            # Auto-checkout even if no commands (agent may just be reading)
            self.checkout()
            return "No commands found after the >> prompt."

        # Execute each command
        statuses = []
        for cmd_text in commands:
            result = parse_and_execute(self.doc, cmd_text, self.performer,
                                        current_section=self.current_section)

            # Handle navigation
            if result.startswith("__NAV_NEW__:"):
                self.current_section = result.split(":")[1]
                result = f"Section '{self.current_section}' added."
                self._save()
            elif result.startswith("__NAV__:"):
                self.current_section = result.split(":")[1]
                result = f"Navigated to section '{self.current_section}'."
                self._save()
            elif result == "__VIEW_ALL__":
                result = "Showing all sections."
                self._save()
                # Write a view_all rendition and return early
                self.checkout(show_all=True)
                statuses.append(result)
                return "\n".join(statuses)
            elif result.startswith("__INSPECT__:"):
                self.inspect_context = result.split(":", 1)[1]
                result = "Inspect context updated."
            elif cmd_text.strip().lower().startswith("inspect"):
                # Failed inspect — clear stale context
                self.inspect_context = ""
            elif result.startswith("__TEMPLATE_SAVED__:"):
                path = result.split(":", 1)[1]
                result = f"Template saved to '{path}'."
            elif "Error" not in result and "Unknown" not in result:
                self._save()

            statuses.append(result)

        # Auto-checkout next rendition
        self.checkout()

        return "\n".join(statuses)

    # --- Convenience method for programmatic use / testing ---

    def submit(self, command_text: str) -> str:
        """Convenience: write a command to the rendition file and checkin.
        Equivalent to editing document.txt and calling checkin().
        Returns status message."""
        # Write rendition with the command already in the prompt
        content = render(self.doc, self.current_section,
                         inspect_context=self.inspect_context)
        # The rendition ends with ">> " (possibly with trailing whitespace)
        # Replace the empty prompt with the command
        lines = content.split("\n")
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip().startswith(">>"):
                lines[i] = f">> {command_text}"
                break

        os.makedirs(self.workspace_path, exist_ok=True)
        with open(self._rendition_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return self.checkin()

    def _save(self) -> None:
        """Persist document and session state to JSON."""
        import json
        os.makedirs(self.workspace_path, exist_ok=True)
        model.save(self.doc, self._source_path)
        session_path = os.path.join(self.workspace_path, "session.json")
        with open(session_path, "w") as f:
            json.dump({"current_section": self.current_section}, f)


def _extract_commands(content: str) -> list[str]:
    """Extract commands from the command zone of a rendition file.
    Commands appear after lines starting with '>> '."""
    commands = []
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith(">> ") and len(stripped) > 3:
            cmd = stripped[3:].strip()
            if cmd:
                commands.append(cmd)
        elif stripped == ">>":
            # Empty prompt, no command
            continue
    return commands
