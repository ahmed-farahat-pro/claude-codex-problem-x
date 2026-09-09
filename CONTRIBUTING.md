# Contributing to Problem X Academy

This repo is **not going to be written by one person, by design.** No single person uses every surface of both tools in every profession, and pretending otherwise is how courses end up confidently wrong about half their material. Corrections and contributions from people doing the actual work are the mechanism that keeps this accurate — they're the plan, not a fallback.

PRs are welcome. Here's what's most useful.

---

## 1. Corrections

The highest-value contribution in the repo. Both Claude and Codex ship constantly, and anything written today can be wrong in a month.

Open a PR — or an issue if you're not sure of the fix — for:

- A step, flag, or menu path that has changed
- Something described inaccurately
- A broken link or a dead reference
- A claim in [claude-vs-codex.md](claude-vs-codex.md) that's no longer true because a gap got closed

**Please include how you verified it** — a version number, a date, a link. "This is wrong" is a start; "this changed in version X, here's the current behavior" is a merge.

---

## 2. New MCP and skill examples

Working examples are what turn an outline into something usable.

- MCP servers and connector configs → [`/mcp-examples/`](mcp-examples/)
- `SKILL.md` examples → [`/skills/`](skills/)

**Tag every example** with where it's been verified:

| Tag | Use when |
|---|---|
| 🟣 **Claude** | It relies on a Claude-specific surface, tool, or config |
| 🟢 **Codex** | It relies on something Codex-specific |
| 🔵 **Both** | It's been run on both, or it's pure `SKILL.md` / plain MCP with no client-specific parts |

Only tag 🔵 Both if you've actually run it on both. An honest 🟣 that someone else ports is far more useful than an optimistic 🔵 that breaks.

**Keep examples minimal.** One server that does one real thing well beats a framework. Include a short README saying what problem it solves and how to run it.

---

## 3. Translations

If this material is useful in your language, translating it makes it useful to a lot more people. Open an issue first so two people don't translate the same file into the same language on the same weekend.

- Mirror the existing structure under a language folder (e.g. `/ar/core/00-foundations.md`)
- Keep filenames identical so links stay predictable
- Translate the meaning, not the words — examples can be localized where that helps

---

## 4. Daily update posts

[`/updates/`](updates/) is a running log of what changed and what shipped in either tool. Posts are welcome if you've been close to something.

- Filename: `YYYY-MM-DD-short-slug.md`
- Open with a title, the date, and who wrote it
- Say what changed and why anyone should care — link the lesson it affects
- Short is fine. A useful paragraph beats a padded page.

---

## How to submit

1. Fork and branch (`fix/mcp-scope-wording`, `add/jira-mcp-example`)
2. Make the change — one topic per PR, please
3. Check your links resolve
4. Open the PR and say what changed and how you verified it

No CLA, no template to fill in, no style guide to memorize. Match the surrounding tone: direct, concrete, no hype.

---

## What gets declined

Only a few things, and none of them personally:

- Vendor marketing copy for either tool
- Content that picks a side rather than helping someone decide — [claude-vs-codex.md](claude-vs-codex.md) is a decision guide, not a scoreboard
- Examples that can't be run or verified
- Large unrequested restructures — open an issue first and let's talk

---

Everything here is MIT licensed. By contributing, you agree your contribution ships under the same terms. → [LICENSE](LICENSE)

---

*[Problem X Academy](README.md) · [problem-x.com](https://problem-x.com)*
