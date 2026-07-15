# Syriac OCR Corpora

This directory contains author-level Syriac OCR corpora used to demonstrate,
validate, and preserve the Kraken workflows documented in this repository.
Where available, a corpus keeps the linked evidence chain from page image to
OCR output:

1. the original page photographs;
2. the cleaned and cropped images actually supplied to Kraken; and
3. the resulting page-level Qoruyo OCR, plus a merged text file when available.

When the original edition is not already supplied as clean page images, one
reproducible way to create the prepared-image stage is the optional
[`document-ai-preprocessing/`](../document-ai-preprocessing/) workflow. It
uses Google Document AI's Layout Parser, applies coordinate-based block
classification, writes body-only crops, and can create an interleaved
original/crop PDF for human review before Qoruyo OCR.

[`isaac-of-antioch/`](isaac-of-antioch/) contains the complete 837-page Isaac
of Antioch corpus with source images, prepared crops, and OCR.
[`jacob-of-serugh/`](jacob-of-serugh/) contains 4,668 page-level OCR files from
six volumes, together with one directly accessible merged text per volume. Its
page images are not included in the current text-only release.

[`NEXT_OCR_TARGETS.md`](NEXT_OCR_TARGETS.md) lists additional public-domain
Syriac text editions that are good candidates for future OCR expansion.

[`isaac-of-nineveh/`](isaac-of-nineveh/) currently contains the 638 uncropped
source page images for the Isaac of Nineveh edition documented at Archive.org.
Its prepared crops and Qoruyo OCR are intentionally withheld until those
downstream stages are ready for release.
