"""Adaptive document-layout classification from Document AI block geometry.

The classifier avoids page-specific crop coordinates. It derives header, body,
and apparatus evidence from normalized geometry, relationships among blocks on
the same page, and repeated blocks across the document.
"""

from __future__ import annotations

import math
import re
import statistics
import unicodedata
from collections import Counter, defaultdict
from typing import Any, Iterable

SYRIAC_RE = re.compile(r"[\u0700-\u074F\u0860-\u086F]")
NUMBER_TOKEN_RE = re.compile(r"(?<!\d)(\d{1,5})(?!\d)")
APPARATUS_PREFIX_RE = re.compile(
    r"^\s*[\(\[\{]\s*(?:\d{1,3}|['*†‡\-–—]+)?\s*[\)\]\}]"
)
LATIN_SIGLA_RE = re.compile(
    r"(?:^|[\s.])(?:M|V|S|R|L|A)(?:[\s.]|$)|"
    r"\b(?:Sic|Om|marg|textu|leg)\b",
    re.IGNORECASE,
)
CLASSIFIER_VERSION = "adaptive-layout-v3"


def normalize_label(label: str | None) -> str:
    return (label or "").replace("-", "_").replace(" ", "_").lower()


def syriac_char_count(text: str) -> int:
    return len(SYRIAC_RE.findall(text or ""))


def has_digit(text: str) -> bool:
    return any(ch.isdigit() for ch in text or "")


def latin_digit_fraction(text: str) -> float:
    non_space = [ch for ch in text or "" if not ch.isspace()]
    if not non_space:
        return 0.0
    count = sum(
        1
        for ch in non_space
        if ch.isascii() and (ch.isalnum() or ch in "().,;:[]-'")
    )
    return count / len(non_space)


def looks_like_page_number(text: str) -> bool:
    return bool(re.fullmatch(r"[\[\(\-–—\s]*\d{1,5}[\]\)\-–—\s]*", (text or "").strip()))


def box_width(box: dict[str, float] | None) -> float:
    return max(0.0, float(box["x_max"]) - float(box["x_min"])) if box else 0.0


def box_height(box: dict[str, float] | None) -> float:
    return max(0.0, float(box["y_max"]) - float(box["y_min"])) if box else 0.0


def box_area(box: dict[str, float] | None) -> float:
    return box_width(box) * box_height(box)


def y_center(box: dict[str, float] | None) -> float:
    return (float(box["y_min"]) + float(box["y_max"])) / 2.0 if box else math.inf


def vertical_overlap(a: dict[str, float] | None, b: dict[str, float] | None) -> float:
    if not a or not b:
        return 0.0
    overlap = min(float(a["y_max"]), float(b["y_max"])) - max(
        float(a["y_min"]), float(b["y_min"])
    )
    return max(0.0, overlap)


def same_row(
    a: dict[str, float] | None,
    b: dict[str, float] | None,
    height_multiplier: float,
) -> bool:
    if not a or not b:
        return False
    if vertical_overlap(a, b) > 0:
        return True
    # A very tall body block can begin close to a page number but must not be
    # treated as sharing its row. The smaller block height represents the row
    # scale far better than the larger one in that case.
    scale = max(min(box_height(a), box_height(b)), 1e-6)
    return abs(y_center(a) - y_center(b)) <= height_multiplier * scale


def canonical_repeated_text(text: str) -> str:
    chars: list[str] = []
    for ch in unicodedata.normalize("NFD", text or ""):
        if unicodedata.category(ch).startswith("M") or ch.isdigit():
            continue
        if ch.isalnum() or SYRIAC_RE.match(ch):
            chars.append(ch.lower())
        elif ch.isspace():
            chars.append(" ")
    return re.sub(r"\s+", " ", "".join(chars)).strip()


def unmarked_syriac(text: str) -> str:
    return "".join(
        ch
        for ch in unicodedata.normalize("NFD", text or "")
        if not unicodedata.category(ch).startswith("M")
    )


def looks_like_critical_apparatus(text: str, mixed_fraction: float) -> bool:
    """Return true for strong, edition-independent critical-note signals."""

    plain = unmarked_syriac(text)
    starts_with_marker = bool(APPARATUS_PREFIX_RE.search(text or ""))
    has_note_label = "ܢܘܗܪ" in plain
    has_latin_sigla = bool(LATIN_SIGLA_RE.search(text or ""))
    return starts_with_marker and (
        has_note_label or has_latin_sigla or latin_digit_fraction(text) >= mixed_fraction
    )


def reading_order(element: dict[str, Any]) -> tuple[float, float, str]:
    box = element.get("box")
    if not box:
        return (math.inf, math.inf, element.get("text", ""))
    return (float(box["y_min"]), -float(box["x_max"]), element.get("text", ""))


def _median(values: Iterable[float], default: float = 0.0) -> float:
    values = [value for value in values if value > 0]
    return statistics.median(values) if values else default


def _document_repetitions(pages: list[dict[str, Any]]) -> Counter[str]:
    appearances: dict[str, set[int]] = defaultdict(set)
    for page in pages:
        page_number = int(page["page_number"])
        for element in page["elements"]:
            canonical = canonical_repeated_text(element.get("text", ""))
            if canonical:
                appearances[canonical].add(page_number)
    return Counter({text: len(page_numbers) for text, page_numbers in appearances.items()})


def _document_prefix_repetitions(
    pages: list[dict[str, Any]],
    prefix_chars: int,
) -> Counter[str]:
    appearances: dict[str, set[int]] = defaultdict(set)
    for page in pages:
        page_number = int(page["page_number"])
        for element in page["elements"]:
            canonical = canonical_repeated_text(element.get("text", ""))
            if len(canonical) >= prefix_chars:
                appearances[canonical[:prefix_chars]].add(page_number)
    return Counter({text: len(page_numbers) for text, page_numbers in appearances.items()})


def _page_number_markers(
    elements: list[dict[str, Any]],
    page_number: int | None,
    fallback_top_fraction: float,
) -> set[int]:
    markers: set[int] = set()
    ordered_indices = sorted(range(len(elements)), key=lambda idx: reading_order(elements[idx]))
    early_indices = set(ordered_indices[: max(2, min(4, len(ordered_indices)))])
    median_height = _median(
        [box_height(element.get("box")) for element in elements],
        default=1.0,
    )
    body_anchor = max(
        (
            element
            for element in elements
            if element.get("box") and syriac_char_count(element.get("text", "")) >= 2
        ),
        key=lambda element: syriac_char_count(element.get("text", ""))
        * (1.0 + math.sqrt(box_area(element.get("box")))),
        default=None,
    )
    # The dominant Syriac block supplies a document-specific top boundary.
    # The configured fraction is only a fallback for pages without a usable
    # body block, such as blank or heavily damaged pages.
    top_boundary = (
        float(body_anchor["box"]["y_min"])
        if body_anchor is not None
        else fallback_top_fraction
    )

    for idx, element in enumerate(elements):
        text = element.get("text", "").strip()
        box = element.get("box")
        above_body = (
            bool(box)
            and float(box["y_max"]) <= top_boundary
            and float(box["y_max"]) <= fallback_top_fraction
        )
        if looks_like_page_number(text):
            numbers = {int(value) for value in NUMBER_TOKEN_RE.findall(text)}
            # Isolated numbers also occur in critical apparatus and inside body
            # paragraphs as footnote markers. Page numbers must therefore be
            # geometrically confined above the dominant body and to a broad,
            # configurable top safety band. This remains robust when image
            # sequence numbers differ from the printed pagination.
            if above_body:
                markers.add(idx)
            continue

        numbers = {int(value) for value in NUMBER_TOKEN_RE.findall(text)}
        contains_expected = page_number is not None and page_number in numbers
        short_early_numbered_block = (
            bool(numbers)
            and idx in early_indices
            and above_body
            and box_height(element.get("box")) <= median_height
        )
        if (contains_expected and idx in early_indices and above_body) or short_early_numbered_block:
            markers.add(idx)

    return markers


def classify_document_pages(
    pages: list[dict[str, Any]],
    config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Classify all blocks for a document.

    Input pages must contain ``page_number`` and ``elements``. Each output page
    contains ``decisions`` and ``body_elements``. Ambiguous blocks follow the
    configured review policy (``keep`` by default) and remain explicitly marked
    for later inspection.
    """

    cfg = config or {}
    min_syriac = int(cfg.get("min_syriac_chars", 2))
    repeat_min_pages = int(cfg.get("repeated_text_min_pages", 2))
    row_height_multiplier = float(cfg.get("page_number_row_height_multiplier", 1.5))
    mixed_fraction = float(cfg.get("mixed_apparatus_fraction", 0.25))
    apparatus_mixed_fraction = float(cfg.get("apparatus_mixed_fraction", 0.05))
    repeated_prefix_chars = int(cfg.get("repeated_prefix_chars", 24))
    page_number_top_fraction = float(cfg.get("page_number_top_fraction", 0.20))
    review_policy = str(cfg.get("review_policy", "keep")).lower()
    excluded_labels = [normalize_label(value) for value in cfg.get("exclude_labels_containing", [])]
    overrides = cfg.get("overrides", {})

    repetitions = _document_repetitions(pages)
    prefix_repetitions = _document_prefix_repetitions(pages, repeated_prefix_chars)
    results: list[dict[str, Any]] = []

    for page in pages:
        page_number = int(page["page_number"])
        elements = page["elements"]
        page_overrides = overrides.get(str(page_number), {})
        markers = _page_number_markers(elements, page_number, page_number_top_fraction)
        marker_boxes = [elements[idx].get("box") for idx in markers if elements[idx].get("box")]

        heights = [box_height(element.get("box")) for element in elements]
        median_height = _median(heights, default=1.0)
        preliminary: list[dict[str, Any]] = []

        for idx, element in enumerate(elements):
            text = element.get("text", "").strip()
            label = normalize_label(element.get("label", ""))
            box = element.get("box")
            syriac_chars = syriac_char_count(text)
            mixed = latin_digit_fraction(text)
            canonical = canonical_repeated_text(text)
            repeated_pages = repetitions.get(canonical, 0)
            repeated_prefix_pages = prefix_repetitions.get(
                canonical[:repeated_prefix_chars],
                0,
            ) if len(canonical) >= repeated_prefix_chars else 0

            action = "keep"
            reason = "syriac_body_candidate"
            confidence = 0.80

            override = page_overrides.get(str(idx))
            if override in {"keep", "drop", "review"}:
                action = override
                reason = "manual_override"
                confidence = 1.0
            elif any(excluded in label for excluded in excluded_labels):
                action, reason, confidence = "drop", "layout_label_excluded", 0.98
            elif idx in markers:
                if looks_like_page_number(text):
                    action, reason, confidence = "drop", "page_number", 1.0
                else:
                    action, reason, confidence = "drop", "header_combined_with_page_number", 0.98
            elif any(same_row(box, marker_box, row_height_multiplier) for marker_box in marker_boxes):
                action, reason, confidence = "drop", "page_number_row_header", 0.96
            elif looks_like_critical_apparatus(text, apparatus_mixed_fraction):
                action, reason, confidence = "drop", "critical_apparatus_signature", 0.97
            elif syriac_chars < min_syriac:
                action, reason, confidence = "drop", "insufficient_syriac", 0.98
            elif has_digit(text) and mixed >= mixed_fraction:
                action, reason, confidence = "drop", "mixed_script_numbered_apparatus", 0.94
            elif repeated_pages >= repeat_min_pages:
                action, reason, confidence = "review", "repeated_document_text", 0.70
            elif repeated_prefix_pages >= repeat_min_pages:
                action, reason, confidence = "review", "repeated_document_prefix", 0.72
            elif not box:
                action, reason, confidence = "review", "missing_geometry", 0.55

            preliminary.append(
                {
                    "index": idx,
                    "classifier_version": CLASSIFIER_VERSION,
                    "action": action,
                    "keep": action == "keep" or (action == "review" and review_policy == "keep"),
                    "reason": reason,
                    "confidence": round(confidence, 3),
                    "label": element.get("label"),
                    "text": text,
                    "box": box,
                    "features": {
                        "syriac_chars": syriac_chars,
                        "latin_digit_fraction": round(mixed, 4),
                        "has_digit": has_digit(text),
                        "width": round(box_width(box), 6),
                        "height": round(box_height(box), 6),
                        "area": round(box_area(box), 6),
                        "height_vs_page_median": round(box_height(box) / median_height, 4)
                        if median_height
                        else None,
                        "repeated_on_pages": repeated_pages,
                        "repeated_prefix_on_pages": repeated_prefix_pages,
                    },
                }
            )

        # A repeated block is a header/footer only when it sits before or after
        # the page's dominant body block. Repeated phrases within the body are
        # retained but flagged for review.
        body_seed_indices = [
            item["index"]
            for item in preliminary
            if item["action"] == "keep" and item["box"]
        ]
        seed_idx = max(
            body_seed_indices,
            key=lambda idx: syriac_char_count(elements[idx].get("text", ""))
            * (1.0 + math.sqrt(box_area(elements[idx].get("box")))),
            default=None,
        )
        seed_box = elements[seed_idx].get("box") if seed_idx is not None else None
        seed_syriac_chars = (
            syriac_char_count(elements[seed_idx].get("text", ""))
            if seed_idx is not None
            else 0
        )

        for item in preliminary:
            if item["action"] != "review" or item["reason"] not in {
                "repeated_document_text",
                "repeated_document_prefix",
            }:
                continue
            box = item["box"]
            short_relative_to_body = (
                item["features"]["syriac_chars"]
                <= max(120, int(seed_syriac_chars * 0.25))
                and box_height(box) <= max(median_height * 3.0, 0.08)
            )
            if seed_box and box and short_relative_to_body and (
                float(box["y_max"]) <= float(seed_box["y_min"])
                or float(box["y_min"]) >= float(seed_box["y_max"])
            ):
                item["action"] = "drop"
                item["keep"] = False
                item["reason"] = "repeated_running_header_or_footer"
                item["confidence"] = 0.90

        body_elements = [
            elements[item["index"]]
            for item in preliminary
            if item["keep"]
        ]
        results.append(
            {
                "page_number": page_number,
                "classifier_version": CLASSIFIER_VERSION,
                "decisions": preliminary,
                "body_elements": sorted(body_elements, key=reading_order),
                "review_count": sum(item["action"] == "review" for item in preliminary),
            }
        )

    return results
