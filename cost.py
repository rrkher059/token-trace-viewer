"""Print every step ranked by dollar cost, highest first."""

import sys

from parser import parse_log

# Source: https://www.anthropic.com/news/claude-opus-5, checked 2026-07-28
# Dollars per 1,000,000 tokens.
PRICES = {
    "claude-opus-5-0": {"input": 5.0, "output": 25.0},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
}


def _cost(step):
    """Dollar cost for one step, or None if we have no price for its model
    (including steps with no llm.model_name at all, e.g. some CHAIN spans)."""
    if not step.model:
        return None
    price = PRICES.get(step.model)
    if price is None:
        return None
    return (step.input_tokens * price["input"] + step.output_tokens * price["output"]) / 1_000_000


def render(steps):
    # Zero-token spans (e.g. a LangGraph CHAIN wrapper span around the LLM
    # span that did the actual work) cost nothing and would just show up as
    # an empty-looking duplicate of the real step. They stay in report.py's
    # totals; they just don't get a ranking row here.
    priced_steps = [s for s in steps if not s.zero_tokens]

    # (agent, step, input_tokens, output_tokens, cost_or_None)
    rows = [(s.agent, s.step, s.input_tokens, s.output_tokens, _cost(s)) for s in priced_steps]

    # Priced rows first, highest cost first; unpriced ("n/a") rows sink to the
    # bottom in their original order rather than being dropped.
    rows.sort(key=lambda r: (r[4] is None, -(r[4] or 0.0)))

    run_total = sum(cost for *_, cost in rows if cost is not None)
    unpriced = sum(1 for *_, cost in rows if cost is None)

    header = ("#", "AGENT", "STEP", "IN", "OUT", "COST", "% OF TOTAL")
    table = [header]
    for rank, (agent, step_name, inp, out, cost) in enumerate(rows, start=1):
        if cost is None:
            cost_s, pct_s = "n/a", "n/a"
        else:
            cost_s = f"${cost:.4f}"
            pct_s = f"{cost / run_total * 100:.1f}%" if run_total > 0 else "n/a"
        table.append((str(rank), agent, step_name, f"{inp:,}", f"{out:,}", cost_s, pct_s))

    right_aligned = {0, 3, 4, 5, 6}
    widths = [max(len(row[i]) for row in table) for i in range(len(header))]
    lines = [
        "  ".join(
            cell.rjust(widths[i]) if i in right_aligned else cell.ljust(widths[i])
            for i, cell in enumerate(row)
        )
        for row in table
    ]

    if unpriced:
        lines.append("")
        lines.append(
            f'note: {unpriced} step(s) have no price for their model (or no '
            f'llm.model_name at all) and are shown with cost "n/a"; they are '
            f"excluded from % of run total."
        )

    return "\n".join(lines)


def main(path):
    steps, skipped, unknown_agents = parse_log(path)
    report = render(steps)
    if report:
        print(report)

    total_lines = len(steps) + skipped
    print(
        f"\ncovered {len(steps)} of {total_lines} lines; "
        f"{skipped} unreadable, {unknown_agents} with no agent name"
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python cost.py <path-to-log.jsonl>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
