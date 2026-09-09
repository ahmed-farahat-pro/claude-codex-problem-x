# The Agent Skills Standard (`SKILL.md`)

**Video: coming soon**
**Status: outline**

---

## What you'll learn

A skill is a folder containing a `SKILL.md` file: YAML frontmatter that names the skill and — critically — describes *when it should be used*, followed by instructions the agent loads only when that moment arrives. That's the whole format. Its importance is out of all proportion to its simplicity, for two reasons. First, it solves context economy: instead of stuffing every rule your team has into one enormous prompt, the agent carries short descriptions and pulls in full instructions on demand. Second, it's an **open standard** that works across **Claude Code, Codex CLI, Cursor, and Gemini CLI** — so the expertise you encode is portable rather than locked to whoever you're using this quarter. This lesson covers the anatomy of a skill, what belongs in one versus what belongs in an MCP server, and why the description line does most of the work.

---

## Key takeaways

- **The format is deliberately tiny** — a folder, a `SKILL.md`, frontmatter plus instructions. Supporting files and scripts live alongside it and are referenced as needed.
- **The description field is the whole trigger.** The agent decides whether to load a skill by reading its description, so write it as *when to use this*, not *what this is*.
- **Progressive disclosure is the point.** Descriptions stay loaded; bodies load on demand. That's what lets you have fifty skills without drowning the context window.
- **Skills encode judgment; MCP servers provide capability.** "How we review a PR" is a skill. "Talk to our ticketing system" is an MCP server. Confusing the two produces bad versions of both.
- **It's cross-tool by design** — the same folder works in Claude Code, Codex CLI, Cursor, and Gemini CLI. This is the least vendor-locked investment available to you.
- **Version them like code.** Skills live in the repo, get reviewed in PRs, and improve when someone hits a rough edge and fixes it for everyone.

---

*Part of [Problem X Academy](../README.md) · [core/](.) · In practice: [claude/03-skills-in-practice.md](../claude/03-skills-in-practice.md) · [codex/03-skills-in-practice.md](../codex/03-skills-in-practice.md) · Examples: [skills/](../skills/)*
