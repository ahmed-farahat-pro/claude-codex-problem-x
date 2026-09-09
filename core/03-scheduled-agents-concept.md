# Scheduled Agents — The Concept

**Video: coming soon**
**Status: outline**

---

## What you'll learn

An agent you have to sit and watch is a better tool. An agent that runs on a schedule, without you, is a different category of thing — it's the point where automation stops being an assistant and starts being infrastructure. This lesson covers the general shape of a recurring autonomous job, independent of any platform: what makes a task a good candidate (recurring, well-defined, tolerant of a wrong answer once), how to define "done" when nobody is watching, what the job should do when it fails or when the world isn't what it expected, and how output should reach a human — because an unattended job that produces something nobody reads is just a cron entry burning tokens. It also covers the honest failure modes: silent drift, compounding errors, and the alert fatigue that turns a useful daily digest into something everyone filters away.

---

## Key takeaways

- **Good candidates are recurring, bounded, and forgiving.** If one wrong run causes real damage, it needs a human in the loop before it needs a schedule.
- **Define "done" before you define the cron.** An unattended job with a fuzzy finish line will find a fuzzy place to stop.
- **Design the failure path first.** What happens on a bad run, a changed input, an unreachable service? "It just won't work" is a decision too, and usually the wrong one.
- **The output is the product.** Route it where a human already looks — chat, inbox, a dashboard they open anyway. A perfect report in an unread folder is a failed job.
- **Watch for drift.** The world changes underneath a schedule: APIs move, formats shift, assumptions rot. Review the runs periodically or the job quietly becomes fiction.
- **Start attended, then let go.** Run it manually until it's boring, and only then put it on a clock.

---

*Part of [Problem X Academy](../README.md) · [core/](.) · In practice: [claude/05-routines-and-managed-agents.md](../claude/05-routines-and-managed-agents.md) · [codex/05-automations.md](../codex/05-automations.md)*
