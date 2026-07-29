"""Detect llm.input_messages content blocks resent verbatim, or with a long
shared leading substring, across steps.

Detection only: no suggestions, no fixes, no rewriting of the trace.
"""

import json
import sys
from collections import defaultdict

CONTENT_PREFIX = "llm.input_messages."
CONTENT_SUFFIX = ".message.content"

# Below this many shared leading characters, two message contents are
# treated as unrelated rather than as a repeated block worth reporting.
MIN_PREFIX_CHARS = 200


def _extract_contents(attrs):
    """Unique message-content strings on one span. A dict, since a span can
    repeat the same text across two message slots (e.g. two system turns)."""
    contents = set()
    for key, value in attrs.items():
        if key.startswith(CONTENT_PREFIX) and key.endswith(CONTENT_SUFFIX) and isinstance(value, str):
            contents.add(value)
    return contents


def _step_label(attrs, record, line_number):
    name = attrs.get("graph.node.name") or record.get("name") or "unknown"
    return f"{name}#{line_number}"


def find_repeats(path):
    """Map each distinct content string to the set of steps it appeared in.

    Same permissive line-by-line JSON reading as parser.py, but this only
    needs message content, not a full Step, so it does not reuse parser.py.
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

            label = _step_label(attrs, record, line_number)
            for content in _extract_contents(attrs):
                occurrences[content].add(label)

    return _blocks_from_occurrences(occurrences)


def _lcp_len(a, b):
    """Length of the longest leading substring a and b have in common."""
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def _blocks_from_occurrences(occurrences):
    """Turn distinct-text -> steps into reportable repeated-block rows.

    Two message contents that are byte-identical are just the special case
    where their shared leading substring is the entire string, so exact
    matches and shared-prefix matches go through the same clustering below
    rather than two separate detectors. Identical strings already collapse
    onto one dict key (one text, several steps) via `occurrences`, which
    accounts for exact matches with zero extra work; everything past that
    is discovering when otherwise-distinct texts (e.g. a fixed system
    prompt followed by different per-step task text) still share a long
    prefix.

    Distinct texts are sorted lexicographically and merged, from the
    longest shared prefix down to MIN_PREFIX_CHARS, using the adjacent
    strings' common-prefix length as the merge order (a standard trick:
    for strings sorted lexicographically, only lexicographically-adjacent
    pairs need to be compared -- any two strings' true shared prefix length
    is the minimum adjacent shared-prefix length between them, so this
    finds every maximal group without checking every pair).
    """
    texts = list(occurrences.keys())
    labels = [set(occurrences[t]) for t in texts]
    parent = list(range(len(texts)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    reported = []  # (prefix_text, step_labels)

    # Groups already fully formed before any cross-text merging: a text
    # that recurred byte-for-byte across two or more steps.
    for text, steps in zip(texts, labels):
        if len(steps) >= 2 and len(text) > MIN_PREFIX_CHARS:
            reported.append((text, set(steps)))

    order = sorted(range(len(texts)), key=lambda i: texts[i])
    edges = [
        (_lcp_len(texts[a], texts[b]), a, b)
        for a, b in zip(order, order[1:])
    ]
    edges = [e for e in edges if e[0] > MIN_PREFIX_CHARS]
    edges.sort(key=lambda e: e[0], reverse=True)

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

    blocks = []
    for text, steps in reported:
        tokens_est = len(text) // 4
        step_count = len(steps)
        wasted_est = (step_count - 1) * tokens_est
        preview = text[:60].replace("\n", " ")
        blocks.append((wasted_est, step_count, tokens_est, preview))

    blocks.sort(key=lambda b: b[0], reverse=True)
    return blocks


def render(blocks):
    if not blocks:
        return "no context blocks repeated across steps"

    header = ("PREVIEW", "STEPS", "TOKENS (EST)", "WASTED (EST)")
    table = [header]
    for wasted_est, step_count, tokens_est, preview in blocks:
        table.append((preview, str(step_count), str(tokens_est), str(wasted_est)))

    right_aligned = {1, 2, 3}
    widths = [max(len(row[i]) for row in table) for i in range(len(header))]
    lines = [
        "  ".join(
            cell.rjust(widths[i]) if i in right_aligned else cell.ljust(widths[i])
            for i, cell in enumerate(row)
        )
        for row in table
    ]
    return "\n".join(lines)


def main(path):
    blocks = find_repeats(path)
    print(render(blocks))
    print(
        "\nnote: token counts are estimates (len(text) // 4 of the raw "
        "string), not measured against a real tokenizer."
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python repeat.py <path-to-log.jsonl>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
