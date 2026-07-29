"""Print every step ranked by dollar cost, highest first."""

import sys

from parser import parse_log

# Source: https://www.anthropic.com/news/claude-opus-5, checked 2026-07-28
# Dollars per 1,000,000 tokens.
PRICES = {
    "claude-opus-5-0": {"input": 5.0, "output": 25.0},
    # Source: https://openrouter.ai/anthropic/claude-sonnet-4.5, checked
    # 2026-07-28. This is OpenRouter's per-token price, which bakes in their
    # margin on top of Anthropic's list price -- not Anthropic's own rate.
    "claude-sonnet-4.5": {"input": 3.0, "output": 15.0},
}


def _normalize_model(model):
    """PRICES keys are bare model names; strip a provider prefix like
    'anthropic/' or 'openai/' before the lookup so 'anthropic/claude-sonnet-4.5'
    resolves the same as 'claude-sonnet-4.5'."""
    if not model:
        return model
    return model.rsplit("/", 1)[-1]


def _cost(step):
    """Dollar cost for one step as (cost, source), or (None, None) if we
    have neither a reported cost nor a price for its model (including steps
    with no llm.model_name at all, e.g. some CHAIN spans).

    A span's own reported cost always wins over our price table -- it
    reflects what was actually billed, including any provider-side
    discounting our static PRICES can't know about."""
    if step.reported_cost is not None:
        return step.reported_cost, "reported"
    if not step.model:
        return None, None
    price = PRICES.get(_normalize_model(step.model))
    if price is None:
        return None, None
    cost = (step.input_tokens * price["input"] + step.output_tokens * price["output"]) / 1_000_000
    return cost, "computed"


def render(steps):
    # Zero-token spans (e.g. a LangGraph CHAIN wrapper span around the LLM
    # span that did the actual work) cost nothing, and ranking them by
    # dollar cost alongside real spend is meaningless. They aren't hidden
    # though -- they get their own labelled section below the ranking, and
    # they still count toward report.py's totals.
    priced_steps = [s for s in steps if not s.zero_tokens]
    container_steps = [s for s in steps if s.zero_tokens]

    # (agent, step, input_tokens, output_tokens, cost_or_None, source_or_None)
    rows = [(s.agent, s.step, s.input_tokens, s.output_tokens, *_cost(s)) for s in priced_steps]

    # Priced rows first, highest cost first; unpriced ("n/a") rows sink to the
    # bottom in their original order rather than being dropped.
    rows.sort(key=lambda r: (r[4] is None, -(r[4] or 0.0)))

    run_total = sum(r[4] for r in rows if r[4] is not None)
    unpriced = sum(1 for r in rows if r[4] is None)

    header = ("#", "AGENT", "STEP", "IN", "OUT", "COST", "SOURCE", "% OF TOTAL")
    table = [header]
    for rank, (agent, step_name, inp, out, cost, source) in enumerate(rows, start=1):
        if cost is None:
            cost_s, pct_s, source_s = "n/a", "n/a", "-"
        else:
            cost_s = f"${cost:.4f}"
            pct_s = f"{cost / run_total * 100:.1f}%" if run_total > 0 else "n/a"
            source_s = source
        table.append((str(rank), agent, step_name, f"{inp:,}", f"{out:,}", cost_s, source_s, pct_s))

    right_aligned = {0, 3, 4, 5, 7}
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

    if container_steps:
        lines.append("")
        lines.append("container spans (0 tokens, work counted in child spans):")
        c_header = ("AGENT", "STEP", "IN", "OUT")
        c_table = [c_header] + [
            (s.agent, s.step, f"{s.input_tokens:,}", f"{s.output_tokens:,}")
            for s in container_steps
        ]
        c_right_aligned = {2, 3}
        c_widths = [max(len(row[i]) for row in c_table) for i in range(len(c_header))]
        lines.extend(
            "  ".join(
                cell.rjust(c_widths[i]) if i in c_right_aligned else cell.ljust(c_widths[i])
                for i, cell in enumerate(row)
            )
            for row in c_table
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
