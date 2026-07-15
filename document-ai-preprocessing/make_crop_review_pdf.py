#!/usr/bin/env python3
"""Create an interleaved original/crop review PDF."""

from __future__ import annotations

import argparse
from io import BytesIO
import re
from pathlib import Path

from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def page_number(path: Path, pattern: re.Pattern[str]) -> int | None:
    match = pattern.search(path.name)
    return int(match.group(1)) if match else None


def discover_images(
    directory: Path,
    file_glob: str,
    page_pattern: re.Pattern[str],
) -> dict[int, Path]:
    pages: dict[int, Path] = {}
    for path in directory.glob(file_glob):
        if not path.is_file():
            continue
        number = page_number(path, page_pattern)
        if number is None:
            continue
        if number in pages:
            raise RuntimeError(f"Duplicate page number {number} in {directory}")
        pages[number] = path
    return pages


def fit_dimensions(
    image_path: Path,
    max_width: float,
    max_height: float,
) -> tuple[float, float]:
    with Image.open(image_path) as image:
        width, height = image.size
    scale = min(max_width / width, max_height / height)
    return width * scale, height * scale


def review_image(image_path: Path, max_pixels: int, jpeg_quality: int) -> ImageReader:
    """Return a compact JPEG-backed image suitable for visual review."""
    image = Image.open(image_path).convert("RGB")
    image.thumbnail((max_pixels, max_pixels), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=jpeg_quality, optimize=True)
    buffer.seek(0)
    return ImageReader(buffer)


def make_review_pdf(
    source_dir: Path,
    cropped_dir: Path,
    output_path: Path,
    source_glob: str,
    cropped_glob: str,
    page_regex: str,
    start_page: int | None,
    end_page: int | None,
    max_pixels: int,
    jpeg_quality: int,
) -> None:
    pattern = re.compile(page_regex)
    source_pages = discover_images(source_dir, source_glob, pattern)
    cropped_pages = discover_images(cropped_dir, cropped_glob, pattern)

    page_numbers = sorted(set(source_pages) & set(cropped_pages))
    page_numbers = [
        number
        for number in page_numbers
        if (start_page is None or number >= start_page)
        and (end_page is None or number <= end_page)
    ]

    missing_crops = sorted(set(source_pages) - set(cropped_pages))
    missing_sources = sorted(set(cropped_pages) - set(source_pages))
    if missing_crops or missing_sources:
        raise RuntimeError(
            "Source/crop page mismatch. "
            f"Missing crops: {missing_crops[:10]}; "
            f"missing sources: {missing_sources[:10]}"
        )
    if not page_numbers:
        raise RuntimeError("No matching page pairs found.")

    page_width, page_height = letter
    margin = 18
    image_max_height = page_height - 2 * margin

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=(page_width, page_height))
    pdf.setTitle("Document AI Crop Review")
    pdf.setAuthor("Syriac Translation Project")
    # Put the cropped page on the left and its source page on the right in
    # viewers that honor the PDF two-page layout preference.
    pdf._doc.Catalog.setPageLayout("TwoPageLeft")
    pdf._doc.Catalog.setPageMode("UseNone")

    for number in page_numbers:
        source_path = source_pages[number]
        cropped_path = cropped_pages[number]

        # Consecutive pages form each review pair: crop first, source second.
        for image_path in (cropped_path, source_path):
            review_image_data = review_image(image_path, max_pixels, jpeg_quality)
            draw_width, draw_height = fit_dimensions(
                image_path,
                page_width - 2 * margin,
                image_max_height,
            )
            draw_x = (page_width - draw_width) / 2
            draw_y = (page_height - draw_height) / 2
            pdf.drawImage(
                review_image_data,
                draw_x,
                draw_y,
                width=draw_width,
                height=draw_height,
                preserveAspectRatio=True,
                mask="auto",
            )
            pdf.showPage()

    pdf.save()
    print(f"Created {output_path} with {len(page_numbers)} review pages.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--cropped-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-glob", default="*.png")
    parser.add_argument("--cropped-glob", default="*.body.png")
    parser.add_argument("--page-regex", default=r"page[_-](\d+)")
    parser.add_argument("--start-page", type=int)
    parser.add_argument("--end-page", type=int)
    parser.add_argument(
        "--max-pixels",
        type=int,
        default=600,
        help="Maximum width or height embedded for each review image (default: 600).",
    )
    parser.add_argument(
        "--jpeg-quality",
        type=int,
        default=75,
        help="JPEG quality for embedded review images (default: 75).",
    )
    args = parser.parse_args()

    make_review_pdf(
        source_dir=args.source_dir,
        cropped_dir=args.cropped_dir,
        output_path=args.output,
        source_glob=args.source_glob,
        cropped_glob=args.cropped_glob,
        page_regex=args.page_regex,
        start_page=args.start_page,
        end_page=args.end_page,
        max_pixels=args.max_pixels,
        jpeg_quality=args.jpeg_quality,
    )


if __name__ == "__main__":
    main()
