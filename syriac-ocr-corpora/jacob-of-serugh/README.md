# Jacob of Serugh: Qoruyo OCR Corpus

This directory contains a complete page-level Qoruyo OCR corpus for the six
Bedjan-Brock volumes of Jacob of Serugh used in this project. The current
release contains the OCR text and its ordering metadata; source scans and
prepared page images are not included at this stage.

## Contents

- `03_qoruyo_ocr/vol1/` through `vol6/`: one UTF-8 plaintext OCR file per
  processed page.
- `merged/`: one numerically ordered merged OCR file for each volume.
- `jacob-of-serugh-complete-qoruyo-ocr.txt`: all six volumes combined, with
  explicit volume and page markers.
- `manifest.json`: page counts, relative paths, page numbers, and SHA-256
  checksums for every page-level OCR file.
- `build_merged_ocr.py`: rebuilds the merged files and manifest from the
  page-level OCR directories.

The page-level collection contains 4,668 OCR files:

| Volume | OCR pages |
| --- | ---: |
| 1 | 720 |
| 2 | 890 |
| 3 | 912 |
| 4 | 914 |
| 5 | 899 |
| 6 | 333 |

## Rebuilding merged texts

From this directory, run:

```bash
python3 build_merged_ocr.py
```

The script discovers page files by their `_page_N.txt` suffix, orders them
numerically within each volume, recreates the six files under `merged/`,
recreates the complete corpus file, and regenerates `manifest.json`.

## OCR workflow

The page texts were generated with Kraken using the Qoruyo printed-page
segmentation model and Eastern Syriac recognition model. The validated
right-to-left settings were:

```bash
kraken -i page.jpg page.txt \
  segment -bl -i syr_print_seg03_91.mlmodel -d horizontal-rl \
  ocr -m SyrEastSyr_01_18.mlmodel --reorder --base-dir R
```

See the repository's [printed-text workflow](../../docs/printed-text-ocr.md)
and [right-to-left guidance](../../docs/right-to-left.md). Cite the relevant
Zenodo model records rather than attributing the models to this repository.

## Scope and reuse

The OCR is a machine-generated transcription rather than a critical edition.
It should be checked against the printed edition before scholarly citation or
text-critical use. The page images may be added later to extend the same
image-to-OCR reproducibility chain already available for the Isaac corpus.
