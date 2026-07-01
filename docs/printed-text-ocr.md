# Printed-text OCR with Qoruyo

## Choose the recognition model

Use the common printed-text segmentation model with one script-specific
recognition model:

- Serto: `serto_print_best_02.mlmodel`
- Estrangela: `SyrEstr_02_34.mlmodel`
- Eastern Syriac: `SyrEastSyr_01_18.mlmodel`

The segmentation model is `syr_print_seg03_91.mlmodel` in all three cases.

## Standard page workflow

```bash
kraken \
  -i page.png page.txt \
  segment \
  -bl \
  -i syr_print_seg03_91.mlmodel \
  -d horizontal-rl \
  ocr \
  -m RECOGNITION_MODEL.mlmodel \
  --base-dir R
```

Use the neural baseline segmenter (`-bl`). Do not substitute the legacy box
segmenter when invoking the Qoruyo segmentation model.

## Optional binarization

For noisy or uneven pages:

```bash
kraken \
  -i page.png page.txt \
  binarize \
  segment -bl -i syr_print_seg03_91.mlmodel -d horizontal-rl \
  ocr -m SyrEastSyr_01_18.mlmodel --base-dir R
```

Binarization is not automatically beneficial. Compare representative pages
with and without it before processing a corpus.

## Columns

The Zenodo record describes the segmentation model as trained for one- and
two-column pages. Four-column pages are supported with lower accuracy. Inspect
structured output and reading order carefully when pages have more than two
columns.

## Batch inputs

Kraken accepts repeated input/output pairs:

```bash
kraken \
  -i images/page_001.png output/page_001.txt \
  -i images/page_002.png output/page_002.txt \
  segment -bl -i syr_print_seg03_91.mlmodel -d horizontal-rl \
  ocr -m SyrEastSyr_01_18.mlmodel --base-dir R
```

Explicit pairs are preferable when filenames carry page numbers and output
order matters.

## Structured output

Use PageXML or ALTO when auditing segmentation and reading order:

```bash
kraken \
  --pagexml \
  -i page.png page.xml \
  segment -bl -i syr_print_seg03_91.mlmodel -d horizontal-rl \
  ocr -m SyrEastSyr_01_18.mlmodel --base-dir R
```

Global output flags must appear before the command chain.
