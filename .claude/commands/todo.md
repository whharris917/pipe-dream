---
description: Add an item to the to-do list
allowed-tools: Read, Edit
argument-hint: <task description>
---

Add the following item to `.claude/TO_DO_LIST.md`:

**Task:** $ARGUMENTS

Instructions:
1. Check if `.claude/TO_DO_LIST.md` exists. If not, create it with this header:
   ```markdown
   # To-Do List

   Tasks and action items.

   ---
   ```
2. Read the current TO_DO_LIST.md file
3. Add a new checkbox item: `- [ ] <task description>`
4. If the task has sub-components or notes, add them as indented bullets
5. Keep entries concise and actionable
