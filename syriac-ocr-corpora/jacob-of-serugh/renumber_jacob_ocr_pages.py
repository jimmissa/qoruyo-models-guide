#!/usr/bin/env python3
"""Rename Jacob OCR page files from scan order to printed page order.

The Qoruyo OCR files were initially named with the image/scan page number.
For the Bedjan-Brock Jacob volumes, the scanned page order is reversed relative
to the true printed page order. This script records the mapping and renames
the page-level OCR files so their filenames match the printed page numbers.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OCR_ROOT = ROOT / "03_qoruyo_ocr"
PAGE_RE = re.compile(r"^(?P<prefix>Jacob_Bedjan_Vol(?P<volume>\d+)_page_)(?P<page>\d+)\.txt$")

# true printed page = scan_to_printed_sum - OCR filename page
SCAN_TO_PRINTED_SUM = {
    1: 721,
    2: 891,
    3: 913,
    4: 915,
    5: 900,
    6: 337,
}


def parse_page(path: Path) -> tuple[int, int]:
    match = PAGE_RE.match(path.name)
    if not match:
        raise ValueError(f"Unexpected Jacob OCR filename: {path.name}")
    return int(match.group("volume")), int(match.group("page"))


def main() -> None:
    crosswalk = {
        "note": (
            "Mapping from original OCR scan-page filenames to true printed "
            "page filenames. Formula: printed_page = scan_to_printed_sum - "
            "ocr_scan_page."
        ),
        "volumes": [],
    }

    planned: list[tuple[Path, Path, dict[str, int | str]]] = []

    for volume, page_sum in SCAN_TO_PRINTED_SUM.items():
        volume_dir = OCR_ROOT / f"vol{volume}"
        if not volume_dir.is_dir():
            raise FileNotFoundError(f"Missing OCR directory: {volume_dir}")

        entries = []
        seen_printed: set[int] = set()
        for path in sorted(volume_dir.glob("*.txt")):
            parsed_volume, scan_page = parse_page(path)
            if parsed_volume != volume:
                raise ValueError(f"{path.name} is in vol{volume} but names vol{parsed_volume}")
            printed_page = page_sum - scan_page
            if printed_page <= 0:
                raise ValueError(f"Invalid printed page {printed_page} from {path.name}")
            if printed_page in seen_printed:
                raise ValueError(f"Duplicate printed page {printed_page} in volume {volume}")
            seen_printed.add(printed_page)

            new_name = f"Jacob_Bedjan_Vol{volume}_page_{printed_page}.txt"
            target = volume_dir / new_name
            entry = {
                "volume": volume,
                "ocr_scan_page": scan_page,
                "printed_page": printed_page,
                "old_file": path.relative_to(ROOT).as_posix(),
                "new_file": target.relative_to(ROOT).as_posix(),
            }
            entries.append(entry)
            if path != target:
                planned.append((path, target, entry))

        crosswalk["volumes"].append(
            {
                "volume": volume,
                "scan_to_printed_sum": page_sum,
                "page_count": len(entries),
                "min_printed_page": min(e["printed_page"] for e in entries),
                "max_printed_page": max(e["printed_page"] for e in entries),
                "pages": sorted(entries, key=lambda e: e["printed_page"]),
            }
        )

    for index, (source, _target, _entry) in enumerate(planned, start=1):
        source.rename(source.with_name(f".renumber_tmp_{index:06d}.txt"))

    for index, (_source, target, _entry) in enumerate(planned, start=1):
        tmp = target.with_name(f".renumber_tmp_{index:06d}.txt")
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite existing file: {target}")
        tmp.rename(target)

    (ROOT / "page_number_crosswalk.json").write_text(
        json.dumps(crosswalk, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Renamed files: {len(planned)}")
    print("Wrote page_number_crosswalk.json")


if __name__ == "__main__":
    main()
