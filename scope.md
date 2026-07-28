# Scope — Token Trace Viewer (v0.1)

## What it does

Reads the OpenInference spans from ONE agent run and tells you where the tokens went.

1. Per-sub-agent totals — input and output tokens grouped by agent.name, and within each agent, by step.
2. Cost ranking — every step in the run, sorted by dollar cost, highest first.
3. Repeated-context detection — flags context blocks sent more than once across steps, with repeat count and cost.

Command-line tool. Point it at a log file, get a table.

## What it does NOT do

- No live dashboard. No server, no web UI, no hosted anything. One command, text output.
- No trends over time. It explains a single run, not many runs across days. That is what LangSmith and Langfuse already do.
- No optimization suggestions. It shows a context block was resent nine times. It does not tell you how to fix it.
- No instrumentation. It does not wrap your LLM calls or collect traces. You bring a log; it reads it.
- Prices for one provider only, hardcoded in v0.1.
- OpenInference spans only. No framework-specific log formats.

## Why this exists

Checked five tools on 2026-07-27 (see `existence-check.md`).

LangSmith and Langfuse both ship per-step cost rankings, but as dashboard widgets that aggregate across many runs over a time window. Helicone can answer the question only if you tag every call yourself and write SQL. Phoenix shows cost per span and per project, with nothing in between. OpenInference defines every field needed — `agent.name`, `graph.node.name`, `llm.cost.total` — but is a spec, not a product.

Two gaps:

1. **Nothing explains a single run.** Every tool is a time-series dashboard. To learn why *this* run cost $4.20 you read the trace tree by eye.
2. **Nothing detects repeated context.** No tool flags identical context resent across steps.

## First ten users

| # | URL | What they said |
|---|-----|----------------|
| 1 | https://github.com/langchain-ai/langgraph/issues/8094 | Costs tripled; spent days chasing phantom regression |
| 2 | https://github.com/langchain-ai/langgraph/issues/7562 | Stable prefix replayed every turn, priced it |
| 3 | https://github.com/langchain-ai/langgraph/issues/7417 | Sub-agents silently re-run, 2-3x wasted cost |
| 4 | https://github.com/crewAIInc/crewAI/issues/1915 | wants per-agent tokens, not crew totals |

Found 4.

---

*Handle:* `rrkher059`
*Repo:* https://github.com/rrkher059-cloud/token-trace-viewer
*Written:* 2026-07-27
