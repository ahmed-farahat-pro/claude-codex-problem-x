# Codex CLI

**Video: coming soon**
**Status: outline**

---

## What you'll learn

The Codex CLI is where most Codex work starts, and the thing worth understanding first is its autonomy model. **Approval modes** control how much the agent does before checking with you — from confirming every command, through automatic execution inside a sandbox, to full autonomy. **Permission profiles** let you keep those settings coherent per context instead of re-answering the same prompts forever: tight on a production repo, loose on a scratch project. This lesson covers the CLI end to end — starting a session with the right repo context, choosing an approval mode honestly (the tempting answer is usually one notch too permissive), reading and steering work in progress, and building the habit of reviewing diffs rather than accepting them. It also covers where the CLI hands off to the cloud, and when that handoff is worth making.

---

## Key takeaways

- **Approval mode is the main dial.** Pick the least autonomy that gets the job done, and raise it deliberately rather than out of impatience.
- **Permission profiles keep it sane across projects** — different repos deserve different levels of trust, and profiles stop you re-deciding every session.
- **Sandboxing is what makes autonomy safe.** Understand what the agent can touch before you let it run unattended.
- **Repo context is the quality lever.** Point it at the right scope, give it the conventions, and output quality moves more than any prompt tweak will.
- **Review the diff, always.** Speed is the feature; unreviewed merges are the failure mode that follows it.
- **Know when to go to the cloud.** Long, parallel, or laptop-independent work belongs there. → [02-cloud-app-and-goals.md](02-cloud-app-and-goals.md)

---

*Part of [Problem X Academy](../README.md) · [codex/](.) · Compare: [claude/01-claude-code.md](../claude/01-claude-code.md)*
