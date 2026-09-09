# Skills in Practice — Codex

**Video: coming soon**
**Status: outline**

---

## What you'll learn

The same `SKILL.md` standard, running inside Codex. This lesson is deliberately structured around one question: **what's shared and what's Codex-specific?** The shared part is most of it — the folder layout, the frontmatter, the description-triggers-loading behavior, and the content itself. A skill written for Claude Code works here, which is the whole promise of an open standard. The Codex-specific part is the surrounding workflow: where skills live and how they're discovered, how they're scoped, and — the interesting bit — how they behave when several agents run in parallel across cloud sandboxes, where a skill becomes the mechanism that keeps five independent agents producing consistent work. You'll also learn how skills interact with approval modes and goals.

---

## Key takeaways

- **The format is identical.** Same `SKILL.md`, same frontmatter, same progressive disclosure — a skill folder is genuinely portable. → [core/02-skills-standard.md](../core/02-skills-standard.md)
- **Codex-specific is the plumbing**, not the content: discovery, scoping, and how skills reach cloud sandboxes.
- **Skills are how you keep parallel agents consistent.** With several agents on one problem, shared skills are what stop five different house styles coming back.
- **Commit them to the repo.** Skills in version control get reviewed, improved, and inherited by every agent and teammate who clones it.
- **Encode review standards early.** When the agent writes more than you read, the review checklist is the highest-leverage skill you own.
- **Write once, run everywhere** — Claude Code, Codex CLI, Cursor, Gemini CLI. → [claude/03-skills-in-practice.md](../claude/03-skills-in-practice.md)

---

*Part of [Problem X Academy](../README.md) · [codex/](.) · Examples: [skills/](../skills/)*
