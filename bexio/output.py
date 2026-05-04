"""Shared output helpers."""

import json
import sys


def print_json(data) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def table(rows: list[dict], columns: list[tuple[str, str, int]]) -> None:
    """Print a table. columns = [(header, key, width), ...]"""
    fmt = "  ".join(f"{{:<{w}}}" for _, _, w in columns)
    header = fmt.format(*[h for h, _, _ in columns])
    print(header)
    print("-" * len(header))
    for row in rows:
        values = []
        for _, key, width in columns:
            val = str(row.get(key, ""))
            values.append(val[:width])
        print(fmt.format(*values))
