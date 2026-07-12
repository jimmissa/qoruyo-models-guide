#!/usr/bin/env python3
"""Build merged Jacob of Serugh OCR texts and a path-neutral manifest."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OCR_ROOT = ROOT / "03_qoruyo_ocr"
MERGED_ROOT = ROOT / "merged"
PAGE_RE = re.compile(r"_page_(?P<page>\d+)\.txt$", re.IGNORECASE)


def page_number(path: Path) -> int:
    match = PAGE_RE.search(path.name)
    if not match:
        raise ValueError(f"Page filename does not end in _page_N.txt: {path}")
    return int(match.group("page"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def page_block(volume: int, page: int, text: str) -> str:
    clean_text = text.rstrip("\n")
    return (
        f"===== VOLUME {volume} | PAGE {page:04d} =====\n"
        f"{clean_text}\n"
    )


def main() -> None:
    MERGED_ROOT.mkdir(parents=True, exist_ok=True)
    manifest = {"volumes": [], "total_pages": 0}
    corpus_blocks: list[str] = []

    for volume in range(1, 7):
        volume_dir = OCR_ROOT / f"vol{volume}"
        if not volume_dir.is_dir():
            raise FileNotFoundError(f"Missing OCR directory: {volume_dir}")

        pages = sorted(volume_dir.glob("*.txt"), key=page_number)
        if not pages:
            raise ValueError(f"No OCR files found in {volume_dir}")

        seen: set[int] = set()
        volume_blocks: list[str] = []
        page_entries = []

        for path in pages:
            number = page_number(path)
            if number in seen:
                raise ValueError(
                    f"Duplicate page number {number} in Volume {volume}"
                )
            seen.add(number)

            relative_path = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8")
            block = page_block(volume, number, text)
            volume_blocks.append(block)
            corpus_blocks.append(block)
            page_entries.append(
                {
                    "page": number,
                    "file": relative_path,
                    "sha256": sha256(path),
                }
            )

        merged_path = (
            MERGED_ROOT
            / f"jacob-of-serugh-volume-{volume}-complete-qoruyo-ocr.txt"
        )
        merged_path.write_text("\n".join(volume_blocks), encoding="utf-8")

        manifest["volumes"].append(
            {
                "volume": volume,
                "page_count": len(pages),
                "merged_file": merged_path.relative_to(ROOT).as_posix(),
                "pages": page_entries,
            }
        )
        manifest["total_pages"] += len(pages)

    complete_path = ROOT / "jacob-of-serugh-complete-qoruyo-ocr.txt"
    complete_path.write_text("\n".join(corpus_blocks), encoding="utf-8")
    manifest["complete_merged_file"] = complete_path.relative_to(ROOT).as_posix()

    (ROOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Volumes: {len(manifest['volumes'])}")
    print(f"Page files: {manifest['total_pages']}")
    print(f"Complete OCR: {complete_path}")


if __name__ == "__main__":
    main()
