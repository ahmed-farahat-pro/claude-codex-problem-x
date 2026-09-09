# Claude vs. Codex — A Decision Guide

**Video: coming soon**
**Status: outline**

---

## What you'll learn

This is not a rivalry piece and there is no winner at the bottom of it. Claude and Codex are both capable agent platforms that happen to have made different bets about where the work happens — and those bets are what should drive your choice, not benchmarks. This guide walks the axes that actually change your day: which surfaces each tool gives you, how each one models agents and subagents, how each handles MCP, the Agent Skills standard they share, what each offers for scheduled and recurring work, and how usable each is if you don't write code. Read it once before you invest a month learning one, then use the table at the end to pick a starting point. Most people who go deep eventually run both; almost nobody should start with both.

---

## Axis 1 — Primary surfaces

*Where the agent actually meets your work.*

**Claude** spreads wide across the places non-code work already happens:

- **Claude Code** — the terminal agent, also available in the desktop app, on the web, and in IDE extensions.
- **Cowork** — an agent workspace built for people who don't live in a terminal.
- **Claude in Chrome** — the agent driving a real browser session.
- **Excel and PowerPoint** — agent work inside the Office documents that carry most business output.
- **Claude Tag (Slack)** — the agent reachable from team chat, where requests already arrive.

**Codex** concentrates on depth around the repository:

- **Codex CLI** — the terminal agent, with approval modes and permission profiles.
- **Codex App** — a desktop client for running and managing several agents at once.
- **Codex Web / Cloud** — cloud sandboxes that clone your repo and work in parallel, with browser-based verification.

**The read:** Claude's surface area is *horizontal* — it reaches into documents, browsers, and chat, so the agent can meet work that was never going to happen in a terminal. Codex's surface area is *vertical* — nearly every surface is another way to point substantial engineering effort at a codebase. Neither is a limitation; they're aimed at different halves of the problem.

→ Detail: [claude/00-overview.md](claude/00-overview.md) · [codex/00-overview.md](codex/00-overview.md)

---

## Axis 2 — The agent and subagent model

*How work gets decomposed and delegated.*

- **Claude** leans on **subagents**: a main agent spawns specialized child agents with their own context windows and tool access, fans work out, and keeps only the conclusions. Combined with **hooks** (deterministic code fired at defined points in the loop) and **`CLAUDE.md`** (project config the agent reads on every run), you shape behavior in-repo rather than in a prompt.
- **Codex** leans on **parallel cloud tasks and persisted goals**: rather than one agent supervising children, you run several agents against sandboxed clones of the repo, each pursuing its own task, and manage the fleet from the App. The `/goal` workflow lets an objective persist across runs instead of dying with a session.

**The read:** Claude's model is *hierarchical* — one orchestrator, many specialists, one synthesized answer. Codex's model is *horizontal and durable* — many peers, isolated environments, objectives that outlive a session. Hierarchy suits "research this broadly, then act." Peers suit "try five approaches to the same hard problem" or "grind on this for a week."

→ Detail: [claude/01-claude-code.md](claude/01-claude-code.md) · [codex/02-cloud-app-and-goals.md](codex/02-cloud-app-and-goals.md)

---

## Axis 3 — MCP support

*How the agent reaches your systems.*

Both implement the **Model Context Protocol**, and this is the axis where the answer is genuinely boring: an MCP server you write works with either. That is the entire point of the protocol — the tool integration is not owned by the model vendor. Both support local (stdio) and remote servers; both need per-server authorization; both let you connect an existing server in minutes and write a custom one in an afternoon.

The differences are ergonomic, not architectural: how servers are configured and scoped, how OAuth flows are handled, how connectors surface to non-technical users, and which first-party connectors ship out of the box. Claude's breadth of surfaces means an MCP connector can end up usable from Cowork or Slack, not just a terminal — which matters more than it sounds if the people who need the integration aren't engineers.

**The read:** Don't pick a tool for MCP. Pick it for the surfaces, then bring your MCP servers along.

→ Detail: [core/01-mcp-protocol.md](core/01-mcp-protocol.md) · [claude/04-mcp-connectors.md](claude/04-mcp-connectors.md) · [codex/04-mcp-connectors.md](codex/04-mcp-connectors.md)

---

## Axis 4 — Agent Skills (the shared `SKILL.md` standard)

*How expertise becomes portable.*

A skill is a folder with a `SKILL.md` file: frontmatter naming the skill and describing when to use it, then instructions the agent loads only when relevant. It is an **open standard**, and the same skill folder works across **Claude Code, Codex CLI, Cursor, and Gemini CLI**.

This is the most underrated fact in this entire guide. Your accumulated house style, review checklists, deploy runbooks, and domain rules are **not** locked to a vendor. If you write your team's expertise as skills, switching tools — or running both — costs you nothing on that front.

Where the tools differ is in the surrounding workflow: how skills are discovered and installed, whether there's a guided creator, how they're scoped per-project or per-user, and how they interact with each tool's own agent model. The content in the middle is shared.

**The read:** Invest in skills early and invest in them once. It's the least vendor-locked thing you can build.

→ Detail: [core/02-skills-standard.md](core/02-skills-standard.md) · [claude/03-skills-in-practice.md](claude/03-skills-in-practice.md) · [codex/03-skills-in-practice.md](codex/03-skills-in-practice.md)

---

## Axis 5 — Scheduled and recurring work

*Getting the job to run without you.*

- **Claude** offers **Cowork Scheduled Tasks** for recurring work in the non-developer workspace, and **Claude Code Routines** plus **Managed Agents** scheduled deployments for cloud-run recurring jobs. The spread means a scheduled job can be set up by someone who has never opened a terminal, or defined in-repo by someone who lives in one.
- **Codex** offers **automations** for recurring and long-running work, and the persisted **`/goal`** workflow for objectives that continue across sessions rather than firing on a clock.

**The read:** Claude's scheduling is broader in *who* can set it up. Codex's is deeper in *how long a single objective can run*. A daily digest for a marketing team and a week-long refactor are both "recurring autonomous work," and they want different machinery.

→ Detail: [core/03-scheduled-agents-concept.md](core/03-scheduled-agents-concept.md) · [claude/05-routines-and-managed-agents.md](claude/05-routines-and-managed-agents.md) · [codex/05-automations.md](codex/05-automations.md)

---

## Axis 6 — Non-developer usability

*Can someone who doesn't write code get real value?*

This is the sharpest split on the list.

**Claude** treats non-developers as a first-class audience. Cowork exists specifically so someone can direct an agent without a terminal. The Excel and PowerPoint surfaces meet finance, ops, and consulting work in the file formats those jobs already run on. Claude in Chrome handles the browser-based drudgery that never had an API. Claude Tag puts the agent in Slack, where requests already arrive. A lawyer, a recruiter, or an analyst can get durable value here without learning git.

**Codex** assumes a repository. The CLI, the sandboxes, the goals, the browser verification — the whole design presumes code under version control and someone who can read a diff. That's not a gap, it's a focus: for people who *do* have that context, the depth is the reason to use it.

**The read:** If the person doing the work doesn't have a repo, that answers the question.

---

## Where to start, by profession

| Profession | Start with | Why |
|---|---|---|
| **Full-stack / backend engineer** | **Codex**, add Claude | Repo-native depth, parallel cloud tasks, and long-running goals fit real engineering work; add Claude Code for subagent research and hooks. → [tracks/fullstack](tracks/fullstack/) |
| **Frontend / product engineer** | **Either** — try Claude first | Claude's browser surface helps verify what you built; Codex's sandboxes shine once the work is repo-heavy |
| **DevOps / platform** | **Codex**, add Claude Routines | Long-running goals suit migrations and refactors; Claude Routines cover scheduled cloud jobs |
| **Data analyst** | **Claude** | Excel is where the work already lives; MCP connectors reach the warehouse |
| **Marketer / content** | **Claude** | Cowork + Scheduled Tasks + PowerPoint cover briefs, decks, and recurring reporting without a terminal |
| **Founder / operator** | **Claude** | Broadest surface coverage across the scattered work a small team actually has |
| **Consultant / analyst** | **Claude** | PowerPoint and Excel surfaces map directly onto the deliverables |
| **Lawyer / compliance** | **Claude** | Document-centric work, plus Skills to encode review checklists once |
| **Recruiter / ops** | **Claude** | Cowork and Chrome handle the browser drudgery that has no API |
| **Researcher / academic** | **Claude** | Subagent fan-out for literature sweeps; Skills to encode methodology |
| **Technical founder with a codebase** | **Both** — Codex first | Codex for the product, Claude for everything around it |

Tracks turn these rows into actual paths, pulling from both `/claude/` and `/codex/` as each step needs. → [tracks/README.md](tracks/README.md)

---

## Key takeaways

- **Surfaces decide more than capability.** Both tools are strong; the question is whether the agent can reach where your work happens.
- **The agent models differ in shape, not quality** — Claude's hierarchical subagents vs. Codex's parallel sandboxed peers.
- **MCP is shared.** Your connectors are portable. Don't let it drive the decision.
- **Skills are shared too** — `SKILL.md` works across Claude Code, Codex CLI, Cursor, and Gemini CLI. Write your expertise once.
- **Non-developer access is the real dividing line.** No repo, no terminal → start with Claude. Repo-native engineering depth → start with Codex.
- **Start with one.** Learn it properly, then add the second where it obviously wins.

---

*Part of [Problem X Academy](README.md) — free, open source, updated daily.*
