#!/usr/bin/env python3
"""Merge page-level OCR files into one traceable, page-delimited text file."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


PAGE_PATTERN = re.compile(r"_page_(\d+)\.txt$")


def page_number(path: Path) -> int:
    match = PAGE_PATTERN.search(path.name)
    if not match:
        raise ValueError(f"Cannot identify page number from {path.name}")
    return int(match.group(1))


def merge_page_ocr(ocr_dir: Path, output_path: Path) -> int:
    pages = sorted(ocr_dir.glob("*_page_*.txt"), key=page_number)
    if not pages:
        raise FileNotFoundError(f"No page OCR files found in {ocr_dir}")

    numbers = [page_number(path) for path in pages]
    expected = list(range(numbers[0], numbers[-1] + 1))
    if numbers != expected:
        missing = sorted(set(expected) - set(numbers))
        raise ValueError(f"Missing page OCR files: {missing}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as output:
        for path, number in zip(pages, numbers):
            output.write(f"\n===== PAGE {number:03d} =====\n")
            output.write(path.read_text(encoding="utf-8").rstrip())
            output.write("\n")

    return len(pages)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ocr-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    count = merge_page_ocr(args.ocr_dir, args.output)
    print(f"Merged {count} page OCR files into {args.output}")


if __name__ == "__main__":
    main()
