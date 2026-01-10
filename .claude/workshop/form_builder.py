#!/usr/bin/env python3
"""
Form Builder - Transactional Multi-Step Prompt System

Prompts build up a form (JSON), but nothing executes until the form is
complete. Incomplete forms are inert and harmless.

Usage:
    # Start new form
    python form_builder.py --start

    # Respond to current prompt
    python form_builder.py --id <form_id> --respond "<value>"

    # View form state
    python form_builder.py --id <form_id> --status

    # Execute completed form
    python form_builder.py --id <form_id> --execute

    # Abandon form
    python form_builder.py --id <form_id> --abandon
"""

import argparse
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

FORMS_DIR = Path(__file__).parent / "forms"


def get_form_path(form_id: str) -> Path:
    return FORMS_DIR / f"{form_id}.json"


def load_form(form_id: str) -> dict | None:
    path = get_form_path(form_id)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def save_form(form: dict):
    path = get_form_path(form["form_id"])
    path.write_text(json.dumps(form, indent=2))


# =============================================================================
# Form Definitions - Each form type defines its prompt sequence
# =============================================================================

FORM_DEFINITIONS = {
    "qms_action": {
        "title": "QMS Action Form",
        "description": "Build a QMS CLI command through guided prompts",
        "steps": [
            {
                "id": "identity_confirm",
                "type": "confirm",
                "prompt": "You are acting as: {identity}\nConfirm this is correct?",
                "dynamic_fields": ["identity"],
                "warning": "Misrepresenting identity violates SOP-007 Section 6.1",
            },
            {
                "id": "action_type",
                "type": "choice",
                "prompt": "What action do you want to perform?",
                "options": ["create", "checkout", "checkin", "route", "review", "approve"],
            },
            {
                "id": "doc_type",
                "type": "choice",
                "prompt": "What document type?",
                "options": ["CR", "SOP", "INV"],
                "condition": {"field": "action_type", "value": "create"},
            },
            {
                "id": "doc_id",
                "type": "text",
                "prompt": "Enter document ID (e.g., CR-001):",
                "condition": {"field": "action_type", "not_value": "create"},
            },
            {
                "id": "title",
                "type": "text",
                "prompt": "Enter document title:",
                "condition": {"field": "action_type", "value": "create"},
            },
            {
                "id": "route_type",
                "type": "choice",
                "prompt": "Route for which phase?",
                "options": ["review", "approval"],
                "condition": {"field": "action_type", "value": "route"},
            },
            {
                "id": "review_outcome",
                "type": "choice",
                "prompt": "Review outcome:",
                "options": ["recommend", "request-updates"],
                "condition": {"field": "action_type", "value": "review"},
            },
            {
                "id": "comment",
                "type": "text",
                "prompt": "Enter comment (required for review):",
                "condition": {"field": "action_type", "value": "review"},
            },
            {
                "id": "final_confirm",
                "type": "confirm",
                "prompt": "Execute command: {generated_command}\n\nProceed?",
                "dynamic_fields": ["generated_command"],
                "warning": "This will modify QMS state.",
            },
        ],
    },
    "simple_test": {
        "title": "Simple Test Form",
        "description": "A minimal form for testing the system",
        "steps": [
            {
                "id": "identity_confirm",
                "type": "confirm",
                "prompt": "You are acting as: {identity}\nConfirm this is correct?",
                "dynamic_fields": ["identity"],
                "warning": "Misrepresenting identity violates SOP-007 Section 6.1",
            },
            {
                "id": "name",
                "type": "text",
                "prompt": "Enter your name:",
            },
            {
                "id": "color",
                "type": "choice",
                "prompt": "Pick a color:",
                "options": ["red", "green", "blue"],
            },
            {
                "id": "confirm",
                "type": "confirm",
                "prompt": "Create greeting for {name} in {color}?",
                "dynamic_fields": ["name", "color"],
            },
        ],
    },
}


def evaluate_condition(condition: dict, responses: dict) -> bool:
    """Check if a step's condition is met."""
    if not condition:
        return True

    field = condition.get("field")
    if "value" in condition:
        return responses.get(field) == condition["value"]
    if "not_value" in condition:
        return responses.get(field) != condition["not_value"]
    if "in" in condition:
        return responses.get(field) in condition["in"]

    return True


def get_current_step(form: dict) -> dict | None:
    """Get the next unanswered step that meets its conditions."""
    definition = FORM_DEFINITIONS[form["form_type"]]
    responses = form["responses"]

    for step in definition["steps"]:
        step_id = step["id"]

        # Skip already answered
        if step_id in responses:
            continue

        # Check condition
        condition = step.get("condition")
        if not evaluate_condition(condition, responses):
            continue

        return step

    return None  # All steps complete


def generate_command(form: dict) -> str:
    """Build the final command from form responses."""
    responses = form["responses"]
    form_type = form["form_type"]

    if form_type == "qms_action":
        identity = form.get("identity", "claude")
        action = responses.get("action_type", "")

        cmd = f"qms --user {identity} {action}"

        if action == "create":
            doc_type = responses.get("doc_type", "CR")
            title = responses.get("title", "")
            cmd += f" {doc_type} --title \"{title}\""
        else:
            doc_id = responses.get("doc_id", "")
            cmd += f" {doc_id}"

            if action == "route":
                route_type = responses.get("route_type", "review")
                cmd += f" --{route_type}"
            elif action == "review":
                outcome = responses.get("review_outcome", "recommend")
                comment = responses.get("comment", "")
                cmd += f" --{outcome} --comment \"{comment}\""

        return cmd

    elif form_type == "simple_test":
        name = responses.get("name", "")
        color = responses.get("color", "")
        return f"echo 'Hello, {name}! Your color is {color}.'"

    return "# No command generated"


def format_prompt(step: dict, form: dict) -> dict:
    """Format a step's prompt with dynamic values."""
    prompt_text = step["prompt"]

    # Replace dynamic fields
    dynamic_fields = step.get("dynamic_fields", [])
    for field in dynamic_fields:
        if field == "generated_command":
            value = generate_command(form)
        elif field == "identity":
            value = form.get("identity", "unknown")
        else:
            value = form["responses"].get(field, f"<{field}>")
        prompt_text = prompt_text.replace(f"{{{field}}}", str(value))

    result = {
        "step_id": step["id"],
        "type": step["type"],
        "prompt": prompt_text,
    }

    if step["type"] == "choice":
        result["options"] = step["options"]

    if "warning" in step:
        result["warning"] = step["warning"]

    return result


# =============================================================================
# Commands
# =============================================================================

def cmd_start(args) -> dict:
    """Start a new form."""
    if not args.identity:
        return {"error": "Identity required. Use --identity <user> (e.g., --identity claude, --identity lead)"}

    form_id = str(uuid.uuid4())[:8]

    form_type = args.form_type or "simple_test"
    if form_type not in FORM_DEFINITIONS:
        return {"error": f"Unknown form type: {form_type}", "available": list(FORM_DEFINITIONS.keys())}

    definition = FORM_DEFINITIONS[form_type]

    form = {
        "form_id": form_id,
        "form_type": form_type,
        "title": definition["title"],
        "identity": args.identity,
        "created_at": datetime.now().isoformat(),
        "responses": {},
        "form_complete": False,
        "command_executed": False,
        "generated_command": None,
    }

    save_form(form)

    # Get first prompt
    step = get_current_step(form)
    current_prompt = format_prompt(step, form) if step else None

    return {
        "status": "created",
        "form_id": form_id,
        "form_type": form_type,
        "title": definition["title"],
        "description": definition["description"],
        "current_prompt": current_prompt,
    }


def cmd_respond(args) -> dict:
    """Respond to the current prompt."""
    form = load_form(args.form_id)
    if not form:
        return {"error": f"Session not found: {args.form_id}"}

    if form["form_complete"]:
        return {"error": "Form already complete", "form_id": args.form_id}

    step = get_current_step(form)
    if not step:
        return {"error": "No pending prompts", "form_id": args.form_id}

    # Validate response
    response = args.respond
    step_type = step["type"]

    if step_type == "choice":
        options = step["options"]
        if response not in options:
            # Try numeric selection
            try:
                idx = int(response) - 1
                if 0 <= idx < len(options):
                    response = options[idx]
                else:
                    return {"error": f"Invalid choice. Options: {options}", "current_prompt": format_prompt(step, form)}
            except ValueError:
                return {"error": f"Invalid choice. Options: {options}", "current_prompt": format_prompt(step, form)}

    elif step_type == "confirm":
        if response.lower() in ("y", "yes", "true", "1"):
            response = True
        elif response.lower() in ("n", "no", "false", "0"):
            response = False
        else:
            return {"error": "Please respond with y/n", "current_prompt": format_prompt(step, form)}

        # If user declines, abort form
        if not response:
            form["abandoned"] = True
            form["abandoned_at"] = datetime.now().isoformat()
            form["abandoned_reason"] = f"User declined at step: {step['id']}"
            save_form(form)
            return {"status": "abandoned", "form_id": args.form_id, "reason": f"Declined at: {step['id']}"}

    # Record response
    form["responses"][step["id"]] = response
    form["updated_at"] = datetime.now().isoformat()

    # Check if form is now complete
    next_step = get_current_step(form)
    if next_step is None:
        form["form_complete"] = True
        form["completed_at"] = datetime.now().isoformat()
        form["generated_command"] = generate_command(form)
        save_form(form)

        return {
            "status": "complete",
            "form_id": args.form_id,
            "form_complete": True,
            "generated_command": form["generated_command"],
            "message": "Form complete. Use --execute to run the command.",
        }

    save_form(form)

    return {
        "status": "continue",
        "form_id": args.form_id,
        "recorded": {step["id"]: response},
        "current_prompt": format_prompt(next_step, form),
    }


def cmd_status(args) -> dict:
    """Show form status."""
    form = load_form(args.form_id)
    if not form:
        return {"error": f"Session not found: {args.form_id}"}

    step = get_current_step(form)

    return {
        "form_id": form["form_id"],
        "form_type": form["form_type"],
        "title": form["title"],
        "identity": form["identity"],
        "created_at": form["created_at"],
        "responses": form["responses"],
        "form_complete": form["form_complete"],
        "command_executed": form["command_executed"],
        "generated_command": form.get("generated_command"),
        "current_prompt": format_prompt(step, form) if step else None,
        "abandoned": form.get("abandoned", False),
    }


def cmd_execute(args) -> dict:
    """Execute a completed form's command."""
    form = load_form(args.form_id)
    if not form:
        return {"error": f"Session not found: {args.form_id}"}

    if not form["form_complete"]:
        return {"error": "Form not complete", "form_id": args.form_id}

    if form["command_executed"]:
        return {"error": "Command already executed", "form_id": args.form_id}

    command = form["generated_command"]

    # For now, just mark as executed (don't actually run)
    # In real implementation, this would execute the command
    form["command_executed"] = True
    form["executed_at"] = datetime.now().isoformat()
    save_form(form)

    return {
        "status": "executed",
        "form_id": args.form_id,
        "command": command,
        "note": "[SIMULATED] Command marked as executed. Real execution would happen here.",
    }


def cmd_abandon(args) -> dict:
    """Abandon an incomplete form."""
    form = load_form(args.form_id)
    if not form:
        return {"error": f"Session not found: {args.form_id}"}

    form["abandoned"] = True
    form["abandoned_at"] = datetime.now().isoformat()
    form["abandoned_reason"] = "User requested abandonment"
    save_form(form)

    return {
        "status": "abandoned",
        "form_id": args.form_id,
    }


def cmd_list(args) -> dict:
    """List all form sessions."""
    forms = []
    for path in FORMS_DIR.glob("*.json"):
        form = json.loads(path.read_text())
        forms.append({
            "form_id": form["form_id"],
            "form_type": form["form_type"],
            "form_complete": form["form_complete"],
            "command_executed": form["command_executed"],
            "abandoned": form.get("abandoned", False),
            "created_at": form["created_at"],
        })

    return {"forms": sorted(forms, key=lambda f: f["created_at"], reverse=True)}


# =============================================================================
# Main
# =============================================================================

def format_prompt_pretty(prompt_data: dict) -> str:
    """Format a prompt for human-readable display."""
    lines = []

    if "warning" in prompt_data:
        lines.append(f"[!] WARNING: {prompt_data['warning']}")
        lines.append("")

    lines.append(prompt_data["prompt"])

    if prompt_data["type"] == "choice":
        lines.append("")
        for i, opt in enumerate(prompt_data["options"], 1):
            lines.append(f"  [{i}] {opt}")
    elif prompt_data["type"] == "confirm":
        lines.append("  [y/n]")

    return "\n".join(lines)


def print_pretty(result: dict):
    """Print result in human-readable format."""
    status = result.get("status")

    if "error" in result:
        print(f"Error: {result['error']}")
        if "current_prompt" in result:
            print()
            print(format_prompt_pretty(result["current_prompt"]))
        return

    if status == "created":
        print(f"Form ID: {result['form_id']}")
        print(f"Title: {result['title']}")
        print("-" * 40)
        if result.get("current_prompt"):
            print(format_prompt_pretty(result["current_prompt"]))

    elif status == "continue":
        print(format_prompt_pretty(result["current_prompt"]))

    elif status == "complete":
        print("Form complete.")
        print(f"Command: {result['generated_command']}")
        print()
        print("Use --execute to run the command.")

    elif status == "executed":
        print(f"Executed: {result['command']}")

    elif status == "abandoned":
        print(f"Form abandoned.")
        if "reason" in result:
            print(f"Reason: {result['reason']}")

    else:
        # Fallback for status and other commands
        print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Form Builder - Transactional Multi-Step Prompts")
    parser.add_argument("--start", action="store_true", help="Start new form")
    parser.add_argument("--form-type", type=str, help="Form type (default: simple_test)")
    parser.add_argument("--identity", type=str, help="Agent identity (required for --start)")
    parser.add_argument("--id", type=str, dest="form_id", help="Form ID")
    parser.add_argument("--respond", type=str, help="Response to current prompt")
    parser.add_argument("--status", action="store_true", help="Show form status")
    parser.add_argument("--execute", action="store_true", help="Execute completed form")
    parser.add_argument("--abandon", action="store_true", help="Abandon form")
    parser.add_argument("--list", action="store_true", help="List all forms")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of pretty format")

    args = parser.parse_args()

    FORMS_DIR.mkdir(parents=True, exist_ok=True)

    if args.start:
        result = cmd_start(args)
    elif args.list:
        result = cmd_list(args)
    elif args.form_id:
        if args.respond:
            result = cmd_respond(args)
        elif args.status:
            result = cmd_status(args)
        elif args.execute:
            result = cmd_execute(args)
        elif args.abandon:
            result = cmd_abandon(args)
        else:
            result = cmd_status(args)
    else:
        parser.print_help()
        return

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_pretty(result)


if __name__ == "__main__":
    main()
