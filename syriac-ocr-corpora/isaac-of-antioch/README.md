# Isaac of Antioch: Qoruyo OCR Corpus

This is a complete page-level OCR corpus for the 837 prepared pages of the
1903 Isaac of Antioch edition by Paul Bedjan used in this project. It is reproducible because
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
- `batch_qoruyo_ocr.py`: a standalone command-line script for OCRing every
  supported image in a folder.
- `qoruyo_parallel_kaggle.ipynb`: a path-neutral Kaggle notebook for dividing
  a large image collection into deterministic parts processed on separate
  machines.

The image and OCR filenames retain their page numbers, permitting direct
comparison from source image through crop to transcription.

## Batch OCR helpers

After installing Kraken and downloading the appropriate Qoruyo models, OCR all
supported images in a local folder with:

```bash
python3 batch_qoruyo_ocr.py \
  --images-dir /path/to/page-images \
  --output-dir /path/to/ocr-output \
  --seg-model /path/to/syr_print_seg03_91.mlmodel \
  --ocr-model /path/to/recognition-model.mlmodel
```

Add `--recursive` to search image subdirectories. Existing nonempty OCR files
are skipped by default, making interrupted runs resumable; use `--overwrite`
to replace them.

For larger collections, open `qoruyo_parallel_kaggle.ipynb` in Kaggle. Set the
same `N_PARTS` on every machine and assign each machine a distinct
`PART_INDEX`. The notebook sorts images naturally, selects a deterministic
non-overlapping partition, performs batched OCR, skips completed files, and
exports that partition as a ZIP archive.

Including these workflows alongside the outputs provides an additional layer
of reproducibility: researchers can inspect the exact batch logic and rerun it
on their own image folders with their own model paths, rather than relying
only on the finished OCR files.

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
