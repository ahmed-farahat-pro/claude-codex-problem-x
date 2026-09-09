# Claude Code — The Terminal Agent

**Video: coming soon**
**Status: outline**

---

## What you'll learn

Claude Code is the agent for work that lives in a repository, and this lesson covers the four things that separate a productive setup from a frustrating one. **Subagents** let the main agent fan work out to specialists with their own context windows — you get the conclusion without the file dumps, which is the difference between a broad search that works and one that fills your context with noise. **Hooks** are deterministic code fired at defined points in the agent loop, so the things that must always happen (format, lint, block a dangerous command) happen every time rather than usually. **`CLAUDE.md`** is project config the agent reads on every run: conventions, architecture notes, the commands that actually work in your repo. And the permission model governs what runs without asking. Get these four right and the agent stops feeling like a clever autocomplete and starts feeling like a teammate who's read the codebase.

---

## Key takeaways

- **Subagents are for fan-out, not delegation theatre.** Use them when answering means sweeping many files and you want the conclusion, not the excerpts. Each gets its own context; only the result comes back.
- **`CLAUDE.md` is the highest-leverage file in your repo.** Conventions, build and test commands, architecture, gotchas. Every correction you find yourself repeating belongs in it.
- **Hooks make the non-negotiable actually non-negotiable.** Formatting, linting, and guardrails that fire deterministically beat instructions the agent might follow.
- **Skills carry the judgment.** House review standards, deploy runbooks, and domain rules go in `SKILL.md` files — portable to other tools. → [03-skills-in-practice.md](03-skills-in-practice.md)
- **Tune permissions once, deliberately.** Auto-approve the safe and repetitive, keep confirmation on anything destructive or outward-facing.
- **It's not only a terminal.** The same agent runs in the desktop app, on the web, and in IDE extensions.

---

*Part of [Problem X Academy](../README.md) · [claude/](.) · Compare: [codex/01-codex-cli.md](../codex/01-codex-cli.md)*
