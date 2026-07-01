# Complete model catalogue

Zenodo is the authoritative source for every model below. All records were
published on 21 October 2025 and declare `CC-BY-4.0`.

## Qoruyo: printed Syriac

### Printed-page segmentation

**File:** `syr_print_seg03_91.mlmodel`

- Purpose: segmentation of printed Syriac pages.
- Layouts: trained for one and two columns; four columns are supported with
  lower reported accuracy.
- Creator listed by Zenodo: Beth Mardutho.
- DOI: <https://doi.org/10.5281/zenodo.17406626>
- Kraken retrieval: `kraken get 10.5281/zenodo.17406626`

### Serto recognition

**File:** `serto_print_best_02.mlmodel`

- Purpose: recognition of printed Syriac in Serto.
- Creator listed by Zenodo: Beth Mardutho.
- DOI: <https://doi.org/10.5281/zenodo.17406677>
- Kraken retrieval: `kraken get 10.5281/zenodo.17406677`

### Estrangela recognition

**File:** `SyrEstr_02_34.mlmodel`

- Purpose: recognition of printed Syriac in Estrangela.
- Creator listed by Zenodo: Beth Mardutho.
- DOI: <https://doi.org/10.5281/zenodo.17406703>
- Kraken retrieval: `kraken get 10.5281/zenodo.17406703`

### Eastern Syriac recognition

**File:** `SyrEastSyr_01_18.mlmodel`

- Purpose: recognition of printed Eastern Syriac (Madhnaya/Madnhaya).
- Creator listed by Zenodo: Beth Mardutho.
- DOI: <https://doi.org/10.5281/zenodo.17406690>
- Kraken retrieval: `kraken get 10.5281/zenodo.17406690`

## Sophro Mhiro: Syriac manuscripts

### One-column segmentation

**File:** `syr_1col_182pp_99_segmonto.mlmodel`

- Purpose: segmentation of single-column manuscript pages.
- Training scope: main text block; marginalia, page numbers, and other page
  features were not included.
- Training data reported by Zenodo: 458 images.
- Reported frequency-weighted mean IoU: 37.3%.
- DOI: <https://doi.org/10.5281/zenodo.17406717>
- Kraken retrieval: `kraken get 10.5281/zenodo.17406717`

### Two-column segmentation

**File:** `syr_2col_469_plusheb_georg_79_segmonto.mlmodel`

- Purpose: segmentation of double-column manuscript pages.
- Training scope: main text block; marginalia, page numbers, and other page
  features were not included.
- Training data reported by Zenodo: 483 images.
- SegmOnto subtypes distinguish right and left columns.
- Reported frequency-weighted mean IoU: 59.9%.
- DOI: <https://doi.org/10.5281/zenodo.17406754>
- Kraken retrieval: `kraken get 10.5281/zenodo.17406754`

### Four-column segmentation

**File:** `syr_4col_99_segmonto.mlmodel`

- Purpose: segmentation of quadruple-column manuscript pages.
- Training scope: main text block; marginalia, page numbers, and other page
  features were not included.
- Training data reported by Zenodo: 80 images.
- SegmOnto subtypes alternate across columns.
- Reported frequency-weighted mean IoU: 50.6%.
- DOI: <https://doi.org/10.5281/zenodo.17406766>
- Kraken retrieval: `kraken get 10.5281/zenodo.17406766`

### Multiscript manuscript recognition

**File:** `syr_41transcribathon_docs_d_3.mlmodel`

- Purpose: recognition of manuscript text in Serto, Estrangela, and Eastern
  Syriac scripts.
- Reported training material: 90,991 characters, 3,466 lines, 100 images, and
  38 manuscripts dated from the sixth through twentieth centuries.
- Character scope: principally Syriac consonants, spaces, limited
  punctuation, and very limited diacritics; no vowels.
- Reported test accuracy: 97.4%.
- DOI: <https://doi.org/10.5281/zenodo.17406773>
- Kraken retrieval: `kraken get 10.5281/zenodo.17406773`

## Sophro Mhiro creators

The four manuscript records list Beth Mardutho, George Kiraz, Christine
Roughan, and Daniel Stokl Ben Ezra as creators. Their descriptions contain
additional contributor, repository, and funding acknowledgements. Cite each
record rather than abbreviating those credits from this guide.
