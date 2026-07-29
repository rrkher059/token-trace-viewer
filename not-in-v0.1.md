# Not in v0.1

- Near-duplicate detection. Exact match only today, so growing conversation
  history goes undetected.
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
