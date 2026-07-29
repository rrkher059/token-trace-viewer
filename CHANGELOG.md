# Changelog

## v0.2 (2026-07-29)

Feedback came from three Reddit responders on the v0.1 post.

- Span ids in the repeat table. repeat.py now lists the step names and
  span ids (or line numbers, when a trace carries no span id) where each
  repeated block occurred, so a finding is something you can go find in
  the trace instead of just a number.
- Rate card moved out of code. cost.py no longer hardcodes PRICES. Prices
  live in `prices.json` (model, input/output price per 1M tokens, source,
  date checked) at the repo root, loaded at runtime, overridable with
  `--prices`. Flagged by two responders as the most-cited v0.1 complaint.
- Normalize-then-hash repeat detection. Message content is normalized
  (whitespace runs collapsed, ends stripped -- no lowercasing, no
  punctuation stripping) before hashing and grouping, so a whitespace-only
  edit no longer hides a recurring context block. Shared-prefix detection
  is unchanged and still catches a stable header followed by varying
  content; each row in the repeat table is labeled with which mechanism
  found it ("normalized-exact", "prefix", or "both").
- Docs. README documents the new span-id column, prices.json, and the two
  detection mechanisms, with a refreshed real sample output.
  `not-in-v0.1.md` renamed to `not-shipped.md`. scope.md's first-user count
  corrected from 2 to 1 -- two previously-cited issues turned out to be
  unrelated LangGraph framework bugs, not cost-attribution problems.

## v0.1 (2026-07-27)

Initial release: per-agent/per-step token totals, cost ranking against a
hardcoded price table, and shared-prefix repeated-context detection.
