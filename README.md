# token-trace-viewer

When your agent run costs more than you expected, this tells you which sub-agent spent it, and how much you paid to resend the same context.

## What it does

- Per-sub-agent totals — input and output tokens grouped by agent, then by step.
- Cost ranking — every step in the run, sorted by dollar cost, highest first.
- Repeated-context detection — flags context blocks sent more than once across steps, with repeat count, estimated wasted tokens, which detection mechanism found it, and the step names and span ids (or line numbers, if the trace has no span id) where it occurred.

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

## Pricing

`cost.py` prices steps from `prices.json` at the repo root, not a hardcoded
table. Each entry:

```json
{
  "model": "claude-opus-5-0",
  "input_per_1m": 5.0,
  "output_per_1m": 25.0,
  "source": "https://www.anthropic.com/news/claude-opus-5",
  "date_checked": "2026-07-28"
}
```

Every entry must carry a `source` — an entry missing one is skipped, same
as if it weren't in the file. A model with no matching entry shows `n/a`
for cost rather than a guessed price.

Point at a different file with `--prices path/to/other.json`. If the file
is missing, isn't valid JSON, or isn't shaped like a list of entries,
cost.py prints a clear warning and falls through to `n/a` for every row —
it does not crash.

## Repeated-context detection

Two independent signals, run over every `llm.input_messages.*.message.content`
value:

- **normalized-exact** — message content is normalized (whitespace runs
  collapsed to a single space, ends stripped; case and punctuation are left
  alone since both change what a prompt means) and hashed. Two occurrences
  land in the same group if they hash the same, even if a stray space or
  newline makes them byte-different. This catches the case a tiny
  formatting edit used to hide a recurring block entirely.
- **prefix** — the existing v0.1 detector: a long shared *leading*
  substring (200+ characters), for a stable header (e.g. a system prompt)
  followed by different per-step content.

Each row in the repeat table is labeled with whichever mechanism found it,
or `both` if the exact same set of steps was found by each independently.

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
PREVIEW                                                       STEPS  TOKENS (EST)  WASTED (EST)  MECHANISM
You are a careful research assistant. You are a careful rese      3           380           760  prefix   
    found at: ChatOpenAI (line 1), ChatOpenAI (line 3), ChatOpenAI (line 5)

note: token counts are estimates (len(text) // 4 of the raw string), not measured against a real tokenizer.
note: MECHANISM is "normalized-exact" (same text once whitespace is collapsed), "prefix" (a stable header followed by varying content), or "both".
note: no span id found on any repeated step in this trace; "found at" locations are line numbers instead.
```

SOURCE distinguishes a span's own reported cost (`reported`) from a price computed from `prices.json` (`computed`). A step whose model has no entry in `prices.json`, or that has no `llm.model_name` at all, shows `n/a` for cost — same as if `prices.json` itself were missing or unreadable.

## What it does not do

- No live dashboard. No server, no web UI, no hosted anything. One command, text output.
- No trends over time. It explains a single run, not many runs across days.
- No optimization suggestions. It shows a context block was resent nine times. It does not tell you how to fix it.
- No instrumentation. It does not wrap your LLM calls or collect traces. You bring a log; it reads it.
- Prices for two models ship in `prices.json`. Adding more is a JSON edit, not a code change, but nothing beyond those two is bundled.
- OpenInference spans only, with one LangGraph-specific fallback: if a span
  has no `agent.name` or `graph.node.name`, the tool looks for a
  `langgraph_node` key inside the OpenInference `metadata` attribute. No
  other framework-specific log formats.

See [not-shipped.md](not-shipped.md) for what's planned but not shipped.

## Contact

Open a GitHub issue, or email <rrkher059@gmail.com>.
