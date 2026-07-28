# Existence check — per-subagent token attribution, ranked by cost

**Question:** does the tool show token/dollar totals grouped by SUB-AGENT, ordered by cost?
**Pass:** shipped view + sub-agent-level dimension + proof URL. No URL = NO. Tags-only = NO.
**Run:** Mon Jul 27, 18:30–19:30 box.

| Tool | Y/N | Proof URL | Note |
|---|---|---|---|
| LangSmith | YES | https://docs.smith.langchain.com/observability/how_to_guides/dashboards | Custom dashboard: group by Run Name + metric Cost (Sum) + ranked bar/table = per-sub-agent cost ranking. Native attribute, no custom tags. Top-20 cap. Cross-trace time-series only — no per-run breakdown. Cloud US. |
| Helicone | NO (tags-only) | https://docs.helicone.ai/features/hql#in-the-dashboard | HQL = arbitrary SQL over request_response_rmt. Group-by examples are request_model. Sub-agent only via custom properties you attach + your own query. No shipped view. Cost stored ×1e9. |
| Langfuse | YES | https://langfuse.com/docs/metrics/features/custom-dashboards | Widgets: data source = observations, dimension = name, metric = cost, bar chart → per-step cost ranking. Same shape as LangSmith. Dashboard-level, not per-run. |
| Phoenix / Arize | NO | https://arize.com/docs/phoenix/tracing/how-to-tracing/cost-tracking | Shows cost per trace, per span, per session, per experiment, per project. No grouping by span name, no ranking. "Most expensive models" still marked coming-soon. |
| OTel LLM tracing | NO (tags-only) | https://arize-ai.github.io/openinference/spec/semantic_conventions.html | Spec, not a product — no UI, so no ranking by definition. But the fields all exist and are standard: agent.name, graph.node.name, graph.node.parent_id, llm.cost.total, llm.token_count.*. |

## Verdict
LangSmith and Langfuse both ship per-step cost rankings via dashboard widgets, but all five are cross-trace time-series tools: none breaks down a single run, and none flags identical context resent across steps. Building that — a CLI that reads OpenInference spans and ranks one run, with repeated-context detection.
