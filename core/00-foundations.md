# Foundations — Chat vs. Agent vs. API

**Video: coming soon**
**Status: outline**

---

## What you'll learn

Almost every bad AI project starts with the wrong one of these three. People reach for a chat window when they needed an agent, wire up an API when a chat window would have done, or build an agent for something that was really one deterministic script and a prompt. This lesson separates the three cleanly — as *concepts*, not products — so you can tell which one a piece of work actually calls for. A chat interface is a conversation where you are the loop: you read, you decide, you paste the next thing. An agent has its own loop: it plans, calls tools, observes what came back, and decides what to do next, repeatedly, until the goal is met or it stops. An API is raw model access you build your own loop around. Getting this distinction right is the difference between automation that survives contact with real work and a demo that impresses once.

---

## Key takeaways

- **The loop is the whole distinction.** Chat: *you* are the loop. Agent: the model runs its own loop with tools. API: you build the loop in code. Everything else follows from this.
- **Agents need three things to be useful** — tools to act with, context about your situation, and a definition of done. Missing any one of them produces confident motion in the wrong direction.
- **More autonomy is not better; it's a trade.** You're exchanging control and predictability for reach and unattended time. Choose the least autonomy that does the job.
- **Chat is still right for a huge amount of work.** One-off reasoning, thinking out loud, drafting — if you'd have to explain the task longer than doing it, don't build an agent for it.
- **Reach for the API when you need determinism at volume** — a fixed pipeline, a known schema, thousands of runs. The flexibility of an agent is dead weight there.

---

*Part of [Problem X Academy](../README.md) · [core/](.) · Next: [MCP, the protocol](01-mcp-protocol.md)*
