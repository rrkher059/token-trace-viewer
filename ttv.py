"""Single entry point: run report.py, cost.py, and repeat.py on one log."""

import sys

import cost
import report
import repeat


def main(path):
    print("== Token totals (report.py) ==")
    report.main(path)

    print("\n== Cost ranking (cost.py) ==")
    cost.main(path)

    print("\n== Repeated context (repeat.py) ==")
    repeat.main(path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python3 ttv.py <path-to-log.jsonl>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
