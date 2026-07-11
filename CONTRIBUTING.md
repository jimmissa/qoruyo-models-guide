# Contributing

Contributions should improve discoverability, reproducibility, or technical
accuracy without obscuring model provenance.

## Good contributions

- corrections confirmed against current Kraken behavior;
- platform-specific installation notes;
- tested commands for representative page layouts;
- validation procedures for reading order and OCR quality; and
- clarifications grounded in Zenodo metadata or official Kraken documentation.

## Requirements

- Do not commit model binaries. Corpus images and OCR may be added only when
  they have a clear provenance notice and preserve the source-to-output chain.
- Cite the relevant Zenodo DOI when describing a model.
- Distinguish tested behavior from recommendations or inference.
- Do not imply endorsement by the original creators.
- Keep example paths generic and portable.

Before submitting a change, check shell examples with:

```bash
bash -n examples/*.sh scripts/*.sh
```
