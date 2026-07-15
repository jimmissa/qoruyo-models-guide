from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adaptive_layout_classifier import classify_document_pages
from run_document_ai_layout import detect_visual_crop_bounds


def element(text: str, y_min: float, y_max: float, x_min: float = 0.15, x_max: float = 0.9):
    return {
        "label": "paragraph",
        "text": text,
        "box": {"x_min": x_min, "x_max": x_max, "y_min": y_min, "y_max": y_max},
    }


class AdaptiveClassifierTests(unittest.TestCase):
    def classify(self, pages):
        return classify_document_pages(
            pages,
            {
                "min_syriac_chars": 2,
                "repeated_text_min_pages": 2,
                "page_number_row_height_multiplier": 1.5,
                "page_number_top_fraction": 0.2,
                "mixed_apparatus_fraction": 0.25,
                "apparatus_mixed_fraction": 0.05,
                "repeated_prefix_chars": 24,
                "review_policy": "keep",
                "exclude_labels_containing": ["header", "footer", "footnote", "page_number"],
            },
        )

    def test_page_number_row_removes_header_but_not_tall_body(self):
        pages = [
            {
                "page_number": 10,
                "elements": [
                    element("ܡܐܡܪܐ ܕܡܪܝ ܐܝܣܚܩ", 0.08, 0.11, 0.35, 0.70),
                    element("10", 0.09, 0.10, 0.15, 0.20),
                    element("ܗܢܐ ܗܘ ܦܓܪܐ ܕܡܐܡܪܐ " * 20, 0.13, 0.84),
                ],
            }
        ]
        decisions = self.classify(pages)[0]["decisions"]
        self.assertEqual(decisions[0]["reason"], "page_number_row_header")
        self.assertEqual(decisions[1]["reason"], "page_number")
        self.assertTrue(decisions[2]["keep"])

    def test_title_inside_body_flow_is_retained(self):
        pages = [
            {
                "page_number": 11,
                "elements": [
                    element("11", 0.08, 0.10, 0.15, 0.20),
                    element("ܦܓܪܐ ܕܡܐܡܪܐ " * 20, 0.13, 0.55),
                    element("ܡܐܡܪܐ ܥܠ ܒܝܬ ܚܘܪ", 0.66, 0.76, 0.30, 0.75),
                    element("ܫܘܪܝܐ ܕܡܐܡܪܐ", 0.80, 0.84),
                ],
            }
        ]
        body = self.classify(pages)[0]["body_elements"]
        self.assertEqual(len(body), 3)
        self.assertIn("ܡܐܡܪܐ ܥܠ ܒܝܬ ܚܘܪ", [item["text"] for item in body])

    def test_numbered_mixed_script_apparatus_is_removed(self):
        pages = [
            {
                "page_number": 12,
                "elements": [
                    element("12", 0.08, 0.10, 0.15, 0.20),
                    element("ܦܓܪܐ ܕܡܐܡܪܐ " * 20, 0.13, 0.82),
                    element("(2) ܘܡܟܣ Bk. (3) ܣܟܠܘܬܗ", 0.86, 0.90, 0.30, 0.80),
                ],
            }
        ]
        decisions = self.classify(pages)[0]["decisions"]
        self.assertIn(
            decisions[2]["reason"],
            {"critical_apparatus_signature", "mixed_script_numbered_apparatus"},
        )
        self.assertFalse(decisions[2]["keep"])

    def test_combined_header_and_expected_page_number_is_removed(self):
        pages = [
            {
                "page_number": 589,
                "elements": [
                    element("ܥܠ ܒܝܬ ܚܘܪ 589", 0.08, 0.10),
                    element("ܦܓܪܐ ܕܡܐܡܪܐ " * 20, 0.13, 0.83),
                ],
            }
        ]
        decisions = self.classify(pages)[0]["decisions"]
        self.assertEqual(decisions[0]["reason"], "header_combined_with_page_number")
        self.assertTrue(decisions[1]["keep"])

    def test_inline_number_cannot_turn_overlapping_body_into_header(self):
        pages = [
            {
                "page_number": 48,
                "elements": [
                    element("48", 0.06, 0.08, 0.78, 0.84),
                    element("ܦܠܓܘܬܐ ܕܡܪܝ ܐܝܣܚܩ", 0.06, 0.09, 0.30, 0.65),
                    element("ܦܓܪܐ ܕܡܐܡܪܐ " * 80, 0.11, 0.60),
                    element("69", 0.57, 0.59, 0.05, 0.10),
                    element("ܫܘܠܡܐ ܕܦܓܪܐ " * 20, 0.61, 0.84),
                ],
            }
        ]
        decisions = self.classify(pages)[0]["decisions"]
        self.assertEqual(decisions[0]["reason"], "page_number")
        self.assertTrue(decisions[2]["keep"])
        self.assertNotEqual(decisions[3]["reason"], "page_number")

    def test_repeated_header_prefix_is_removed_despite_varying_page_number(self):
        pages = []
        for page_number in (23, 25):
            pages.append(
                {
                    "page_number": page_number,
                    "elements": [
                        element(
                            f"ܡܡܠܠܐ ܡܘܬܪܢܐ ܕܥܠ ܐܘܪܚܐ ܕܕܝܪܝܘܬܐ {page_number}",
                            0.06,
                            0.09,
                        ),
                        element("ܦܓܪܐ ܕܡܐܡܪܐ " * 40, 0.12, 0.84),
                    ],
                }
            )
        results = self.classify(pages)
        for result in results:
            self.assertFalse(result["decisions"][0]["keep"])
            self.assertTrue(result["decisions"][1]["keep"])

    def test_header_prefix_merged_with_substantial_body_is_retained(self):
        repeated = "ܡܡܠܠܐ ܡܘܬܪܢܐ ܕܥܠ ܐܘܪܚܐ ܕܕܝܪܝܘܬܐ"
        pages = [
            {
                "page_number": 235,
                "elements": [
                    element(f"{repeated} 235 " + "ܦܓܪܐ ܕܡܐܡܪܐ " * 45, 0.06, 0.39),
                    element("ܬܘܒ ܦܓܪܐ ܕܡܐܡܪܐ " * 20, 0.40, 0.88),
                ],
            },
            {
                "page_number": 237,
                "elements": [
                    element(f"{repeated} 237", 0.06, 0.09),
                    element("ܦܓܪܐ ܕܡܐܡܪܐ " * 45, 0.12, 0.88),
                ],
            },
        ]
        results = self.classify(pages)
        self.assertTrue(results[0]["decisions"][0]["keep"])
        self.assertFalse(results[1]["decisions"][0]["keep"])

    def test_visual_header_rule_survives_merged_header_body_block(self):
        from PIL import Image, ImageDraw

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "page.png"
            image = Image.new("L", (500, 1000), 240)
            draw = ImageDraw.Draw(image)
            draw.line((25, 40, 475, 40), fill=20, width=3)
            draw.line((25, 90, 475, 90), fill=20, width=2)
            draw.line((25, 910, 475, 910), fill=20, width=3)
            image.save(path)

            bounds = detect_visual_crop_bounds(
                path,
                [element("ܡܡܠܠܐ " * 100, 0.06, 0.85)],
            )
            self.assertIsNotNone(bounds.top)
            self.assertAlmostEqual(bounds.top, 0.09, delta=0.015)

if __name__ == "__main__":
    unittest.main()
