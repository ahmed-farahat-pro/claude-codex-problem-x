# Codex Automations

**Video: coming soon**
**Status: outline**

---

## What you'll learn

Codex's automation and plugin features for work that recurs or runs long. Two different shapes matter here and it's worth keeping them apart. **Recurring** work fires on a trigger — a schedule, a push, a new issue — and does a bounded job each time: the nightly dependency check, the automatic first-pass review on every PR, the weekly cleanup. **Long-running** work is one objective that continues across sessions until it's done, which is where the persisted [`/goal`](02-cloud-app-and-goals.md) workflow lives. This lesson covers setting up both, how they combine with cloud sandboxes so nothing depends on your laptop, how automations use your repo's skills to stay consistent with the house style, and how to keep output reviewable rather than producing a stream of PRs nobody reads.

---

## Key takeaways

- **Separate recurring from long-running.** A nightly bounded job and a week-long objective want different machinery; conflating them produces bad versions of both.
- **Trigger-based automations fit engineering rhythms** — on push, on PR, on issue, on schedule — because they attach to events your team already has.
- **Cloud execution removes the laptop dependency**, which is what makes an automation infrastructure rather than a habit.
- **Point automations at your skills** so unattended output matches what a reviewer expects. → [03-skills-in-practice.md](03-skills-in-practice.md)
- **Guard the review path.** Automation that generates more PRs than the team can read has moved the bottleneck, not removed it.
- **Watch the runs.** Long-running goals and recurring jobs both drift; periodic review is part of the design, not an afterthought. → [core/03-scheduled-agents-concept.md](../core/03-scheduled-agents-concept.md)

---

*Part of [Problem X Academy](../README.md) · [codex/](.) · Compare: [claude/05-routines-and-managed-agents.md](../claude/05-routines-and-managed-agents.md)*
