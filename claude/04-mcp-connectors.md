# MCP Connectors — Claude

**Video: coming soon**
**Status: outline**

---

## What you'll learn

Two halves, in the order that makes sense. First, **connecting a server that already exists**: adding it in Claude Code or the desktop app, handling the authorization flow, scoping it to a project or your whole account, and confirming the tools actually landed — plus what to do when they didn't. Most people's first genuinely useful agent moment happens here, when the agent can suddenly read their tickets or query their warehouse. Second, **building a minimal custom server**: the smallest thing that exposes one real tool from your own system, why you should start with one tool rather than twenty, and how to write descriptions the agent can actually choose between. By the end you'll be able to reach any system your team runs, whether or not anyone has published a connector for it.

---

## Key takeaways

- **Connect before you build.** There's an existing server for a surprising amount; borrow first and learn the shape.
- **Scope matters** — project-level for repo-specific systems, user-level for tools you use everywhere. Getting this wrong is how a config drifts into a mess.
- **Verify the tools loaded** before debugging your prompt. Half of "the agent ignored my connector" is a server that never started.
- **Start a custom server with exactly one tool.** One real, useful, well-described tool beats a wide surface of vague ones.
- **Descriptions are the interface.** The agent selects tools by reading them; ambiguity there shows up as wrong calls downstream.
- **The server enforces its own limits.** Never rely on the agent to stay inside a boundary you could enforce in code.
- **It's portable.** The same server works with Codex and anything else speaking MCP. → [codex/04-mcp-connectors.md](../codex/04-mcp-connectors.md)

---

*Part of [Problem X Academy](../README.md) · [claude/](.) · Concept: [core/01-mcp-protocol.md](../core/01-mcp-protocol.md) · Examples: [mcp-examples/](../mcp-examples/)*
