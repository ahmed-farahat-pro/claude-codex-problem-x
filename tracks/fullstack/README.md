# Track: Full-Stack Engineering

**Video: coming soon**
**Status: outline**

---

## What you'll learn

This track is for engineers who ship features end to end and want agents doing real work rather than autocompleting lines. It moves through three stages, drawing on Codex and Claude wherever each is genuinely stronger. **Multi-agent orchestration** — decomposing work so several agents run in parallel without colliding, using Codex's cloud sandboxes for isolated attempts and Claude Code's subagents for research fan-out, and knowing which shape fits which problem. **Code review agents** — encoding your team's standards as skills so review is consistent, catching the specific things agents get wrong (over-broad changes, plausible-looking tests, silent scope creep), and keeping a human in the loop where it matters. **Deploy pipelines** — agents in CI, automated checks that fire on push, scheduled maintenance jobs, and the guardrails that make unattended work safe to merge.

The case study is **[Nigents](https://problem-x.com)**, a real multi-agent project — not a to-do app. You'll see the actual orchestration decisions, the review setup that keeps agent output shippable, and the pipeline it deploys through, including the parts that went wrong first.

---

## Key takeaways

- **Decomposition is the skill.** Multi-agent work fails at the split, not the execution — badly split tasks produce agents that duplicate, conflict, or wait on each other.
- **Two orchestration shapes, two jobs.** Codex's parallel sandboxes for independent attempts at one hard problem; Claude Code's subagents for fanning out research and getting one synthesized answer. → [codex/02-cloud-app-and-goals.md](../../codex/02-cloud-app-and-goals.md) · [claude/01-claude-code.md](../../claude/01-claude-code.md)
- **Review is the bottleneck once agents write faster than you read.** Encode standards as skills so the first pass is consistent and your attention goes to what actually needs judgment. → [core/02-skills-standard.md](../../core/02-skills-standard.md)
- **Automate the pipeline, not the judgment.** Checks, tests, and formatting run unattended; merge decisions stay human until the track's guardrails are in place. → [codex/05-automations.md](../../codex/05-automations.md) · [claude/05-routines-and-managed-agents.md](../../claude/05-routines-and-managed-agents.md)
- **Connectors give agents the context you carry in your head** — tickets, CI, logs, deploys. Without them the agent is reasoning about a codebase in a vacuum. → [core/01-mcp-protocol.md](../../core/01-mcp-protocol.md)
- **Case study: Nigents.** A real multi-agent system, including the orchestration choices that had to be redone.

---

## Track outline

| # | Stage | Primary tool | Supporting material |
|---|---|---|---|
| 1 | Setup and repo context | Codex CLI + Claude Code | [codex/01](../../codex/01-codex-cli.md) · [claude/01](../../claude/01-claude-code.md) |
| 2 | Encoding house standards as skills | Both | [core/02](../../core/02-skills-standard.md) · [skills/](../../skills/) |
| 3 | Wiring connectors (tickets, CI, logs) | Both | [core/01](../../core/01-mcp-protocol.md) · [mcp-examples/](../../mcp-examples/) |
| 4 | Multi-agent orchestration | Codex Cloud + App | [codex/02](../../codex/02-cloud-app-and-goals.md) |
| 5 | Research fan-out with subagents | Claude Code | [claude/01](../../claude/01-claude-code.md) |
| 6 | Code review agents | Both | [claude/03](../../claude/03-skills-in-practice.md) · [codex/03](../../codex/03-skills-in-practice.md) |
| 7 | Deploy pipelines and scheduled maintenance | Both | [codex/05](../../codex/05-automations.md) · [claude/05](../../claude/05-routines-and-managed-agents.md) |
| 8 | Case study: Nigents end to end | Both | — |

---

*Part of [Problem X Academy](../../README.md) · [tracks/](../) · Which tool when: [claude-vs-codex.md](../../claude-vs-codex.md)*
