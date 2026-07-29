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
