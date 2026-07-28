"""Detect llm.input_messages content blocks resent verbatim across steps.

Detection only: no suggestions, no fixes, no rewriting of the trace.
"""

import json
import sys
from collections import defaultdict

CONTENT_PREFIX = "llm.input_messages."
CONTENT_SUFFIX = ".message.content"


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

    with open(path, "r", encoding="utf-8", errors="replace") as handle:
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

    # (wasted_tokens_est, step_count, tokens_est, preview)
    blocks = []
    for text, steps in occurrences.items():
        if len(steps) < 2:
            continue
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
