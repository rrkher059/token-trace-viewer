# token-trace-viewer

When your agent run costs more than you expected, this tells you which sub-agent spent it, and how much you paid to resend the same context.

## What it does

- Per-sub-agent totals — input and output tokens grouped by agent, then by step.
- Cost ranking — every step in the run, sorted by dollar cost, highest first.
- Repeated-context detection — flags context blocks sent more than once across steps, with repeat count and estimated wasted tokens.

## Install

Requires Python 3.10+ (the code uses `str | None` union syntax). No dependencies — standard library only.

## Run it

```
git clone https://github.com/rrkher059/token-trace-viewer.git
cd token-trace-viewer
python3 ttv.py sample.jsonl
```

On Windows, use `py ttv.py sample.jsonl` instead of `python3`.

The tool reads OpenInference spans as JSONL, one span per line, so it works
against anything that exports that format — Phoenix, Langfuse, or plain
OpenTelemetry instrumented with OpenInference semantic conventions. Only the
bundled `sample.jsonl` / `sample-broken.jsonl` have actually been tested;
real exports from those tools have not been run through it yet.

## Sample output

This is real output from an actual LangGraph run instrumented with OpenInference, not a synthetic sample.

Full output includes per-agent token totals; trimmed here.

```
== Cost ranking (cost.py) ==
#  AGENT     STEP         IN  OUT  COST  % OF TOTAL
1  research  ChatOpenAI  300  241   n/a         n/a
2  write     ChatOpenAI  536  179   n/a         n/a
3  review    ChatOpenAI  473   58   n/a         n/a

note: 3 step(s) have no price for their model (or no llm.model_name at all) and are shown with cost "n/a"; they are excluded from % of run total.

container spans (0 tokens, work counted in child spans):
AGENT     STEP       IN  OUT
research  research    0    0
write     write       0    0
review    review      0    0
unknown   LangGraph   0    0

== Repeated context (repeat.py) ==
PREVIEW                                                       STEPS  TOKENS (EST)  WASTED (EST)
You are a careful research assistant. You are a careful rese      3           380           760

note: token counts are estimates (len(text) // 4 of the raw string), not measured against a real tokenizer.
```

## What it does not do

- No live dashboard. No server, no web UI, no hosted anything. One command, text output.
- No trends over time. It explains a single run, not many runs across days.
- No optimization suggestions. It shows a context block was resent nine times. It does not tell you how to fix it.
- No instrumentation. It does not wrap your LLM calls or collect traces. You bring a log; it reads it.
- Prices for one provider only, hardcoded in v0.1.
- OpenInference spans only. No framework-specific log formats.

See [not-in-v0.1.md](not-in-v0.1.md) for what's planned but not shipped.

## Contact

Open a GitHub issue, or email <rrkher059@gmail.com>.
