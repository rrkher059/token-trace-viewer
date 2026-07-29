"""Detect llm.input_messages content blocks resent across steps, via two
independent signals: normalized-exact (same text once whitespace noise is
collapsed out) and shared-prefix (a stable header followed by varying
per-step content).

Detection only: no suggestions, no fixes, no rewriting of the trace.
"""

import hashlib
import json
import sys
from collections import defaultdict

from parser import extract_span_id

CONTENT_PREFIX = "llm.input_messages."
CONTENT_SUFFIX = ".message.content"

# Below this many shared leading characters, two message contents are
# treated as unrelated rather than as a repeated block worth reporting.
MIN_PREFIX_CHARS = 200

# A repeated block can occur in many steps; the "where" listing stays
# readable by showing only the first this-many occurrences (in file order)
# and folding the rest into a count.
MAX_OCCURRENCES_SHOWN = 5


def _extract_contents(attrs):
    """Unique message-content strings on one span. A dict, since a span can
    repeat the same text across two message slots (e.g. two system turns)."""
    contents = set()
    for key, value in attrs.items():
        if key.startswith(CONTENT_PREFIX) and key.endswith(CONTENT_SUFFIX) and isinstance(value, str):
            contents.add(value)
    return contents


def _step_occurrence(attrs, record, line_number):
    """Where a repeated block occurred: step name plus a span id if the
    record carries one, else the line number. Returned as a tuple (not the
    previous "name#line" string) so callers can render name and location
    separately, and so identical tuples still dedupe like the old label did.
    """
    name = attrs.get("graph.node.name") or record.get("name") or "unknown"
    span_id = extract_span_id(record)
    where = f"span {span_id}" if span_id else f"line {line_number}"
    return (name, where, line_number)


def find_repeats(path):
    """Map each distinct content string to the set of steps it appeared in.

    Same permissive line-by-line JSON reading as parser.py, but this only
    needs message content and a span id, not a full Step, so it does not
    build parser.py's Step objects (it does reuse extract_span_id, since
    duplicating that lookup would just be a second place for it to drift).
    """
    occurrences = defaultdict(set)

    try:
        handle = open(path, "r", encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"error: cannot read '{path}': {exc.strerror}", file=sys.stderr)
        sys.exit(1)

    with handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("line is valid JSON but not an object")
                attrs = record.get("attributes") or {}
                if not isinstance(attrs, dict):
                    attrs = {}
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError,
                    TypeError, AttributeError):
                continue

            occurrence = _step_occurrence(attrs, record, line_number)
            for content in _extract_contents(attrs):
                occurrences[content].add(occurrence)

    return _blocks_from_occurrences(occurrences)


def _lcp_len(a, b):
    """Length of the longest leading substring a and b have in common."""
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def _normalize(text):
    """Collapse whitespace runs to single spaces and strip the ends.

    Deliberately does NOT lowercase and does NOT strip punctuation -- both
    would change what a prompt means, not just its incidental formatting.
    str.split() with no argument already splits on any run of whitespace
    (space, tab, newline) and drops leading/trailing runs, so rejoining
    with single spaces is the whole normalization."""
    return " ".join(text.split())


def _normalized_exact_groups(occurrences):
    """Group raw texts by the hash of their normalized form.

    Two texts that differ only in whitespace (a doubled space, a stray
    trailing newline) are different dict keys in `occurrences` and would
    never meet in the old byte-identical check, but they normalize to the
    same string and land in the same group here -- this is what catches
    "a tiny edit hiding the same recurring tax."

    Returns {hash: (representative_raw_text, occurrence_set)}, one entry
    per hash whose combined occurrence set has at least 2 members and whose
    normalized length clears MIN_PREFIX_CHARS (short recurring boilerplate
    isn't worth flagging as wasted context, same floor the old exact-match
    check used). representative_raw_text is the RAW text of the earliest
    occurrence in the group (by line number): token/preview stats should
    reflect what was actually sent on the wire, not the normalized stand-in
    that exists only to decide "these are the same block."
    """
    occs_by_hash = defaultdict(set)
    first_seen = {}  # hash -> (min_line_number, raw_text)

    for text, occs in occurrences.items():
        digest = hashlib.sha256(_normalize(text).encode("utf-8")).hexdigest()
        occs_by_hash[digest] |= occs
        min_line = min(o[2] for o in occs)
        if digest not in first_seen or min_line < first_seen[digest][0]:
            first_seen[digest] = (min_line, text)

    return {
        digest: (first_seen[digest][1], occs)
        for digest, occs in occs_by_hash.items()
        if len(occs) >= 2 and len(first_seen[digest][1]) > MIN_PREFIX_CHARS
    }


def _prefix_groups(occurrences):
    """Shared-leading-prefix detection: a fixed header (e.g. a stable
    system prompt) followed by varying per-step text still shares a long
    leading substring even though the full strings differ.

    Unchanged from v0.1 except it no longer also special-cases byte-
    identical text -- that's a strict subset of normalized-exact (an
    identical string is trivially identical after normalization too), so
    _normalized_exact_groups already covers it and this only needs to find
    genuinely partial matches.

    Distinct texts are sorted lexicographically and merged, from the
    longest shared prefix down to MIN_PREFIX_CHARS, using the adjacent
    strings' common-prefix length as the merge order (a standard trick:
    for strings sorted lexicographically, only lexicographically-adjacent
    pairs need to be compared -- any two strings' true shared prefix length
    is the minimum adjacent shared-prefix length between them, so this
    finds every maximal group without checking every pair).

    Returns a list of (prefix_text, occurrence_set).
    """
    texts = list(occurrences.keys())
    labels = [set(occurrences[t]) for t in texts]
    parent = list(range(len(texts)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    order = sorted(range(len(texts)), key=lambda i: texts[i])
    edges = [
        (_lcp_len(texts[a], texts[b]), a, b)
        for a, b in zip(order, order[1:])
    ]
    edges = [e for e in edges if e[0] > MIN_PREFIX_CHARS]
    edges.sort(key=lambda e: e[0], reverse=True)

    reported = []  # (prefix_text, step_labels)

    # Merge tier by tier (same shared-prefix length together), so a chain
    # of equal-length merges (a shares X with b, b shares X with c) is
    # reported once as one 3-way group instead of two overlapping 2-way
    # ones.
    i = 0
    while i < len(edges):
        weight = edges[i][0]
        j = i
        touched = set()
        while j < len(edges) and edges[j][0] == weight:
            _, a, b = edges[j]
            touched.add(a)
            touched.add(b)
            ra, rb = find(a), find(b)
            if ra != rb:
                labels[ra] |= labels[rb]
                parent[rb] = ra
            j += 1
        for root in {find(v) for v in touched}:
            if len(labels[root]) >= 2:
                reported.append((texts[root][:weight], set(labels[root])))
        i = j

    return reported


def _blocks_from_occurrences(occurrences):
    """Combine both detectors into reportable repeated-block rows.

    A block whose occurrence set is identical between the two detectors is
    reported once, labeled "both", rather than twice -- but a block that
    normalized-exact finds across steps {1,2,3} and prefix finds across
    {1,2,3,4} (prefix caught an extra step whose content diverges from the
    other three before it diverges from all four) are genuinely different
    findings and are both kept.
    """
    normalized_groups = _normalized_exact_groups(occurrences)
    prefix_groups = _prefix_groups(occurrences)

    rows = {}  # frozenset(occurrences) -> {"text": str, "mechanisms": set}

    for _digest, (raw_text, occs) in normalized_groups.items():
        rows[frozenset(occs)] = {"text": raw_text, "mechanisms": {"normalized-exact"}}

    for prefix_text, occs in prefix_groups:
        key = frozenset(occs)
        if key in rows:
            rows[key]["mechanisms"].add("prefix")
        else:
            rows[key] = {"text": prefix_text, "mechanisms": {"prefix"}}

    blocks = []
    for occs, info in rows.items():
        text = info["text"]
        tokens_est = len(text) // 4
        step_count = len(occs)
        wasted_est = (step_count - 1) * tokens_est
        preview = text[:60].replace("\n", " ")
        # File order, so "first 5" in the rendered output means first-seen,
        # not an arbitrary set-iteration order.
        ordered_occs = sorted(occs, key=lambda o: o[2])
        mechanism = "both" if len(info["mechanisms"]) > 1 else next(iter(info["mechanisms"]))
        blocks.append((wasted_est, step_count, tokens_est, preview, ordered_occs, mechanism))

    blocks.sort(key=lambda b: b[0], reverse=True)
    return blocks


def _where_line(ordered_occs):
    """One indented line per block listing where it occurred: step name
    and span id (or line number) for the first MAX_OCCURRENCES_SHOWN, in
    file order, plus a count of the rest so the table above stays readable
    even when a block repeats across dozens of steps."""
    shown = ordered_occs[:MAX_OCCURRENCES_SHOWN]
    parts = [f"{name} ({where})" for name, where, _line in shown]
    rest = len(ordered_occs) - len(shown)
    if rest > 0:
        parts.append(f"+ {rest} more")
    return "    found at: " + ", ".join(parts)


def render(blocks):
    if not blocks:
        return "no context blocks repeated across steps"

    header = ("PREVIEW", "STEPS", "TOKENS (EST)", "WASTED (EST)", "MECHANISM")
    table = [header]
    for wasted_est, step_count, tokens_est, preview, ordered_occs, mechanism in blocks:
        table.append((preview, str(step_count), str(tokens_est), str(wasted_est), mechanism))

    right_aligned = {1, 2, 3}
    widths = [max(len(row[i]) for row in table) for i in range(len(header))]
    lines = [
        "  ".join(
            cell.rjust(widths[i]) if i in right_aligned else cell.ljust(widths[i])
            for i, cell in enumerate(row)
        )
        for row in table
    ]

    # Interleave a "found at" line after each data row (table[1:], since
    # table[0] is the header) so each block's locations sit right under it.
    output_lines = [lines[0]]
    for line, (wasted_est, step_count, tokens_est, preview, ordered_occs, mechanism) in zip(lines[1:], blocks):
        output_lines.append(line)
        output_lines.append(_where_line(ordered_occs))

    return "\n".join(output_lines)


def main(path):
    blocks = find_repeats(path)
    print(render(blocks))
    print(
        "\nnote: token counts are estimates (len(text) // 4 of the raw "
        "string), not measured against a real tokenizer."
    )
    print(
        "note: MECHANISM is \"normalized-exact\" (same text once whitespace "
        "is collapsed), \"prefix\" (a stable header followed by varying "
        "content), or \"both\"."
    )
    has_span_id = any(
        "span " in where
        for _wasted, _steps, _tokens, _preview, occs, _mechanism in blocks
        for _name, where, _line in occs
    )
    if blocks and not has_span_id:
        print(
            "note: no span id found on any repeated step in this trace; "
            "\"found at\" locations are line numbers instead."
        )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python repeat.py <path-to-log.jsonl>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
