---
description: Add an idea to the idea tracker
allowed-tools: Read, Edit
argument-hint: <idea title or description>
---

Add the following idea to `.claude/notes/IDEA_TRACKER.md`:

**Idea:** $ARGUMENTS

Instructions:
1. Read the current IDEA_TRACKER.md file
2. Find today's date section (format: `## YYYY-MM-DD`). If it doesn't exist, create it after the `---` following the header.
3. Add a new `### <Idea Title>` subsection under today's date
4. Write a brief description based on what the user provided
5. If the idea warrants discussion points or considerations, add them
6. End with `---` separator

Keep entries concise but capture the essence of the idea.
