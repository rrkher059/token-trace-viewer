# Not in v0.1

- Near-duplicate detection beyond shared-prefix matching. Exact matches and
  long shared leading-prefix matches (e.g. a fixed system prompt followed by
  different per-step text) are both caught today; true near-duplicates that
  diverge earlier in the string -- paraphrases, reordered content, mid-string
  edits -- are not.
- Real tokenizer instead of len(text) // 4.
- More providers.
- Spans with token counts but no message content (e.g. CHAIN spans) are
  priced but invisible to repeat detection. Their tokens may be repeats we
  can't see.
- Shared-prefix detection compares adjacent sorted strings, which is fast
  enough for small traces but untested on traces with hundreds of spans.
- Negative token counts are trusted into totals without warning. A span
  with a negative llm.token_count.prompt/completion silently pulls the
  report and cost totals down instead of being flagged as bad data.
- cost.py has no row cap on the ranking table. A trace with 5,000 spans
  prints 5,000 rows instead of a top-N summary.
- A negative llm.cost.total is trusted the same as negative token counts: it
  prints as a negative dollar figure (e.g. "$-3.5000"), and it drags the
  ranking's run total to zero or below, which forces every % OF TOTAL in
  that run to "n/a" instead of a signed percentage.
- Untested against traces with loops, tool calls, or nested sub-agents. The
  one real trace on hand (see README) is a straight-line, three-node run
  with no branching, retries, or agent-within-agent nesting.
- Untested against real exporter output from Phoenix, Langfuse, CrewAI, or
  AutoGen. Only a hand-rolled LangGraph/OpenInference trace has been run
  through it.
