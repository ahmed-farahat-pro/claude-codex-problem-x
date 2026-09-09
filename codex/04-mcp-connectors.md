# MCP Connectors — Codex

**Video: coming soon**
**Status: outline**

---

## What you'll learn

Connecting Codex to your systems over MCP: configuring servers for the CLI, handling authorization, scoping servers per project or globally, and verifying the tools actually loaded before you start debugging a prompt that was never the problem. Because Codex's centre of gravity is the repo, the highest-value connectors tend to be the ones that surround it — issue trackers, CI, observability, deploy systems, internal service catalogs — the context an engineer holds in their head that the agent otherwise can't see. This lesson also covers what changes when agents run in **cloud sandboxes** rather than on your machine: which servers are reachable, how credentials get there safely, and why the answer for a local stdio server is different from a remote one.

---

## Key takeaways

- **Same protocol, same servers.** Anything you built for another MCP client works here — that's the point. → [core/01-mcp-protocol.md](../core/01-mcp-protocol.md)
- **The best Codex connectors surround the repo** — tickets, CI, logs, deploys. Give the agent the context you carry in your head.
- **Scope per project.** A repo-specific server belongs to that repo, not to your global config.
- **Cloud sandboxes change the reachability question.** Local stdio servers and remote HTTP servers behave differently once the agent isn't on your laptop; plan credentials accordingly.
- **Verify tools loaded first.** Most "the agent didn't use my connector" reports are a server that failed to start.
- **Enforce limits in the server.** Especially with parallel agents and higher approval modes, the server is the boundary that actually holds.

---

*Part of [Problem X Academy](../README.md) · [codex/](.) · Compare: [claude/04-mcp-connectors.md](../claude/04-mcp-connectors.md) · Examples: [mcp-examples/](../mcp-examples/)*
