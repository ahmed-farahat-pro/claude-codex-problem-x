# Routines and Managed Agents

**Video: coming soon**
**Status: outline**

---

## What you'll learn

[Cowork Scheduled Tasks](02-cowork-and-scheduled-tasks.md) cover recurring work for people without a terminal. This lesson covers the developer-side equivalents: **Claude Code Routines**, which put a repo-aware agent job on a cron schedule, and **Managed Agents** scheduled deployments, which run agents in the cloud on a schedule without your laptop being open. The distinction that matters is *where the job runs* — a routine tied to your machine dies when you close the lid; a cloud-run deployment doesn't. You'll learn how to define a scheduled job, how to give it the repo context and connectors it needs, how to get its output somewhere a human will see it, and how to keep an eye on runs so a job that's been quietly failing for three weeks doesn't stay quiet.

---

## Key takeaways

- **Routines put recurring agent work on a schedule** with the same repo context you'd have interactively — the natural home for nightly checks and weekly reports.
- **Managed Agents scheduled deployments run in the cloud**, so the job doesn't depend on your machine being awake. That's the difference between a habit and infrastructure.
- **Scheduled jobs need their context handed to them.** No one is there to answer a clarifying question — the prompt, the skills, and the connectors have to be complete up front.
- **Give it exactly the permissions it needs.** Unattended plus broad is the combination worth being careful about.
- **Make the output land somewhere human.** Chat, a PR, an issue, a doc — somewhere the result gets seen without anyone going to look for it.
- **Check the runs.** Schedule a periodic review of your schedules; drift is silent and cumulative. → [core/03-scheduled-agents-concept.md](../core/03-scheduled-agents-concept.md)

---

*Part of [Problem X Academy](../README.md) · [claude/](.) · Compare: [codex/05-automations.md](../codex/05-automations.md)*
