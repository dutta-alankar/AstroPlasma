#!/usr/bin/env python3
"""
Count the lines of code in the repository and render the badge SVG.

Replaces shadowmoose/GHA-LoC-Badge, which is pinned at its only release (1.0.0,
2020), still declares ``using: node12`` and reports its results with the retired
``set-output`` command.  There is no newer tag to upgrade to, so the behaviour is
reproduced here instead: the same badge layout, and results written to
``$GITHUB_OUTPUT``.

Only files tracked by git are counted, which keeps the total independent of
whatever untracked material happens to sit in the working tree on a runner.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# Layout constants taken from the badge this replaces, so the rendered SVG is
# unchanged for a given count.  The label is fixed, hence a fixed text length;
# digits and separators in the value each advance by 64 units at font-size 110.
LABEL_TEXT_LENGTH = 747
VALUE_ADVANCE_PER_CHAR = 64
TEXT_SIDE_PADDING = 100

SVG_TEMPLATE = """<svg width="{width}" height="20" viewBox="0 0 {total} 200" xmlns="http://www.w3.org/2000/svg">
  <linearGradient id="a" x2="0" y2="100%">
    <stop offset="0" stop-opacity=".1" stop-color="#EEE"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <mask id="m"><rect width="{total}" height="200" rx="30" fill="#FFF"/></mask>
  <g mask="url(#m)">
    <rect width="{label_w}" height="200" fill="#555"/>
    <rect width="{value_w}" height="200" fill="{color}" x="{label_w}"/>
    <rect width="{total}" height="200" fill="url(#a)"/>
  </g>
  <g fill="#fff" text-anchor="start" font-family="Verdana,DejaVu Sans,sans-serif" font-size="110">
    <text x="60" y="148" textLength="{label_len}" fill="#000" opacity="0.25">{label}</text>
    <text x="50" y="138" textLength="{label_len}">{label}</text>
    <text x="{value_shadow_x}" y="148" textLength="{value_len}" fill="#000" opacity="0.25">{value}</text>
    <text x="{value_x}" y="138" textLength="{value_len}">{value}</text>
  </g>
{gap}
</svg>"""

# The replaced action emitted a two-space line before the closing tag and no
# final newline.  Kept as a placeholder so the badge stays byte-identical
# without leaving trailing whitespace in this file for the linters to strip.
SVG_GAP = "  "


def tracked_files(root: Path) -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [name for name in out.split("\0") if name]


def is_hidden(name: str) -> bool:
    """
    True when any component of the path starts with a dot.

    The action being replaced walked the working tree and skipped dot-prefixed
    entries, so .github, .gitignore and friends never reached the total.
    """
    return any(part.startswith(".") for part in name.split("/"))


def count_lines(path: Path) -> int | None:
    """
    Line count for a text file, or None when the file looks binary.
    """
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data:
        return None
    # Matches the replaced action, which split the text on newlines and took the
    # length -- so a trailing newline contributes a final empty line.
    return data.count(b"\n") + 1


def render(label: str, value: str, color: str) -> str:
    label_w = LABEL_TEXT_LENGTH + TEXT_SIDE_PADDING
    value_len = VALUE_ADVANCE_PER_CHAR * len(value)
    value_w = value_len + TEXT_SIDE_PADDING
    total = label_w + value_w
    return SVG_TEMPLATE.format(
        width=f"{total / 10:g}",
        total=total,
        label_w=label_w,
        value_w=value_w,
        color=color,
        label_len=LABEL_TEXT_LENGTH,
        label=label,
        value_len=value_len,
        value=value,
        value_x=label_w + 45,
        value_shadow_x=label_w + 55,
        gap=SVG_GAP,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root (default: %(default)s)")
    parser.add_argument("--ignore", default="", help="Regex alternation of paths to skip")
    parser.add_argument("--badge", required=True, help="Path of the SVG to write")
    parser.add_argument("--label", default="Lines of Code", help="Badge label (default: %(default)s)")
    parser.add_argument("--color", default="#08C", help="Badge value colour (default: %(default)s)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ignore = re.compile(args.ignore) if args.ignore else None

    total_lines = 0
    counted_files = 0
    for name in tracked_files(root):
        if is_hidden(name):
            continue
        if ignore is not None and ignore.search(name):
            continue
        lines = count_lines(root / name)
        if lines is None:
            continue
        total_lines += lines
        counted_files += 1

    badge_path = Path(args.badge)
    badge_path.parent.mkdir(parents=True, exist_ok=True)
    badge_path.write_text(render(args.label, f"{total_lines:,}", args.color))

    print(f"Scanned: {counted_files}")
    print(f"Line Count: {total_lines}")

    # Environment files, the supported replacement for the set-output command.
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as handle:
            handle.write(f"counted_files={counted_files}\n")
            handle.write(f"total_lines={total_lines}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
