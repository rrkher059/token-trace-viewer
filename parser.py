"""Parse an OpenInference-style JSONL agent trace into flat Step records.

Parsing only: no cost math, no ranking, no grouping. Standard library only.
"""

import json
import sys
from dataclasses import dataclass


@dataclass
class Step:
    agent: str
    step: str
    model: str | None
    input_tokens: int
    output_tokens: int
    raw_line_number: int
    zero_tokens: bool
    reported_cost: float | None
    span_id: str | None


def _as_int(value) -> int:
    """Token counts arrive as ints, sometimes as numeric strings, sometimes null.
    Anything we can't turn into an int becomes 0 rather than blowing up the run."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _as_float(value) -> float | None:
    """Cost values arrive as floats normally, sometimes as numeric strings,
    sometimes garbage. Unlike _as_int, missing/unparseable becomes None, not
    0 -- a $0 span and a span with no cost data are different things."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _reported_cost(attrs: dict) -> float | None:
    """OpenInference spec: a span may report its dollar cost directly via
    llm.cost.total, or split as llm.cost.prompt and llm.cost.completion.
    Prefer the total when present; fall back to the sum of both halves only
    if both are readable, so a half-populated pair doesn't silently read as
    the cost of just one side."""
    total = _as_float(attrs.get("llm.cost.total"))
    if total is not None:
        return total
    prompt_cost = _as_float(attrs.get("llm.cost.prompt"))
    completion_cost = _as_float(attrs.get("llm.cost.completion"))
    if prompt_cost is not None and completion_cost is not None:
        return prompt_cost + completion_cost
    return None


def extract_span_id(record: dict) -> str | None:
    """OpenInference/OTel spans carry a span id either as a top-level
    "span_id" key or nested under "context.span_id". Checked against real
    traces on hand: the bundled sample.jsonl and the one real LangGraph
    trace have neither (their exporter dropped the OTel "context" wrapper
    entirely) -- only sample-broken.jsonl's hand-crafted edge case carries
    a top-level span_id. Callers should fall back to line number when this
    returns None, which is the common case today, not the exception."""
    span_id = record.get("span_id")
    if isinstance(span_id, str) and span_id:
        return span_id
    context = record.get("context")
    if isinstance(context, dict):
        span_id = context.get("span_id")
        if isinstance(span_id, str) and span_id:
            return span_id
    return None


def _langgraph_node(attrs: dict) -> str | None:
    """Real LangGraph traces carry no agent.name or graph.node.name attribute;
    the node name is buried in the metadata attribute, itself a JSON string,
    under langgraph_node. Return None if it can't be recovered."""
    metadata = attrs.get("metadata")
    if not isinstance(metadata, str):
        return None
    try:
        parsed = json.loads(metadata)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    node = parsed.get("langgraph_node")
    return node if isinstance(node, str) else None


def _to_step(record: dict, line_number: int) -> Step:
    """Build a Step from one decoded JSON object, filling in defaults for
    anything the exporter left out. This never raises on missing keys."""
    attrs = record.get("attributes") or {}
    if not isinstance(attrs, dict):
        attrs = {}
    input_tokens = _as_int(attrs.get("llm.token_count.prompt"))
    output_tokens = _as_int(attrs.get("llm.token_count.completion"))
    return Step(
        agent=attrs.get("agent.name") or _langgraph_node(attrs) or "unknown",
        # A real LangGraph node emits two spans: a CHAIN span named after the
        # node (0 tokens) and, nested inside it, the LLM span that did the
        # actual work. Preferring the span's own name over langgraph_node
        # here keeps those two spans visibly distinct instead of both
        # collapsing onto the node name and looking like a duplicated step.
        step=(attrs.get("graph.node.name") or record.get("name")
              or _langgraph_node(attrs) or "unknown"),
        model=attrs.get("llm.model_name"),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        raw_line_number=line_number,
        zero_tokens=input_tokens == 0 and output_tokens == 0,
        reported_cost=_reported_cost(attrs),
        span_id=extract_span_id(record),
    )


def parse_log(path: str) -> tuple[list[Step], int, int]:
    """Read a JSONL trace one line at a time.

    Returns (steps, skipped_count, unknown_agent_count).

    The file is streamed, never json.load()'d as a whole, for two reasons:
    real traces are far too large to hold in memory, and a single corrupt
    byte anywhere would otherwise poison the entire file instead of one line.
    """
    steps: list[Step] = []
    skipped = 0
    unknown_agents = 0

    try:
        handle = open(path, "r", encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"error: cannot read '{path}': {exc.strerror}", file=sys.stderr)
        sys.exit(1)

    with handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()

            # An empty or whitespace-only line is not an error worth reporting
            # loudly, but it is also not a span. Count it as skipped so the
            # totals still add up to the number of lines in the file.
            if not line:
                skipped += 1
                continue

            try:
                record = json.loads(line)

                # A line can be syntactically valid JSON and still not be a
                # span - e.g. a bare string, a number, or a list. Anything that
                # isn't an object has no attributes to read, so reject it here
                # and let the except block below count it uniformly.
                if not isinstance(record, dict):
                    raise ValueError("line is valid JSON but not an object")

                step = _to_step(record, line_number)

                # A line that parses fine but carries no agent name is the
                # QUIET failure: the run looks healthy while the tool has
                # actually learned nothing from it. Count these separately so
                # a mismatched log format shows up loudly instead of printing
                # a cheerful empty table.
                if step.agent == "unknown":
                    unknown_agents += 1

                steps.append(step)

            # WHY EACH OF THESE IS CAUGHT:
            #
            # json.JSONDecodeError - the common case. Trace files are written
            #   by a streaming exporter, so a crashed or killed process leaves
            #   a half-written line, and a poorly escaped string value (an
            #   unescaped quote inside a prompt, say) produces the same error.
            #   Both mean "this one line is garbage", not "this file is bad".
            #   Note the last line of a truncated file hits this too, and it
            #   has no trailing newline - iterating the handle still yields it.
            #
            # UnicodeDecodeError - a log cut mid-multibyte-character. We open
            #   with errors="replace" so this is unlikely, but a caller passing
            #   a differently-opened file should not crash the run.
            #
            # ValueError - covers our own "not an object" raise above, and is
            #   the parent class of JSONDecodeError, so it is the safety net.
            #
            # TypeError / AttributeError - defensive. If a line decodes to a
            #   shape we did not anticipate, we would rather drop the line and
            #   keep the other 99,999 than lose the whole run to one oddity.
            #
            # We deliberately do NOT catch bare Exception: OSError while reading
            #   the file, KeyboardInterrupt, and MemoryError are real problems
            #   that should stop the program, not be silently tallied.
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError,
                    TypeError, AttributeError):
                skipped += 1
                continue

    return steps, skipped, unknown_agents


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python parser.py <path-to-log.jsonl>", file=sys.stderr)
        sys.exit(1)

    parsed_steps, bad_lines, no_agent = parse_log(sys.argv[1])
    no_span_id = sum(1 for s in parsed_steps if s.span_id is None)
    print(f"parsed {len(parsed_steps)} steps, "
          f"skipped {bad_lines} bad lines, "
          f"{no_agent} step(s) had no agent name, "
          f"{no_span_id} step(s) had no span id (using line number instead)")
