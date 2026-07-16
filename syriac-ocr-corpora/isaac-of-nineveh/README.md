# Isaac of Nineveh: Qoruyo OCR Corpus

This directory contains the 638 source-page images, prepared page crops, and
replacement Qoruyo OCR for the Isaac of Nineveh edition documented at
[Archive.org](https://archive.org/details/deperfectionerel0000isaa). Page numbers
are retained in both image and OCR filenames for direct comparison.

## Contents

- `01_original_source/README.md`: documentation for the source edition.
- `01_original_source/uncropped_photos/`: 638 page images preserving the
  original page framing and page numbering.
- `02_prepared_page_crops/isaac-of-nineveh-prepared-page-crops.zip`: one ZIP
  archive containing all 638 body crops supplied to the OCR workflow.
- `03_qoruyo_ocr/`: one UTF-8 Qoruyo OCR text file per page, numbered 1-638.
- `isaac-of-nineveh-complete-qoruyo-ocr.txt`: the complete OCR in numerical
  page order with explicit page markers.
- `ocr_manifest.json`: page coverage, archive-part provenance, and SHA-256
  checksums for the five source archives and all page-level OCR files.

The page-level files preserve the replacement OCR output as generated. The
merged file removes empty lines and lines containing only an integer, which
eliminates isolated OCR page-number noise while retaining the Syriac text.
The crop archive is stored through Git LFS because its size exceeds GitHub's
normal per-file limit; a Git LFS-enabled clone retrieves the complete ZIP.

For a general reproducible route from uncropped page images to prepared crops,
see the repository's optional
[`document-ai-preprocessing/`](../../document-ai-preprocessing/) workflow. It
can apply the same layout-based preparation approach to this or another
edition, followed by human review before OCR.

The OCR is a machine-generated transcription rather than a critical edition.
Consult the page images when verifying readings for scholarly use.
