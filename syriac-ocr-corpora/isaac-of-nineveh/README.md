# Isaac of Nineveh: Qoruyo OCR Corpus

This directory contains the prepared page images and, subsequently, the
Qoruyo OCR output for the Isaac of Nineveh edition documented at
[Archive.org](https://archive.org/details/deperfectionerel0000isaa).

## Contents

- `01_original_source/`: documentation for the external uncropped source.
- `02_prepared_page_crops/`: direct body crops supplied to Kraken/Qoruyo.
- `03_qoruyo_ocr/`: page-level OCR output, to be added after the Kaggle OCR
  run.
- `isaac-of-nineveh-complete-qoruyo-ocr.txt`: merged OCR output, to be added
  after page-level OCR is complete.

The prepared image filenames preserve the original page numbers. This permits
page-by-page comparison between the source, cleaned crop, and later OCR text.

For a general reproducible route from uncropped page images to prepared crops,
see the repository's optional
[`document-ai-preprocessing/`](../../document-ai-preprocessing/) workflow. It
can apply the same layout-based preparation approach to this or another
edition, followed by human review before OCR.

The OCR will use the Qoruyo printed-page segmentation model and the Qoruyo
Eastern Syriac recognition model with these validated Kraken settings:

```bash
kraken -i page.png page.txt \
  segment -bl -i syr_print_seg03_91.mlmodel -d horizontal-rl \
  ocr -m SyrEastSyr_01_18.mlmodel --reorder --base-dir R
```

The OCR is a machine-generated transcription and should be checked against the
source images before scholarly citation.
