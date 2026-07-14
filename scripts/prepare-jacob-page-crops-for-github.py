#!/usr/bin/env python3
"""Prepare Jacob of Serugh page crops for the GitHub corpus tree.

This copies the locally prepared page crops into:

  syriac-ocr-corpora/jacob-of-serugh/02_prepared_page_crops/

and renames them by printed page number so they match the existing
03_qoruyo_ocr filenames. The mapping is read from the Jacob
page_number_crosswalk.json file already stored in the repository.

The source-root argument should point to the local folder that contains:

  Vol1 photos/
  Vol2 photos/
  Vol3 photos/
  Vol4 photos/
  Vol5 photos/
  Vol6 photos_1/
  Vol6 photos_2/
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


CORPUS_RELATIVE = Path("syriac-ocr-corpora/jacob-of-serugh")
OUTPUT_RELATIVE = CORPUS_RELATIVE / "02_prepared_page_crops"
CROSSWALK_RELATIVE = CORPUS_RELATIVE / "page_number_crosswalk.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy and printed-page-rename Jacob prepared page crops."
    )
    parser.add_argument(
        "--source-root",
        required=True,
        type=Path,
        help="Folder containing the local Jacob volume image folders.",
    )
    parser.add_argument(
        "--repo-root",
        default=Path.cwd(),
        type=Path,
        help="Root of the qoruyo-models-guide repository. Defaults to cwd.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate paths and report planned copies without writing files.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove the existing 02_prepared_page_crops folder before copying.",
    )
    return parser.parse_args()


def source_image_for_scan(source_root: Path, volume: int, scan_page: int) -> Path:
    if 1 <= volume <= 5:
        return (
            source_root
            / f"Vol{volume} photos"
            / f"Homilies Vol{volume}_page_{scan_page}.jpg"
        )

    if volume == 6:
        if 1 <= scan_page <= 83:
            return (
                source_root
                / "Vol6 photos_1"
                / f"Homilies Vol6 Subsetted 1_cropped_page_{scan_page}.jpg"
            )
        if 84 <= scan_page <= 336:
            return (
                source_root
                / "Vol6 photos_2"
                / f"Homilies Vol6 Subsetted 2_cropped_page_{scan_page - 84}.jpg"
            )

    raise ValueError(f"Unsupported volume/scan page: vol={volume}, scan={scan_page}")


def main() -> None:
    args = parse_args()
    source_root = args.source_root.expanduser().resolve()
    repo_root = args.repo_root.expanduser().resolve()
    crosswalk_path = repo_root / CROSSWALK_RELATIVE
    output_root = repo_root / OUTPUT_RELATIVE

    if not source_root.exists():
        raise SystemExit(f"Missing source root: {source_root}")
    if not crosswalk_path.exists():
        raise SystemExit(f"Missing crosswalk: {crosswalk_path}")

    data = json.loads(crosswalk_path.read_text(encoding="utf-8"))

    planned: list[dict[str, object]] = []
    missing: list[Path] = []
    for volume_entry in data["volumes"]:
        volume = int(volume_entry["volume"])
        for page_entry in volume_entry["pages"]:
            scan_page = int(page_entry["ocr_scan_page"])
            printed_page = int(page_entry["printed_page"])
            src = source_image_for_scan(source_root, volume, scan_page)
            dst = (
                output_root
                / f"vol{volume}"
                / f"Jacob_Bedjan_Vol{volume}_page_{printed_page}.jpg"
            )
            if not src.exists():
                missing.append(src)
            planned.append(
                {
                    "volume": volume,
                    "scan_page": scan_page,
                    "printed_page": printed_page,
                    "source_file": src.name,
                    "destination_file": str(dst.relative_to(output_root)),
                }
            )

    if missing:
        print(f"Missing {len(missing)} source image(s). First examples:")
        for path in missing[:20]:
            print(f"  {path}")
        raise SystemExit(1)

    print(f"Prepared copy plan: {len(planned)} image(s)")
    print(f"Source root: {source_root}")
    print(f"Output root: {output_root}")

    if args.dry_run:
        print("Dry run only; no files written.")
        return

    if args.clean and output_root.exists():
        shutil.rmtree(output_root)

    for item in planned:
        volume = int(item["volume"])
        scan_page = int(item["scan_page"])
        printed_page = int(item["printed_page"])
        src = source_image_for_scan(source_root, volume, scan_page)
        dst = (
            output_root
            / f"vol{volume}"
            / f"Jacob_Bedjan_Vol{volume}_page_{printed_page}.jpg"
        )
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    manifest = {
        "description": (
            "Prepared Jacob of Serugh page crops copied from local OCR inputs "
            "and renamed to printed page numbers matching 03_qoruyo_ocr."
        ),
        "source_root_note": (
            "The absolute local source path is intentionally not preserved in "
            "this manifest."
        ),
        "crosswalk": str(CROSSWALK_RELATIVE),
        "image_count": len(planned),
        "volumes": [
            {
                "volume": int(volume_entry["volume"]),
                "image_count": len(volume_entry["pages"]),
                "output_dir": f"vol{int(volume_entry['volume'])}",
            }
            for volume_entry in data["volumes"]
        ],
        "pages": planned,
    }
    (output_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {len(planned)} image(s) and manifest.")


if __name__ == "__main__":
    main()
