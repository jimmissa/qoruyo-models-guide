# Isaac of Antioch: Qoruyo OCR Corpus

This is a complete page-level OCR corpus for the 837 prepared pages of the
1903 Isaac of Antioch edition used in this project. It is reproducible because
it preserves the complete chain from source page to OCR:

1. the original page photographs;
2. the cleaned and cropped page images supplied to Kraken; and
3. the Qoruyo OCR output generated from those prepared images.

## Contents

- `01_original_page_images/`: uncropped source-page PNGs.
- `02_prepared_page_crops/`: cleaned/cropped JPEG page images supplied to
  Kraken for OCR.
- `03_qoruyo_ocr/`: one UTF-8 plaintext transcription per prepared page.
- `isaac-of-antioch-complete-qoruyo-ocr.txt`: a numerically ordered merged
  transcription with explicit page markers.

The image and OCR filenames retain their page numbers, permitting direct
comparison from source image through crop to transcription.

## OCR workflow

The transcriptions were generated with the Qoruyo printed-page segmentation
model and the Qoruyo Eastern Syriac recognition model using Kraken. The
validated right-to-left settings were:

```bash
kraken -i page.jpg page.txt \
  segment -bl -i syr_print_seg03_91.mlmodel -d horizontal-rl \
  ocr -m SyrEastSyr_01_18.mlmodel --reorder --base-dir R
```

See the repository's [printed-text workflow](../../docs/printed-text-ocr.md)
and [right-to-left guidance](../../docs/right-to-left.md). The original model
records, rather than this repository, remain the authoritative sources for
the models and their metadata.

## Scope and reuse

This corpus is supplied for workflow transparency, inspection, and
reproducibility. The OCR is a derived transcription, not a critical edition,
and should be verified against the page images for scholarly citation or
editing. Consult
[`DATA_NOTICE.md`](DATA_NOTICE.md) before redistributing or repurposing the
page images for the source-edition and OCR attribution details.
