#!/usr/bin/env python3
"""
Multi-Step Prompt Experiment

Tests terminal interactivity with a series of prompts that branch
based on user input. This explores patterns for future QMS CLI
enhancements.
"""

import sys


def clear_line():
    """Move cursor up and clear line (for re-prompting on invalid input)."""
    sys.stdout.write("\033[A\033[K")
    sys.stdout.flush()


def prompt_choice(question: str, options: list[str], allow_quit: bool = True) -> str | None:
    """
    Present a numbered choice prompt.

    Returns the selected option string, or None if user quits.
    """
    print(f"\n{question}")
    print("-" * len(question))

    for i, opt in enumerate(options, 1):
        print(f"  [{i}] {opt}")

    if allow_quit:
        print(f"  [q] Quit")

    while True:
        choice = input("\nYour choice: ").strip().lower()

        if allow_quit and choice == 'q':
            return None

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            pass

        clear_line()
        print(f"Invalid choice. Enter 1-{len(options)}" + (" or 'q'" if allow_quit else ""))


def prompt_confirm(question: str, default: bool = True) -> bool:
    """Yes/no confirmation prompt."""
    suffix = " [Y/n]: " if default else " [y/N]: "

    while True:
        answer = input(f"\n{question}{suffix}").strip().lower()

        if answer == "":
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False

        clear_line()
        print("Please enter 'y' or 'n'")


def prompt_text(question: str, required: bool = True) -> str:
    """Free-text input prompt."""
    while True:
        answer = input(f"\n{question}: ").strip()

        if answer or not required:
            return answer

        clear_line()
        print("This field is required.")


def simulate_document_workflow():
    """Simulate a QMS document workflow decision tree."""

    print("\n" + "=" * 50)
    print("  QMS Document Workflow Simulator")
    print("=" * 50)

    # Step 1: Select document type
    doc_type = prompt_choice(
        "What type of document are you working with?",
        ["Change Record (CR)", "Investigation (INV)", "SOP", "Test Protocol (TP)"]
    )

    if doc_type is None:
        return

    print(f"\n  Selected: {doc_type}")

    # Step 2: Select action based on document type
    if doc_type == "Change Record (CR)":
        actions = ["Create new CR", "Check out existing CR", "Route for review", "Release for execution"]
    elif doc_type == "Investigation (INV)":
        actions = ["Create new INV", "Add CAPA", "Route for review", "Close INV"]
    elif doc_type == "SOP":
        actions = ["Create new SOP", "Revise existing SOP", "Route for review", "View effective version"]
    else:
        actions = ["Create TP from CR", "Execute test case", "Log exception", "Close TP"]

    action = prompt_choice(
        f"What would you like to do with this {doc_type.split()[0]}?",
        actions
    )

    if action is None:
        return

    print(f"\n  Action: {action}")

    # Step 3: Gather details based on action
    if "Create" in action:
        title = prompt_text("Enter document title")
        print(f"\n  Title: {title}")

        confirm = prompt_confirm(f"Create new document with title '{title}'?")

        if confirm:
            print("\n  [SIMULATED] Document created successfully!")
            print(f"  [SIMULATED] Document ID: {doc_type.split()[0][:3].upper()}-999")
        else:
            print("\n  Cancelled.")

    elif "Route" in action:
        route_type = prompt_choice(
            "Route for which phase?",
            ["Pre-review", "Pre-approval", "Post-review", "Post-approval"],
            allow_quit=False
        )
        print(f"\n  [SIMULATED] Routed for {route_type}")

    else:
        print(f"\n  [SIMULATED] Action '{action}' would be executed here.")


def main():
    """Main entry point."""
    print("\n" + "=" * 50)
    print("  Multi-Step Prompt Experiment")
    print("=" * 50)
    print("\nThis script tests terminal interactivity patterns")
    print("for potential QMS CLI enhancements.")

    while True:
        mode = prompt_choice(
            "Select a demo mode:",
            [
                "Document workflow simulator",
                "Simple choice chain",
                "Text input with validation"
            ]
        )

        if mode is None:
            print("\nExiting. Goodbye!")
            break

        if mode == "Document workflow simulator":
            simulate_document_workflow()

        elif mode == "Simple choice chain":
            # Quick 3-step demo
            color = prompt_choice("Pick a color:", ["Red", "Green", "Blue"])
            if color:
                size = prompt_choice("Pick a size:", ["Small", "Medium", "Large"])
                if size:
                    confirm = prompt_confirm(f"You chose {color} and {size}. Confirm?")
                    print(f"\n  Result: {'Confirmed' if confirm else 'Cancelled'}")

        elif mode == "Text input with validation":
            name = prompt_text("Enter your name")
            email = prompt_text("Enter your email (optional)", required=False)
            print(f"\n  Name: {name}")
            print(f"  Email: {email or '(not provided)'}")

        # Ask to continue
        if not prompt_confirm("\nRun another demo?"):
            print("\nExiting. Goodbye!")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
        sys.exit(0)
