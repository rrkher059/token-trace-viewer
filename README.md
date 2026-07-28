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

Full output includes per-agent token totals; trimmed here.

```
== Cost ranking (cost.py) ==
 #  AGENT       STEP                     IN    OUT     COST  % OF TOTAL
 1  planner     verify_output        15,240    430  $0.0869       18.4%
 2  researcher  summarize_findings   18,430  1,276  $0.0744       15.8%
 3  writer      revise_draft         12,680  1,905  $0.0666       14.1%
 4  writer      emit_answer          16,010  1,120  $0.0648       13.8%
 5  writer      draft_section         9,120  2,340  $0.0625       13.2%

== Repeated context (repeat.py) ==
PREVIEW                                                       STEPS  TOKENS (EST)  WASTED (EST)
You are an autonomous agent operating inside a multi-agent r      9           766          6128

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
