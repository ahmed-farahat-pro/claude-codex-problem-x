<div align="center">

# Problem X Academy

### A free, always-updating course on building with **Claude** and **Codex**

**MCP · Agents · Skills · Scheduled Automation**

[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg?style=flat-square)](LICENSE)
[![Updated Daily](https://img.shields.io/badge/updated-daily-brightgreen.svg?style=flat-square)](updates/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-blue.svg?style=flat-square)](CONTRIBUTING.md)
[![Built by Problem X](https://img.shields.io/badge/built%20by-Problem%20X-orange.svg?style=flat-square)](https://problem-x.com)

[Start here](#-start-here) · [Claude vs. Codex](claude-vs-codex.md) · [Daily updates](updates/) · [Contribute](CONTRIBUTING.md) · [problem-x.com](https://problem-x.com)

</div>

---

## What this is

**Problem X Academy is a free, open-source course on actually using AI agents — not watching demos of them.** It covers the two tools doing the most serious work right now, Claude and Codex, and it covers them side by side: the Model Context Protocol that lets agents talk to your systems, the Agent Skills standard that makes expertise portable between them, the agent and subagent models each one uses, and how to put a job on a schedule so it runs without you. Everything lives here in the open, gets corrected in public, and updates daily as both tools ship. Built by [Ahmed Farahat / Problem X](https://problem-x.com). No paywall, no email gate, no course platform — just a repo you can clone, read, and send a PR to.

---

## 🚀 Start here

| If you are… | Go to |
|---|---|
| Brand new to agents | [core/00-foundations.md](core/00-foundations.md) |
| Deciding which tool to learn first | [claude-vs-codex.md](claude-vs-codex.md) |
| A developer who lives in the terminal | [codex/01-codex-cli.md](codex/01-codex-cli.md) · [claude/01-claude-code.md](claude/01-claude-code.md) |
| Not a developer, but drowning in repetitive work | [claude/02-cowork-and-scheduled-tasks.md](claude/02-cowork-and-scheduled-tasks.md) |
| Here to automate one specific recurring job | [core/03-scheduled-agents-concept.md](core/03-scheduled-agents-concept.md) |
| Trying to apply this to your own profession | [core/04-adapt-to-your-job.md](core/04-adapt-to-your-job.md) · [tracks/](tracks/) |

---

## 🗂 How this repo is organized

The material is split four ways on purpose, so you can learn a concept once and then apply it in whichever tool you actually use.

### `/core/` — tool-agnostic concepts

The ideas that outlive any particular product. What an agent *is* as distinct from a chat window or an API call. What MCP is as a **protocol**, independent of who implements it. The `SKILL.md` standard as an open spec. What a recurring autonomous job means in the abstract. Deliberately free of UI steps — nothing here goes stale when a menu moves.

### `/claude/` and `/codex/` — deep dives per tool

Where the concepts meet real surfaces. [`/claude/`](claude/) covers Claude Code, Cowork and Scheduled Tasks, Skills, MCP connectors, Routines and Managed Agents. [`/codex/`](codex/) covers the Codex CLI, the desktop App, Web/Cloud sandboxes and goals, Skills, MCP, and automations. Same lesson shape on both sides, so you can read them in parallel and see exactly where the two diverge.

### `/claude-vs-codex.md` — the decision guide

Not a rivalry piece. An axis-by-axis breakdown — surfaces, agent model, MCP support, Skills, scheduling, non-developer usability — ending in a table that maps a profession to the tool worth starting with, and why. → [Read it](claude-vs-codex.md)

### `/tracks/` — profession-specific application

Concepts and tools assembled into a path for a particular kind of work, pulling from `/claude/` and `/codex/` as each step demands. [Full-stack](tracks/fullstack/) is first; more get added based on real demand. → [How tracks work](tracks/README.md)

Plus two example libraries that fill in as lessons ship: [`/skills/`](skills/) for working `SKILL.md` examples and [`/mcp-examples/`](mcp-examples/) for runnable MCP servers and connector configs — each tagged Claude, Codex, or both.

---

## 📁 Repo structure

```text
problemx-academy/
├── README.md                          ← you are here
├── claude-vs-codex.md                 ← decision guide: which tool, when
├── CONTRIBUTING.md
├── LICENSE
│
├── core/                              ← tool-agnostic concepts
│   ├── 00-foundations.md                 chat vs. agent vs. API
│   ├── 01-mcp-protocol.md                MCP as a protocol
│   ├── 02-skills-standard.md             the SKILL.md open standard
│   ├── 03-scheduled-agents-concept.md    recurring autonomous jobs
│   └── 04-adapt-to-your-job.md           the reusable framework
│
├── claude/                            ← deep dive: Claude
│   ├── 00-overview.md                    surfaces, and when to start here
│   ├── 01-claude-code.md                 terminal agent, subagents, hooks
│   ├── 02-cowork-and-scheduled-tasks.md  non-dev workspace + recurring work
│   ├── 03-skills-in-practice.md          building & installing skills
│   ├── 04-mcp-connectors.md              connect, then build an MCP server
│   └── 05-routines-and-managed-agents.md cloud-run recurring jobs
│
├── codex/                             ← deep dive: Codex
│   ├── 00-overview.md                    surfaces, and when to start here
│   ├── 01-codex-cli.md                   approval modes, permission profiles
│   ├── 02-cloud-app-and-goals.md         sandboxes, /goal, the desktop App
│   ├── 03-skills-in-practice.md          SKILL.md inside Codex
│   ├── 04-mcp-connectors.md              connecting MCP servers to Codex
│   └── 05-automations.md                 recurring & long-running work
│
├── tracks/                            ← profession-specific paths
│   ├── README.md
│   └── fullstack/
│       └── README.md
│
├── skills/                            ← worked SKILL.md examples
│   └── README.md
├── mcp-examples/                      ← worked MCP server examples
│   └── README.md
└── updates/                           ← daily changelog & posts
    └── 2026-09-09-repo-is-live.md
```

---

## 📅 Daily updates

This repo changes most days — new lessons, corrections, and notes on what shipped in Claude or Codex that week. Every update is a dated post in **[`/updates/`](updates/)**. Watch the repo to get them, or just read the folder newest-first.

Latest: **[2026-09-09 — The repo is live](updates/2026-09-09-repo-is-live.md)**

---

## 🤝 Contributing

Corrections, new MCP and skill examples, translations, and update posts are all welcome — this repo is not meant to be written by one person. See **[CONTRIBUTING.md](CONTRIBUTING.md)** for how to tag an example (Claude, Codex, or both) and what makes a good PR.

---

## 🔮 Coming soon: the AI concierge

> **Placeholder.** An AI concierge is being built for problem-x.com: you describe your job and the recurring work that eats your week, and it points you at the exact lessons, tools, and tracks worth your time — then keeps you posted as new ones land. What people actually ask it will decide which tracks get built next. Not live yet; this section becomes a link when it is.

---

## 📊 Status

Every lesson carries a status line. Right now most read **`Status: outline`** with **`Video: coming soon`** — the structure is set, the depth and the video walkthroughs land lesson by lesson. Nothing is hidden behind a "premium" tier; when a lesson is done, it is done here.

---

<div align="center">

**[problem-x.com](https://problem-x.com)** · Built in the open by Ahmed Farahat

*Free forever. MIT licensed. Updated daily.*

</div>
