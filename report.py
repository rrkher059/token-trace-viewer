"""Print token totals grouped by agent, then by step, biggest first."""

import sys
from collections import defaultdict

from parser import parse_log


def _totals_by_agent_and_step(steps):
    totals = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))  # agent -> step -> [in, out, count]
    for step in steps:
        entry = totals[step.agent][step.step]
        entry[0] += step.input_tokens
        entry[1] += step.output_tokens
        entry[2] += 1
    return totals


def render(steps):
    totals = _totals_by_agent_and_step(steps)
    agent_totals = {
        agent: (
            sum(inp for inp, _out, _count in step_map.values()),
            sum(out for _inp, out, _count in step_map.values()),
        )
        for agent, step_map in totals.items()
    }
    agents = sorted(agent_totals, key=lambda a: sum(agent_totals[a]), reverse=True)

    rows = []  # (label, input_tokens, output_tokens)
    for agent in agents:
        agent_in, agent_out = agent_totals[agent]
        rows.append((agent, agent_in, agent_out))
        step_map = totals[agent]
        for step, (inp, out, count) in sorted(
            step_map.items(), key=lambda kv: kv[1][0] + kv[1][1], reverse=True
        ):
            label = f"{step} (x{count})" if count > 1 else step
            rows.append((f"    {label}", inp, out))

    grand_in = sum(inp for inp, _out in agent_totals.values())
    grand_out = sum(out for _inp, out in agent_totals.values())
    rows.append(("TOTAL", grand_in, grand_out))

    label_width = max((len(label) for label, _in, _out in rows), default=0)
    in_width = max((len(f"{inp:,}") for _label, inp, _out in rows), default=0)
    out_width = max((len(f"{out:,}") for _label, _inp, out in rows), default=0)

    return "\n".join(
        f"{label:<{label_width}}  {inp:>{in_width},} in  {out:>{out_width},} out"
        for label, inp, out in rows
    )


def main(path):
    steps, skipped, unknown_agents = parse_log(path)
    report = render(steps)
    if report:
        print(report)

    total_lines = len(steps) + skipped
    print(
        f"covered {len(steps)} of {total_lines} lines; "
        f"{skipped} unreadable, {unknown_agents} with no agent name"
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python report.py <path-to-log.jsonl>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
