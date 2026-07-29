# Not shipped

Renamed from `not-in-v0.1.md` now that it spans more than one release.

- True near-duplicate detection: paraphrases, reordered content, and
  mid-string edits that change actual wording (not just whitespace) still
  defeat detection. v0.2 added normalized-exact hashing, which catches
  whitespace-only edits (a doubled space, a stray newline) that used to
  slip past both the byte-exact and shared-prefix checks -- but a rephrased
  sentence or a reordered paragraph still looks like unrelated text to both
  detectors.
- Separate hashing of tool schemas versus instruction blocks. A responder's
  suggestion: today a repeated tool schema and a repeated instruction block
  are both just "message content" to repeat.py, hashed and prefix-matched
  the same way. Splitting them would let a reader tell "the tool
  definitions are identical every step" from "the system prompt is
  identical every step" instead of one merged finding.
- Real tokenizer instead of len(text) // 4.
- More providers priced out of the box. prices.json (v0.2) makes adding a
  model a JSON edit instead of a code change, but the shipped file still
  only carries two entries.
- Spans with token counts but no message content (e.g. CHAIN spans) are
  priced but invisible to repeat detection. Their tokens may be repeats we
  can't see.
- Shared-prefix detection compares adjacent sorted strings, which is fast
  enough for small traces but untested on traces with hundreds of spans.
  Normalized-exact hashing (v0.2) is a straightforward O(n) group-by and
  doesn't share this concern.
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
