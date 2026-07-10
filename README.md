# Qoruyo and Sophro Mhiro: Syriac OCR and ATR Models for Kraken

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](LICENSE)
[![Models: Zenodo](https://img.shields.io/badge/models-Zenodo%20source%20of%20truth-blue)](docs/model-catalogue.md)
[![Model binaries](https://img.shields.io/badge/model%20binaries-not%20included-orange)](NOTICE.md)

An independent guide to finding and using the **Qoruyo** printed-text OCR
models and **Sophro Mhiro** manuscript ATR models with
[Kraken](https://kraken.re/).

This guide is intended for Syriac studies scholars, digital humanists,
librarians, and researchers who need reproducible OCR/ATR workflows for Syriac
printed books or manuscripts.

> [!IMPORTANT]
> This is an independent community documentation project. It is **not** an
> official Beth Mardutho repository, and its maintainer did not create or train
> the models. The original models were created by Beth Mardutho and the
> collaborators named in their Zenodo records. Zenodo is the authoritative
> source for the model files, metadata, licenses, and version history.

## Repository status

This repository documents how to use the models with Kraken. It does not host
or version the model binaries. The individual Zenodo records remain the source
of truth for model files, metadata, authorship, licensing, and version history.

## Why this repository exists

Kraken can discover and download models hosted through its Zenodo-backed model
repository. The eight Syriac models documented here are therefore already
available through persistent, citable records. What has been missing is a
single Syriac-specific entry point explaining:

- which models form the Qoruyo and Sophro Mhiro families;
- which segmentation and recognition models belong together;
- how to select printed or manuscript workflows;
- how to select Serto, Estrangela, or Eastern Syriac recognition;
- how to preserve right-to-left reading order; and
- how to run reproducible single-page and batch OCR.

This repository supplies that documentation while keeping the model files on
Zenodo.

## Quick start

Install Kraken:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip kraken
```

List models known to Kraken and inspect a record:

```bash
kraken list
kraken show 10.5281/zenodo.17406690
```

Download the printed-text segmentation model and one recognition model:

```bash
kraken get 10.5281/zenodo.17406626
kraken get 10.5281/zenodo.17406690
```

Run OCR on a printed Eastern Syriac page:

```bash
kraken \
  -i page.png page.txt \
  segment \
  -bl \
  -i syr_print_seg03_91.mlmodel \
  -d horizontal-rl \
  ocr \
  -m SyrEastSyr_01_18.mlmodel \
  --base-dir R
```

The two direction settings do different jobs:

- `segment -d horizontal-rl` controls page and line reading order.
- `ocr --base-dir R` sets the right-to-left base direction of recognized text.

See [Right-to-left behavior](docs/right-to-left.md) before processing a large
collection.

## Model families

### Qoruyo: printed texts

Qoruyo provides:

- one printed-page segmentation model; and
- separate recognition models for Serto, Estrangela, and Eastern Syriac
  (Madhnaya/Madnhaya).

Use one segmentation model plus the recognition model matching the typeface.
See [Printed-text OCR](docs/printed-text-ocr.md).

### Sophro Mhiro: manuscripts

Sophro Mhiro provides:

- separate segmentation models for one-, two-, and four-column manuscripts;
  and
- one recognition model trained across Serto, Estrangela, and Eastern Syriac.

Use the segmentation model matching the page layout plus the shared
recognition model. See [Manuscript ATR](docs/manuscript-atr.md).

## Documentation

- [Installation and model retrieval](docs/installation.md)
- [Complete model catalogue](docs/model-catalogue.md)
- [Printed-text OCR](docs/printed-text-ocr.md)
- [Manuscript ATR](docs/manuscript-atr.md)
- [Right-to-left behavior](docs/right-to-left.md)
- [Command reference](docs/command-reference.md)
- [Advanced Qoruyo/Kraken technical reference](docs/technical-reference.md)
- [Troubleshooting and validation](docs/troubleshooting.md)
- [Attribution and provenance](NOTICE.md)

Ready-to-run commands are also available in [`examples/`](examples/).

## Model downloads

To download all eight models through Kraken:

```bash
bash scripts/download-all-models.sh
```

Kraken controls where repository models are stored and prints the resulting
location. The model binaries are intentionally excluded from this GitHub
repository. This avoids duplicating Zenodo, preserves DOI-based provenance,
and reduces the risk of stale or ambiguously versioned copies.

## Licensing

Every model record documented here declares the model under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Model users must
credit the creators identified by the relevant Zenodo record, link the
license, and indicate modifications.

The original model licenses do not make this repository official or imply
endorsement by the model creators. The independently written documentation in
this repository is also released under CC BY 4.0. See [LICENSE](LICENSE) and
[NOTICE.md](NOTICE.md).

## Citation

Cite the individual Zenodo record or records for every model used. Do not cite
this repository as though it created the models. A citation file for this
documentation project is supplied in [`CITATION.cff`](CITATION.cff).

## Contributing

Corrections, tested commands, platform notes, and reproducible OCR examples are
welcome. Please keep model claims traceable to the original Zenodo records or
official Kraken documentation.
