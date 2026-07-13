# Jacob of Serugh: Qoruyo OCR Corpus

This directory contains a complete page-level Qoruyo OCR corpus for the six
Bedjan-Brock volumes of Jacob of Serugh used in this project. The current
release contains the OCR text and its ordering metadata; source scans and
prepared page images are not included at this stage.

## Contents

- `03_qoruyo_ocr/vol1/` through `vol6/`: one UTF-8 plaintext OCR file per
  processed page.
- `jacob-of-serugh-volume-1-complete-qoruyo-ocr.txt` through
  `jacob-of-serugh-volume-6-complete-qoruyo-ocr.txt`: six numerically ordered
  merged transcriptions, placed in this directory for direct access.
- `manifest.json`: page counts, relative paths, page numbers, and SHA-256
  checksums for every page-level OCR file.
- `build_merged_ocr.py`: rebuilds the merged files and manifest from the
  page-level OCR directories.
- `qoruyo_parallel_kaggle.ipynb`: reproduces the volume-aware, parallelized
  Kaggle OCR workflow used for large image collections.

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
numerically within each volume, recreates the six merged files in this
directory, and regenerates `manifest.json`.

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

## Parallel OCR in Kaggle

The included [`qoruyo_parallel_kaggle.ipynb`](qoruyo_parallel_kaggle.ipynb)
divides one Jacob volume into deterministic, non-overlapping parts that can be
processed simultaneously in separate Kaggle notebook sessions.

1. Create a Kaggle notebook and import `qoruyo_parallel_kaggle.ipynb`.
2. Use **Add Input** to attach a Kaggle dataset containing the cropped page
   images, `syr_print_seg03_91.mlmodel`, and
   `SyrEastSyr_01_18.mlmodel`. Kaggle mounts attached datasets below
   `/kaggle/input/`; this is a standard Kaggle path, not a private local path.
3. Set `VOLUME` to the volume being processed. Set `N_PARTS` to the number of
   parallel sessions and give every session a distinct `PART_INDEX` from `1`
   through `N_PARTS`. For four sessions, all four use `N_PARTS = 4`, while
   their `PART_INDEX` values are `1`, `2`, `3`, and `4`.
4. Run both notebook cells. Each session installs Kraken, discovers the
   attached models and appropriate volume images, executes Qoruyo with the
   validated right-to-left settings, and writes a ZIP archive under
   `/kaggle/working/`.
5. Download every part ZIP and combine their text files into the volume's OCR
   directory. Output filenames use deterministic volume-wide page numbers, so
   independently processed parts do not overlap.

The notebook handles Volumes 1-5 as single image collections. It also handles
the two sequential image collections used for Volume 6, assigning the second
collection an offset so that its output page numbers continue from the first.
Saved execution output and account-specific dataset paths have been removed
from the published notebook.

## Scope and reuse

The OCR is a machine-generated transcription rather than a critical edition.
It should be checked against the printed edition before scholarly citation or
text-critical use. The page images may be added later to extend the same
image-to-OCR reproducibility chain already available for the Isaac corpus.
