# The Model Context Protocol (MCP)

**Video: coming soon**
**Status: outline**

---

## What you'll learn

MCP is the answer to a problem that was quietly strangling agent adoption: every agent needed its own bespoke integration with every tool, so N agents times M systems meant N×M pieces of glue that nobody wanted to maintain. MCP replaces that with one open protocol — you write a server that exposes your system once, and any agent that speaks MCP can use it. This lesson covers MCP purely as a protocol: what a server exposes (tools the agent can call, resources it can read, prompts it can use), how a client and server talk over local and remote transports, how capability negotiation and authorization work, and why "it's a protocol, not a feature" is the single most important thing to understand about it. No vendor UI here — this is the layer that stays true whichever agent you end up running.

---

## Key takeaways

- **MCP turns N×M integrations into N+M.** One server per system, one client implementation per agent, and the two sides never need to know about each other.
- **A server exposes three things:** *tools* (actions the agent can invoke), *resources* (data it can read), and *prompts* (reusable instruction templates). Most of the value is in tools.
- **Transport is an implementation detail** — local processes over stdio for things on your machine, remote servers over HTTP for shared or hosted systems. The protocol is the same either way.
- **Authorization belongs to the server, not the agent.** The server decides what a caller may do; the agent just asks. Design it as if the caller might be wrong or confused, because sometimes it will be.
- **Portability is the payoff.** A well-built MCP server outlives your choice of agent — the same reason it's worth building carefully.
- **Tool descriptions are your real interface.** The agent picks tools by reading their descriptions; vague ones produce wrong calls no amount of model quality fixes.

---

*Part of [Problem X Academy](../README.md) · [core/](.) · In practice: [claude/04-mcp-connectors.md](../claude/04-mcp-connectors.md) · [codex/04-mcp-connectors.md](../codex/04-mcp-connectors.md)*
