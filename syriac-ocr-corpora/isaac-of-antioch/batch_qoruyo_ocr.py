#!/usr/bin/env python3
"""Batch OCR every supported image in a folder with Qoruyo and Kraken."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def natural_key(path: Path) -> list[object]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.name)]


def batches(items: list[Path], size: int):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def discover_images(image_dir: Path, recursive: bool) -> list[Path]:
    candidates = image_dir.rglob("*") if recursive else image_dir.glob("*")
    images = sorted(
        (path for path in candidates if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES),
        key=natural_key,
    )

    duplicate_stems: dict[str, list[Path]] = {}
    for path in images:
        duplicate_stems.setdefault(path.stem, []).append(path)
    conflicts = {stem: paths for stem, paths in duplicate_stems.items() if len(paths) > 1}
    if conflicts:
        names = ", ".join(sorted(conflicts))
        raise ValueError(f"Duplicate image stems would overwrite OCR output: {names}")

    return images


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images-dir", type=Path, required=True, help="Folder containing page images.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Folder for page-level OCR text files.")
    parser.add_argument("--seg-model", type=Path, required=True, help="Qoruyo printed-text segmentation model.")
    parser.add_argument("--ocr-model", type=Path, required=True, help="Qoruyo recognition model for the page script.")
    parser.add_argument("--batch-size", type=int, default=50, help="Images passed to each Kraken process (default: 50).")
    parser.add_argument("--kraken-bin", default="kraken", help="Kraken executable name or path.")
    parser.add_argument("--recursive", action="store_true", help="Search image subdirectories recursively.")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing nonempty OCR files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.batch_size < 1:
        raise ValueError("--batch-size must be at least 1")

    for path, label in ((args.images_dir, "image directory"), (args.seg_model, "segmentation model"), (args.ocr_model, "OCR model")):
        if not path.exists():
            raise FileNotFoundError(f"Missing {label}: {path}")

    images = discover_images(args.images_dir, args.recursive)
    if not images:
        raise FileNotFoundError(f"No supported images found in {args.images_dir}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
    failures: list[tuple[int, int, int]] = []

    print(f"Found {len(images)} image(s)")
    for batch_number, image_batch in enumerate(batches(images, args.batch_size), start=1):
        command = [args.kraken_bin]
        queued: list[Path] = []

        for image_path in image_batch:
            output_path = args.output_dir / f"{image_path.stem}.txt"
            if not args.overwrite and output_path.exists() and output_path.stat().st_size > 0:
                continue
            command.extend(["-i", str(image_path), str(output_path)])
            queued.append(image_path)

        if not queued:
            print(f"Batch {batch_number}: already complete")
            continue

        command.extend(
            [
                "segment",
                "-bl",
                "-i",
                str(args.seg_model),
                "-d",
                "horizontal-rl",
                "ocr",
                "-m",
                str(args.ocr_model),
                "--reorder",
                "--base-dir",
                "R",
            ]
        )

        print(f"Batch {batch_number}: OCRing {len(queued)} image(s), {queued[0].name} through {queued[-1].name}")
        result = subprocess.run(command, env=environment, text=True, capture_output=True)
        if result.returncode != 0:
            failures.append((batch_number, len(queued), result.returncode))
            print(result.stdout)
            print(result.stderr)
        else:
            print(f"Batch {batch_number}: complete")

    created = sum(1 for path in args.output_dir.glob("*.txt") if path.stat().st_size > 0)
    print(f"OCR files present: {created}")
    if failures:
        raise RuntimeError(f"Failed batches: {failures}")


if __name__ == "__main__":
    main()
