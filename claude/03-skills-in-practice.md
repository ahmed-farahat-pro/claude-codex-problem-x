# Skills in Practice — Claude

**Video: coming soon**
**Status: outline**

---

## What you'll learn

The [standard](../core/02-skills-standard.md) is simple; the craft is in what you put in a skill and how you know it's working. This lesson is the Claude-specific workflow end to end: using **Skill Creator** to go from "here's how we do code review" to a working skill without hand-writing frontmatter, installing skills at the right scope (personal vs. project, so a team gets them by cloning the repo), invoking them explicitly versus letting the description trigger them, and debugging the most common failure — a skill that exists but never fires, which is almost always a description that says *what it is* instead of *when to use it*. You'll also learn where the line sits between a skill and a `CLAUDE.md` entry, and how skills interact with subagents.

---

## Key takeaways

- **Skill Creator is the fastest path in** — describe the workflow in plain language, get a properly structured skill, then refine the description until it triggers reliably.
- **Scope deliberately.** Project-scoped skills ship with the repo and give the whole team the same behavior; personal skills follow you across projects.
- **"It never triggers" is a description bug.** Rewrite it as the situation the agent will find itself in, using the words that will actually be in the request.
- **Keep the body short and the references separate.** Long procedures and examples belong in files the skill points to, loaded only when needed.
- **`CLAUDE.md` for always-on facts, skills for situational procedures.** Conventions the agent needs every run go in config; "when doing X, do it this way" goes in a skill.
- **They're portable.** The same folder works in Codex CLI, Cursor, and Gemini CLI — write it once. → [codex/03-skills-in-practice.md](../codex/03-skills-in-practice.md)

---

*Part of [Problem X Academy](../README.md) · [claude/](.) · Standard: [core/02-skills-standard.md](../core/02-skills-standard.md) · Examples: [skills/](../skills/)*
