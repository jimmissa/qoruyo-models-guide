#!/usr/bin/env python3
"""Run Google Document AI Layout Parser on page images.

The script converts each one-page image to a one-page PDF, sends it to a
Document AI LAYOUT_PARSER_PROCESSOR, saves the raw response, and derives a
body-text candidate with adaptive coordinate-based block classification.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    from adaptive_layout_classifier import CLASSIFIER_VERSION, classify_document_pages
except ImportError:  # Allow importing this file as part of a package.
    from .adaptive_layout_classifier import CLASSIFIER_VERSION, classify_document_pages

PIPELINE_VERSION = "document-layout-v3"

@dataclass(frozen=True)
class PageImage:
    page_number: int
    image_path: Path
    pdf_path: Path
    raw_json_path: Path
    elements_json_path: Path
    body_text_path: Path
    body_crop_path: Path
    decisions_json_path: Path


@dataclass(frozen=True)
class VisualCropBounds:
    top: float | None
    bottom: float | None
    rule_groups: tuple[tuple[float, float, float], ...]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_config(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    return load_json(path)


def cfg_get(config: dict[str, Any], key: str, env_name: str | None = None) -> Any:
    value = config.get(key)
    if isinstance(value, str) and value.startswith("YOUR_"):
        value = ""
    if value:
        return value
    if env_name:
        return os.environ.get(env_name, "")
    return value


def resolve_path(base: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def page_sort_key(path: Path, page_number_regex: str) -> tuple[int, str]:
    match = re.search(page_number_regex, path.name)
    if not match:
        return (10**12, path.name)
    return (int(match.group(1)), path.name)


def discover_pages(
    source_dir: Path,
    output_dir: Path,
    file_glob: str,
    page_number_regex: str,
    start_page: int | None,
    end_page: int | None,
    limit: int | None,
) -> list[PageImage]:
    image_paths = sorted(source_dir.glob(file_glob), key=lambda p: page_sort_key(p, page_number_regex))
    pages: list[PageImage] = []

    for ordinal, image_path in enumerate(image_paths, start=1):
        match = re.search(page_number_regex, image_path.name)
        page_number = int(match.group(1)) if match else ordinal
        if start_page is not None and page_number < start_page:
            continue
        if end_page is not None and page_number > end_page:
            continue

        stem = image_path.stem
        pages.append(
            PageImage(
                page_number=page_number,
                image_path=image_path,
                pdf_path=output_dir / "page_pdfs" / f"{stem}.pdf",
                raw_json_path=output_dir / "raw_json" / f"{stem}.document.json",
                elements_json_path=output_dir / "layout_elements" / f"{stem}.elements.json",
                body_text_path=output_dir / "body_text_candidates" / f"{stem}.body.txt",
                body_crop_path=output_dir / "body_crops" / f"{stem}.body.png",
                decisions_json_path=output_dir / "block_decisions" / f"{stem}.decisions.json",
            )
        )

    if limit is not None:
        pages = pages[:limit]

    return pages


def convert_image_to_pdf(image_path: Path, pdf_path: Path, force: bool = False) -> None:
    if pdf_path.exists() and not force:
        return

    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is required. Run: pip install -r requirements_document_ai.txt") from exc

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(image_path) as img:
        rgb = img.convert("RGB")
        rgb.save(pdf_path, "PDF", resolution=300.0)


def create_documentai_client(location: str):
    try:
        from google.api_core.client_options import ClientOptions
        from google.cloud import documentai
    except ImportError as exc:
        raise RuntimeError(
            "google-cloud-documentai is required. Run: pip install -r requirements_document_ai.txt"
        ) from exc

    client_options = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
    return documentai.DocumentProcessorServiceClient(client_options=client_options), documentai


def build_process_options(documentai: Any, request_cfg: dict[str, Any]) -> Any:
    layout_kwargs: dict[str, Any] = {}

    if request_cfg.get("return_bounding_boxes") is not None:
        layout_kwargs["return_bounding_boxes"] = bool(request_cfg.get("return_bounding_boxes"))
    if request_cfg.get("return_images") is not None:
        layout_kwargs["return_images"] = bool(request_cfg.get("return_images"))
    if request_cfg.get("enable_image_annotation") is not None:
        layout_kwargs["enable_image_annotation"] = bool(request_cfg.get("enable_image_annotation"))
    if request_cfg.get("enable_table_annotation") is not None:
        layout_kwargs["enable_table_annotation"] = bool(request_cfg.get("enable_table_annotation"))

    chunk_size = request_cfg.get("chunk_size")
    if chunk_size:
        chunking_config = documentai.ProcessOptions.LayoutConfig.ChunkingConfig(
            chunk_size=int(chunk_size),
            include_ancestor_headings=bool(request_cfg.get("include_ancestor_headings", True)),
        )
        layout_kwargs["chunking_config"] = chunking_config

    if not layout_kwargs:
        return None

    layout_config = documentai.ProcessOptions.LayoutConfig(**layout_kwargs)
    return documentai.ProcessOptions(layout_config=layout_config)


def process_pdf_with_document_ai(
    pdf_path: Path,
    project_id: str,
    location: str,
    processor_id: str,
    processor_version_id: str | None,
    request_cfg: dict[str, Any],
) -> dict[str, Any]:
    from google.protobuf.json_format import MessageToDict

    client, documentai = create_documentai_client(location)

    if processor_version_id:
        name = client.processor_version_path(project_id, location, processor_id, processor_version_id)
    else:
        name = client.processor_path(project_id, location, processor_id)

    content = pdf_path.read_bytes()
    raw_document = documentai.RawDocument(content=content, mime_type="application/pdf")
    process_options = build_process_options(documentai, request_cfg)

    request_kwargs: dict[str, Any] = {
        "name": name,
        "raw_document": raw_document,
    }
    field_mask = request_cfg.get("field_mask")
    if field_mask:
        request_kwargs["field_mask"] = field_mask
    if process_options is not None:
        request_kwargs["process_options"] = process_options

    request = documentai.ProcessRequest(**request_kwargs)
    result = client.process_document(request=request)
    document = result.document

    return MessageToDict(
        document._pb,
        preserving_proto_field_name=True,
    )


def process_pdf_with_retries(
    *,
    pdf_path: Path,
    project_id: str,
    location: str,
    processor_id: str,
    processor_version_id: str | None,
    request_cfg: dict[str, Any],
) -> dict[str, Any]:
    """Retry transient per-page API failures without restarting the corpus."""
    max_attempts = int(request_cfg.get("max_page_attempts", 5) or 5)
    base_delay = float(request_cfg.get("page_retry_delay_seconds", 15.0) or 15.0)

    for attempt in range(1, max_attempts + 1):
        try:
            return process_pdf_with_document_ai(
                pdf_path=pdf_path,
                project_id=project_id,
                location=location,
                processor_id=processor_id,
                processor_version_id=processor_version_id,
                request_cfg=request_cfg,
            )
        except Exception as exc:
            message = str(exc)
            is_quota_error = any(
                marker in message.lower()
                for marker in ("resource_exhausted", "quota exceeded", "429", "rate limit")
            )
            if is_quota_error:
                print(f"  quota/rate-limit response: {type(exc).__name__}: {message}")

            if attempt >= max_attempts:
                raise

            delay = base_delay * attempt
            print(
                f"  API attempt {attempt}/{max_attempts} failed: "
                f"{type(exc).__name__}: {message}"
            )
            print(f"  retrying this page in {delay:.0f} second(s)")
            time.sleep(delay)

    raise RuntimeError("Unreachable retry state")


def text_from_anchor(anchor: dict[str, Any] | None, document_text: str) -> str:
    if not anchor:
        return ""
    pieces: list[str] = []
    for segment in anchor.get("text_segments", []) or []:
        start = int(segment.get("start_index", 0) or 0)
        end = int(segment.get("end_index", 0) or 0)
        if end > start:
            pieces.append(document_text[start:end])
    return "".join(pieces).strip()


def bounding_poly_to_box(layout: dict[str, Any]) -> dict[str, float] | None:
    poly = layout.get("bounding_poly") or layout.get("boundingBox") or layout.get("bounding_box") or {}
    vertices = (
        poly.get("normalized_vertices")
        or poly.get("normalizedVertices")
        or poly.get("vertices")
        or []
    )
    if not vertices:
        return None

    xs = [float(v.get("x", 0.0) or 0.0) for v in vertices]
    ys = [float(v.get("y", 0.0) or 0.0) for v in vertices]
    return {
        "x_min": min(xs),
        "x_max": max(xs),
        "y_min": min(ys),
        "y_max": max(ys),
    }


def normalize_label(label: str | None) -> str:
    return (label or "").replace("-", "_").replace(" ", "_").lower()


def extract_document_layout_elements(document_json: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract layout parser elements when DocumentLayout is present.

    The exact nested shape can vary by processor version, so this intentionally
    walks the JSON recursively and captures objects that have text anchors,
    layout labels, or bounding boxes.
    """

    document_text = document_json.get("text", "")
    elements: list[dict[str, Any]] = []

    def visit(obj: Any, path: str) -> None:
        if isinstance(obj, dict):
            layout = obj.get("layout") if isinstance(obj.get("layout"), dict) else obj
            text = ""
            if isinstance(layout, dict):
                text = text_from_anchor(layout.get("text_anchor"), document_text)
            text_block = {}
            if isinstance(obj.get("textBlock"), dict):
                text_block = obj["textBlock"]
            elif isinstance(obj.get("text_block"), dict):
                text_block = obj["text_block"]

            if not text:
                if isinstance(text_block.get("text"), str) and text_block.get("text", "").strip():
                    text = text_block.get("text", "").strip()
            if not text:
                for key in ("text", "content", "markdown_text"):
                    value = obj.get(key)
                    if isinstance(value, str) and value.strip():
                        text = value.strip()
                        break

            label = (
                obj.get("type")
                or obj.get("block_type")
                or obj.get("layout_type")
                or obj.get("detected_type")
                or obj.get("category")
                or obj.get("blockType")
                or text_block.get("type_")
                or text_block.get("type")
                or path.rsplit(".", 1)[-1]
            )
            box = bounding_poly_to_box(obj) or (bounding_poly_to_box(layout) if isinstance(layout, dict) else None)

            if text and (box or "chunked_document" in path or "chunkedDocument" in path):
                elements.append(
                    {
                        "label": normalize_label(str(label)),
                        "path": path,
                        "text": text,
                        "box": box,
                    }
                )

            for key, value in obj.items():
                visit(value, f"{path}.{key}" if path else key)
        elif isinstance(obj, list):
            for idx, value in enumerate(obj):
                visit(value, f"{path}[{idx}]")

    # Prefer DocumentLayout blocks because they preserve per-block geometry. The
    # chunked document is an aggregate intended for retrieval and can collapse a
    # whole page into one geometry-free text item.
    for root_key in ("document_layout", "documentLayout"):
        if root_key in document_json:
            visit(document_json[root_key], root_key)

    if not elements:
        for root_key in ("chunked_document", "chunkedDocument"):
            if root_key in document_json:
                visit(document_json[root_key], root_key)

    return dedupe_elements(elements)


def extract_page_line_elements(document_json: dict[str, Any]) -> list[dict[str, Any]]:
    document_text = document_json.get("text", "")
    elements: list[dict[str, Any]] = []

    for page_idx, page in enumerate(document_json.get("pages", []) or [], start=1):
        candidates = page.get("lines") or page.get("paragraphs") or page.get("blocks") or []
        for idx, item in enumerate(candidates, start=1):
            layout = item.get("layout", {}) if isinstance(item, dict) else {}
            text = text_from_anchor(layout.get("text_anchor"), document_text)
            if not text:
                continue
            elements.append(
                {
                    "label": "line_or_paragraph",
                    "path": f"pages[{page_idx}].items[{idx}]",
                    "text": text,
                    "box": bounding_poly_to_box(layout),
                }
            )

    return dedupe_elements(elements)


def dedupe_elements(elements: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, Any]] = []

    for element in elements:
        text = re.sub(r"\s+", " ", element.get("text", "")).strip()
        if not text:
            continue
        box_key = json.dumps(element.get("box"), sort_keys=True)
        key = (text, box_key)
        if key in seen:
            continue
        seen.add(key)
        element = dict(element)
        element["text"] = text
        deduped.append(element)

    return deduped


def extract_all_elements(document_json: dict[str, Any]) -> list[dict[str, Any]]:
    elements = extract_document_layout_elements(document_json)
    if not elements:
        elements = extract_page_line_elements(document_json)
    return elements


def _normalized_body_vertical_extent(
    body_elements: list[dict[str, Any]],
) -> tuple[float, float] | None:
    boxes = [element.get("box") for element in body_elements if element.get("box")]
    if not boxes:
        return None
    max_coord = max(
        max(abs(float(box[key])) for key in ("x_min", "x_max", "y_min", "y_max"))
        for box in boxes
    )
    if max_coord > 1.5:
        return None
    return (
        min(float(box["y_min"]) for box in boxes),
        max(float(box["y_max"]) for box in boxes),
    )


def detect_visual_crop_bounds(
    image_path: Path,
    body_elements: list[dict[str, Any]],
    min_rule_run_fraction: float = 0.35,
    header_rule_max_frame_fraction: float = 0.15,
) -> VisualCropBounds:
    """Infer header/footer separators from long horizontal printed rules.

    The detector is intentionally supplementary. It only constrains a crop
    when an interior rule is supported by the body geometry; otherwise it
    leaves the Document AI crop unchanged.
    """

    extent = _normalized_body_vertical_extent(body_elements)
    if extent is None:
        return VisualCropBounds(None, None, ())

    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is required. Run: pip install -r requirements_document_ai.txt") from exc

    with Image.open(image_path) as source:
        gray = source.convert("L")
        target_width = min(512, gray.width)
        target_height = max(1, round(gray.height * target_width / gray.width))
        gray = gray.resize((target_width, target_height), Image.Resampling.NEAREST)
        pixels = gray.load()

        sampled = sorted(
            pixels[x, y]
            for y in range(0, target_height, max(1, target_height // 80))
            for x in range(0, target_width, max(1, target_width // 60))
        )
        background = sampled[(3 * len(sampled)) // 4]
        dark_threshold = max(35, int(background) - 20)
        left = target_width // 20
        right = target_width - left
        row_width = max(1, right - left)
        gap_tolerance = max(1, target_width // 250)
        candidate_rows: list[tuple[int, float]] = []

        for y in range(target_height):
            run = best = gap = 0
            for x in range(left, right):
                if pixels[x, y] < dark_threshold:
                    run += 1
                    gap = 0
                elif run and gap < gap_tolerance:
                    run += 1
                    gap += 1
                else:
                    best = max(best, run - gap)
                    run = gap = 0
            best = max(best, run - gap)
            run_fraction = best / row_width
            if run_fraction >= min_rule_run_fraction:
                candidate_rows.append((y, run_fraction))

    groups: list[list[tuple[int, float]]] = []
    for row in candidate_rows:
        # A printed border is often double-stroked. Merge nearby rows before
        # deciding which rules are interior separators.
        if not groups or row[0] > groups[-1][-1][0] + 8:
            groups.append([row])
        else:
            groups[-1].append(row)

    rule_groups: list[tuple[float, float, float]] = []
    for group in groups:
        rule_groups.append(
            (
                group[0][0] / target_height,
                group[-1][0] / target_height,
                max(value for _, value in group),
            )
        )

    # With a bordered critical edition the first and last groups are the page
    # frame. Only rules between them may delimit a running head or apparatus.
    interior = rule_groups[1:-1] if len(rule_groups) >= 3 else []
    body_top, body_bottom = extent
    body_midpoint = (body_top + body_bottom) / 2.0

    frame_top = rule_groups[0][1] if rule_groups else 0.0
    frame_bottom = rule_groups[-1][0] if rule_groups else 1.0
    frame_height = max(frame_bottom - frame_top, 1e-6)
    top_candidates = [
        group
        for group in interior
        if group[1] <= body_top
        or (
            group[1] < body_midpoint
            and (group[1] - frame_top) / frame_height <= header_rule_max_frame_fraction
        )
    ]
    bottom_candidates = [
        group
        for group in interior
        if group[0] >= body_midpoint and group[0] <= body_bottom + 0.05
    ]

    # The first qualifying interior rule is the running-head separator. Taking
    # the first avoids mistaking a later internal section rule for a header.
    top = min(top_candidates, key=lambda group: group[0])[1] if top_candidates else None
    bottom = min(bottom_candidates, key=lambda group: group[0])[0] if bottom_candidates else None
    return VisualCropBounds(top, bottom, tuple(rule_groups))


def crop_body_image(
    image_path: Path,
    body_elements: list[dict[str, Any]],
    output_path: Path,
    padding_fraction: float,
    visual_bounds: VisualCropBounds | None = None,
) -> bool:
    boxes = [element.get("box") for element in body_elements if element.get("box")]
    if not boxes:
        return False

    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is required. Run: pip install -r requirements_document_ai.txt") from exc

    with Image.open(image_path) as img:
        width, height = img.size

        max_coord = max(
            max(abs(float(box[key])) for key in ("x_min", "x_max", "y_min", "y_max"))
            for box in boxes
        )
        normalized = max_coord <= 1.5

        if normalized:
            x_min = min(float(box["x_min"]) for box in boxes) * width
            x_max = max(float(box["x_max"]) for box in boxes) * width
            y_min = min(float(box["y_min"]) for box in boxes) * height
            y_max = max(float(box["y_max"]) for box in boxes) * height
            pad_x = padding_fraction * width
            pad_y = padding_fraction * height
        else:
            x_min = min(float(box["x_min"]) for box in boxes)
            x_max = max(float(box["x_max"]) for box in boxes)
            y_min = min(float(box["y_min"]) for box in boxes)
            y_max = max(float(box["y_max"]) for box in boxes)
            pad_x = padding_fraction * width
            pad_y = padding_fraction * height

        left = max(0, int(round(x_min - pad_x)))
        upper = max(0, int(round(y_min - pad_y)))
        right = min(width, int(round(x_max + pad_x)))
        lower = min(height, int(round(y_max + pad_y)))

        if visual_bounds and visual_bounds.top is not None:
            upper = max(upper, int(round(visual_bounds.top * height)))
        if visual_bounds and visual_bounds.bottom is not None:
            lower = min(lower, int(round(visual_bounds.bottom * height)))

        if right <= left or lower <= upper:
            return False

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.crop((left, upper, right, lower)).save(output_path)
        return True


def build_manifest(
    config: dict[str, Any],
    args: argparse.Namespace,
    pages: list[PageImage],
    project_id: str,
    location: str,
    processor_id: str,
    processor_version_id: str | None,
) -> dict[str, Any]:
    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": Path(__file__).name,
        "pipeline_version": PIPELINE_VERSION,
        "classifier_version": CLASSIFIER_VERSION,
        "project_id": project_id,
        "location": location,
        "processor_id": processor_id,
        "processor_version_id": processor_version_id or "",
        "source_dir": str(args.source_dir),
        "output_dir": str(args.output_dir),
        "start_page": args.start_page,
        "end_page": args.end_page,
        "limit": args.limit,
        "dry_run": args.dry_run,
        "config": config,
        "pages": [
            {
                "page_number": page.page_number,
                "image_path": str(page.image_path),
                "pdf_path": str(page.pdf_path),
                "raw_json_path": str(page.raw_json_path),
                "body_text_path": str(page.body_text_path),
                "body_crop_path": str(page.body_crop_path),
                "decisions_json_path": str(page.decisions_json_path),
            }
            for page in pages
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="Path to config JSON.")
    parser.add_argument("--project-id", help="Google Cloud project ID.")
    parser.add_argument("--location", help="Document AI processor location, usually us or eu.")
    parser.add_argument("--processor-id", help="Document AI Layout Parser processor ID.")
    parser.add_argument("--processor-version-id", default=None, help="Optional processor version ID.")
    parser.add_argument("--credentials", type=Path, help="Path to a service-account JSON key.")
    parser.add_argument("--source-dir", type=Path, help="Directory containing page images.")
    parser.add_argument("--output-dir", type=Path, help="Directory for outputs.")
    parser.add_argument("--file-glob", help="Input image glob; overrides config.")
    parser.add_argument("--page-number-regex", help="Regex with one capture group; unmatched files use sequence order.")
    parser.add_argument("--raw-json-file", type=Path, help="Process an already-exported Document AI JSON file instead of calling Google.")
    parser.add_argument("--image-file", type=Path, help="Source image corresponding to --raw-json-file.")
    parser.add_argument("--start-page", type=int, help="First page number to process.")
    parser.add_argument("--end-page", type=int, help="Last page number to process.")
    parser.add_argument("--limit", type=int, help="Limit number of pages after filtering.")
    parser.add_argument("--force", action="store_true", help="Reprocess even if raw JSON exists.")
    parser.add_argument("--dry-run", action="store_true", help="Discover pages and write manifest only.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    config = load_config(args.config)

    if args.credentials:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(args.credentials.expanduser().resolve())
    elif config.get("credentials_path"):
        credentials_path = resolve_path(script_dir, config.get("credentials_path"))
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credentials_path)

    project_id = args.project_id or cfg_get(config, "project_id", "GOOGLE_CLOUD_PROJECT")
    location = args.location or cfg_get(config, "location", "DOCUMENT_AI_LOCATION")
    processor_id = args.processor_id or cfg_get(config, "processor_id", "DOCUMENT_AI_PROCESSOR_ID")
    processor_version_id = (
        args.processor_version_id
        or config.get("processor_version_id")
        or os.environ.get("DOCUMENT_AI_PROCESSOR_VERSION_ID")
        or ""
    )

    source_dir = args.source_dir or resolve_path(script_dir, config.get("source_dir") or "..")
    output_dir = args.output_dir or resolve_path(script_dir, config.get("output_dir") or "document_ai_layout_output")
    if source_dir is None or output_dir is None:
        raise RuntimeError("Could not resolve source_dir/output_dir.")
    args.source_dir = source_dir
    args.output_dir = output_dir

    request_cfg = config.get("request", {})
    extraction_cfg = config.get("body_extraction", {})
    file_glob = args.file_glob or config.get("file_glob", "page_*.png")
    page_number_regex = args.page_number_regex or config.get("page_number_regex", r"(?:page[_-]?)?(\d+)")

    using_exported_json = args.raw_json_file is not None
    if using_exported_json:
        if args.image_file is None:
            raise RuntimeError("--image-file is required with --raw-json-file.")
        image_path = args.image_file.expanduser().resolve()
        raw_json_path = args.raw_json_file.expanduser().resolve()
        stem = image_path.stem
        match = re.search(page_number_regex, image_path.name)
        page_number = int(match.group(1)) if match else 1
        pages = [
            PageImage(
                page_number=page_number,
                image_path=image_path,
                pdf_path=output_dir / "page_pdfs" / f"{stem}.pdf",
                raw_json_path=raw_json_path,
                elements_json_path=output_dir / "layout_elements" / f"{stem}.elements.json",
                body_text_path=output_dir / "body_text_candidates" / f"{stem}.body.txt",
                body_crop_path=output_dir / "body_crops" / f"{stem}.body.png",
                decisions_json_path=output_dir / "block_decisions" / f"{stem}.decisions.json",
            )
        ]
    else:
        pages = discover_pages(
            source_dir=source_dir,
            output_dir=output_dir,
            file_glob=file_glob,
            page_number_regex=page_number_regex,
            start_page=args.start_page,
            end_page=args.end_page,
            limit=args.limit,
        )

    if not pages:
        print("No pages found.", file=sys.stderr)
        return 1

    print(f"Discovered {len(pages)} page(s): {pages[0].page_number} to {pages[-1].page_number}")

    manifest = build_manifest(
        config=config,
        args=args,
        pages=pages,
        project_id=project_id or "",
        location=location or "",
        processor_id=processor_id or "",
        processor_version_id=processor_version_id,
    )
    manifest_path = output_dir / "manifests" / f"run_manifest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    write_json(manifest_path, manifest)
    print(f"Wrote manifest: {manifest_path}")

    if args.dry_run:
        print("Dry run complete; no Google request was made.")
        return 0

    missing = [
        name
        for name, value in (
            ("project_id", project_id),
            ("location", location),
            ("processor_id", processor_id),
        )
        if not value
    ]
    if missing and not using_exported_json:
        raise RuntimeError(
            "Missing required Google Cloud settings: "
            + ", ".join(missing)
            + ". Fill document_ai_config.local.json or pass CLI arguments."
        )

    skip_existing = bool(request_cfg.get("skip_existing", True)) and not args.force
    sleep_seconds = float(request_cfg.get("sleep_seconds", 0.0) or 0.0)
    page_records: list[dict[str, Any]] = []

    for idx, page in enumerate(pages, start=1):
        print(f"[{idx}/{len(pages)}] Page {page.page_number}: {page.image_path.name}")

        if not using_exported_json:
            convert_image_to_pdf(page.image_path, page.pdf_path, force=args.force)

        if using_exported_json:
            document_json = load_json(page.raw_json_path)
            print(f"  using exported raw JSON: {page.raw_json_path}")
        elif page.raw_json_path.exists() and skip_existing:
            print(f"  using existing raw JSON: {page.raw_json_path.name}")
            document_json = load_json(page.raw_json_path)
        else:
            document_json = process_pdf_with_retries(
                pdf_path=page.pdf_path,
                project_id=project_id,
                location=location,
                processor_id=processor_id,
                processor_version_id=processor_version_id,
                request_cfg=request_cfg,
            )
            write_json(page.raw_json_path, document_json)
            print(f"  saved raw JSON: {page.raw_json_path.name}")

        all_elements = extract_all_elements(document_json)
        if not all_elements:
            raise RuntimeError(
                f"No coordinate-bearing layout blocks found in {page.raw_json_path}. "
                f"Top-level fields: {sorted(document_json)}. For batch output, ensure the "
                "GCS field mask includes documentLayout,chunkedDocument."
            )
        write_json(page.elements_json_path, all_elements)

        page_records.append(
            {
                "page": page,
                "page_number": page.page_number,
                "elements": all_elements,
            }
        )

        if sleep_seconds and idx < len(pages):
            time.sleep(sleep_seconds)

    strategy = str(extraction_cfg.get("strategy", "adaptive")).lower()
    if strategy != "adaptive":
        raise RuntimeError(f"Only the adaptive body extraction strategy is supported, not {strategy!r}")
    classified_pages = classify_document_pages(page_records, extraction_cfg)

    combined_sections: list[str] = []
    review_queue: list[dict[str, Any]] = []

    for record, classified in zip(page_records, classified_pages):
        page = record["page"]
        all_elements = record["elements"]
        body_elements = classified["body_elements"]
        body_text = "\n".join(element.get("text", "").strip() for element in body_elements).strip()
        decisions = classified["decisions"]
        visual_bounds = detect_visual_crop_bounds(
            page.image_path,
            body_elements,
            min_rule_run_fraction=float(
                extraction_cfg.get("visual_rule_min_run_fraction", 0.35)
            ),
            header_rule_max_frame_fraction=float(
                extraction_cfg.get("visual_header_rule_max_frame_fraction", 0.15)
            ),
        )

        write_json(page.decisions_json_path, decisions)
        write_json(
            output_dir / "visual_crop_bounds" / f"{page.image_path.stem}.visual_bounds.json",
            {
                "classifier_version": CLASSIFIER_VERSION,
                "top": visual_bounds.top,
                "bottom": visual_bounds.bottom,
                "rule_groups": [
                    {"y_min": start, "y_max": end, "run_fraction": run}
                    for start, end, run in visual_bounds.rule_groups
                ],
            },
        )
        write_text(page.body_text_path, body_text + ("\n" if body_text else ""))
        crop_written = crop_body_image(
            page.image_path,
            body_elements,
            page.body_crop_path,
            padding_fraction=float(extraction_cfg.get("crop_padding_fraction", 0.015)),
            visual_bounds=visual_bounds,
        )
        print(f"  body candidate lines: {len(body_text.splitlines()) if body_text else 0}")
        if crop_written:
            print(f"  saved body crop: {page.body_crop_path.name}")
        else:
            print("  no body crop written; no usable bounding boxes")

        combined_sections.append(f"===== PAGE {page.page_number} =====\n{body_text}".rstrip())
        review_queue.extend(
            {
                "page_number": page.page_number,
                **decision,
            }
            for decision in decisions
            if decision.get("action") == "review"
        )

    combined_path = output_dir / "combined_body_text.txt"
    write_text(combined_path, "\n\n".join(combined_sections).strip() + "\n")
    write_json(output_dir / "review_queue.json", review_queue)
    print(f"Saved combined body text: {combined_path}")
    print(f"Review queue: {len(review_queue)} ambiguous block(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
