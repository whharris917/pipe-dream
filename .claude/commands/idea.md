---
description: Add an idea to the idea tracker
allowed-tools: Read, Edit
argument-hint: <idea title or description>
---

Add the following idea to `.claude/IDEA_TRACKER.md`:

**Idea:** $ARGUMENTS

Instructions:
1. Check if `.claude/IDEA_TRACKER.md` exists. If not, create it with this header:
   ```markdown
   # Idea Tracker

   Ideas and concepts captured during sessions.

   ---
   ```
2. Read the current IDEA_TRACKER.md file
3. Find today's date section (format: `## YYYY-MM-DD`). If it doesn't exist, create it after the last `---` separator.
4. Add a new `### <Idea Title>` subsection under today's date
5. Write a brief description based on what the user provided
6. If the idea warrants discussion points or considerations, add them
7. End with `---` separator

Keep entries concise but capture the essence of the idea.
