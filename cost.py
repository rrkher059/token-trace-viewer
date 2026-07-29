"""Print every step ranked by dollar cost, highest first."""

import argparse
import json
import sys
from pathlib import Path

from parser import parse_log

# prices.json lives at the repo root, next to this file, unless --prices
# points somewhere else.
DEFAULT_PRICES_PATH = Path(__file__).resolve().parent / "prices.json"


def load_prices(path=None):
    """Load the rate card from a JSON file: a list of entries, each with
    model, input_per_1m, output_per_1m, source, and date_checked.

    Returns (prices, error). On any problem -- the file is missing, isn't
    valid JSON, or isn't shaped like a list of priced entries -- prices is
    an empty dict and error is a human-readable message. Every step then
    shows cost "n/a" instead of the run crashing; a missing or broken rate
    card is not a reason to refuse to show the rest of the report.

    An entry with no source is dropped rather than trusted: the constraint
    that every price must be traceable to where it came from held in the
    old hardcoded PRICES table, and moving to JSON doesn't relax it.
    """
    prices_path = Path(path) if path else DEFAULT_PRICES_PATH

    try:
        raw = prices_path.read_text(encoding="utf-8")
    except OSError as exc:
        return {}, f"cannot read prices file '{prices_path}': {exc.strerror}"

    try:
        entries = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {}, f"prices file '{prices_path}' is not valid JSON: {exc}"

    if not isinstance(entries, list):
        return {}, f"prices file '{prices_path}' must contain a JSON list of entries"

    prices = {}
    skipped = 0
    for entry in entries:
        if not isinstance(entry, dict):
            skipped += 1
            continue
        model = entry.get("model")
        input_price = entry.get("input_per_1m")
        output_price = entry.get("output_per_1m")
        source = entry.get("source")
        valid = (
            isinstance(model, str) and model
            and isinstance(input_price, (int, float)) and not isinstance(input_price, bool)
            and isinstance(output_price, (int, float)) and not isinstance(output_price, bool)
            and isinstance(source, str) and source
        )
        if not valid:
            skipped += 1
            continue
        prices[model] = {"input": float(input_price), "output": float(output_price)}

    if not prices:
        return {}, f"prices file '{prices_path}' has no usable priced entries"

    if skipped:
        print(
            f"warning: {skipped} entry(ies) in '{prices_path}' were skipped "
            f"(missing model/price/source)",
            file=sys.stderr,
        )

    return prices, None


def _normalize_model(model):
    """prices.json keys are bare model names; strip a provider prefix like
    'anthropic/' or 'openai/' before the lookup so 'anthropic/claude-sonnet-4.5'
    resolves the same as 'claude-sonnet-4.5'."""
    if not model:
        return model
    return model.rsplit("/", 1)[-1]


def _cost(step, prices):
    """Dollar cost for one step as (cost, source), or (None, None) if we
    have neither a reported cost nor a price for its model (including steps
    with no llm.model_name at all, e.g. some CHAIN spans, or a model with
    no entry in prices.json).

    A span's own reported cost always wins over the rate card -- it
    reflects what was actually billed, including any provider-side
    discounting a static price list can't know about."""
    if step.reported_cost is not None:
        return step.reported_cost, "reported"
    if not step.model:
        return None, None
    price = prices.get(_normalize_model(step.model))
    if price is None:
        return None, None
    cost = (step.input_tokens * price["input"] + step.output_tokens * price["output"]) / 1_000_000
    return cost, "computed"


def render(steps, prices):
    # Zero-token spans (e.g. a LangGraph CHAIN wrapper span around the LLM
    # span that did the actual work) cost nothing, and ranking them by
    # dollar cost alongside real spend is meaningless. They aren't hidden
    # though -- they get their own labelled section below the ranking, and
    # they still count toward report.py's totals.
    priced_steps = [s for s in steps if not s.zero_tokens]
    container_steps = [s for s in steps if s.zero_tokens]

    # (agent, step, input_tokens, output_tokens, cost_or_None, source_or_None)
    rows = [(s.agent, s.step, s.input_tokens, s.output_tokens, *_cost(s, prices)) for s in priced_steps]

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


def main(path, prices_path=None):
    prices, prices_error = load_prices(prices_path)
    if prices_error:
        print(f"warning: {prices_error}; showing cost as n/a for every row", file=sys.stderr)

    steps, skipped, unknown_agents = parse_log(path)
    report = render(steps, prices)
    if report:
        print(report)

    total_lines = len(steps) + skipped
    print(
        f"\ncovered {len(steps)} of {total_lines} lines; "
        f"{skipped} unreadable, {unknown_agents} with no agent name"
    )


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="Rank trace steps by dollar cost.")
    arg_parser.add_argument("path", help="path to a JSONL trace file")
    arg_parser.add_argument(
        "--prices", default=None,
        help=f"path to a prices JSON file (default: {DEFAULT_PRICES_PATH.name} next to cost.py)",
    )
    args = arg_parser.parse_args()
    main(args.path, args.prices)
