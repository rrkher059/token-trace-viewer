# token-trace-viewer

When your agent run costs more than you expected, this tells you which sub-agent spent it, and how much you paid to resend the same context.

## What it does

- Per-sub-agent totals — input and output tokens grouped by agent, then by step.
- Cost ranking — every step in the run, sorted by dollar cost, highest first.
- Repeated-context detection — flags context blocks sent more than once across steps, with repeat count and estimated wasted tokens.

## Install

Requires Python 3.10+ (the code uses `str | None` union syntax). No dependencies — standard library only.
`tools/` has its own dependencies (see `tools/README.md`) for reproducing a real trace; the tool itself still has none.

## Run it

```
git clone https://github.com/rrkher059/token-trace-viewer.git
cd token-trace-viewer
python3 ttv.py sample.jsonl
```

On Windows, use `py ttv.py sample.jsonl` instead of `python3`.

The tool reads OpenInference spans as JSONL, one span per line, so it should
work against anything that exports that format — Phoenix, Langfuse, or plain
OpenTelemetry instrumented with OpenInference semantic conventions. In
practice it has been tested against the bundled `sample.jsonl` /
`sample-broken.jsonl` fixtures and exactly one real trace: a three-node
linear LangGraph run (research → write → review). Phoenix, Langfuse,
CrewAI, and AutoGen exports have not been run through it.

## Sample output

This is real output from an actual LangGraph run instrumented with OpenInference, not a synthetic sample.

Full output includes per-agent token totals; trimmed here.

```
== Cost ranking (cost.py) ==
#  AGENT     STEP         IN  OUT     COST  SOURCE    % OF TOTAL
1  research  ChatOpenAI  300  241  $0.0045  computed       40.7%
2  write     ChatOpenAI  536  179  $0.0043  computed       38.7%
3  review    ChatOpenAI  473   58  $0.0023  computed       20.6%

container spans (0 tokens, work counted in child spans):
AGENT     STEP       IN  OUT
research  research    0    0
write     write       0    0
review    review      0    0
unknown   LangGraph   0    0

covered 7 of 7 lines; 0 unreadable, 1 with no agent name

== Repeated context (repeat.py) ==
PREVIEW                                                       STEPS  TOKENS (EST)  WASTED (EST)
You are a careful research assistant. You are a careful rese      3           380           760

note: token counts are estimates (len(text) // 4 of the raw string), not measured against a real tokenizer.
```

SOURCE distinguishes a span's own reported cost (`reported`) from a price computed from the `PRICES` table (`computed`). A step whose model has no entry in `PRICES`, or that has no `llm.model_name` at all, shows `n/a` for cost.

## What it does not do

- No live dashboard. No server, no web UI, no hosted anything. One command, text output.
- No trends over time. It explains a single run, not many runs across days.
- No optimization suggestions. It shows a context block was resent nine times. It does not tell you how to fix it.
- No instrumentation. It does not wrap your LLM calls or collect traces. You bring a log; it reads it.
- Prices for one provider only, hardcoded in v0.1.
- OpenInference spans only, with one LangGraph-specific fallback: if a span
  has no `agent.name` or `graph.node.name`, the tool looks for a
  `langgraph_node` key inside the OpenInference `metadata` attribute. No
  other framework-specific log formats.

See [not-in-v0.1.md](not-in-v0.1.md) for what's planned but not shipped.

## Contact

Open a GitHub issue, or email <rrkher059@gmail.com>.
