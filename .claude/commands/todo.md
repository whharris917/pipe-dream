---
description: Add an item to the to-do list
allowed-tools: Read, Edit
argument-hint: <task description>
---

Add the following item to `.claude/TO_DO_LIST.md`:

**Task:** $ARGUMENTS

Instructions:
1. Read the current TO_DO_LIST.md file (create it if it doesn't exist)
2. Add a new checkbox item: `- [ ] <task description>`
3. If the task has sub-components or notes, add them as indented bullets
4. Keep entries concise and actionable
