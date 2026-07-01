# Kraken command reference for these models

This is a practical subset of the Kraken command-line interface relevant to
the documented Syriac models. Confirm details against `kraken --help` and the
official documentation for the installed Kraken release.

## Processing chain

```text
kraken [GLOBAL OPTIONS] INPUTS COMMAND [OPTIONS] COMMAND [OPTIONS]
```

Typical Syriac page OCR:

```bash
kraken \
  -i INPUT_IMAGE OUTPUT_FILE \
  segment -bl -i SEGMENTATION_MODEL -d horizontal-rl \
  ocr -m RECOGNITION_MODEL --base-dir R
```

## Useful global options

- `-i`, `--input`: explicit input/output pair.
- `-I`, `--batch-input`: batch input expression.
- `-o`, `--suffix`: output suffix for batch inputs.
- `-v`, `--verbose`: increase diagnostic output.
- `--device`: inference device such as `cpu` or `cuda:0`.
- `--threads`: OpenMP/BLAS thread count.
- `--raise-on-error`: stop when processing fails.
- `--pagexml`: write PageXML.
- `--alto`: write ALTO XML.
- `--hocr`: write hOCR.
- `--native`: write Kraken's native output.

## Relevant `segment` options

- `-bl`, `--baseline`: use neural baseline segmentation.
- `-i`, `--model`: segmentation model.
- `-d`, `--text-direction`: principal page text direction. Use
  `horizontal-rl` for Syriac.
- `--maxcolseps`: maximum column separators.
- `--input-pad`: add padding around the input image.
- `--remove-hlines` or `--hlines`: control horizontal-line handling.

The Qoruyo and Sophro Mhiro segmentation models are intended for the neural
baseline workflow.

## Relevant `ocr` options

- `-m`, `--model`: recognition model.
- `--base-dir`: base bidirectional direction. Use `R` for Syriac.
- `--reorder` or `--no-reorder`: logical code-point reordering.
- `--batch-size`: lines per forward pass.
- `--num-line-workers`: line extraction worker count.
- `--no-segmentation`: treat the input as one pre-cropped line image.
- `--pad`: padding around extracted lines.

## Repository commands

```bash
kraken list
kraken show MODEL_DOI
kraken get MODEL_DOI
```

The DOI is the stable identifier. Repository display and filtering options can
change between Kraken releases.

## Single-line recognition

For an image already cropped to exactly one text line:

```bash
kraken \
  -i line.png line.txt \
  ocr \
  -m SyrEastSyr_01_18.mlmodel \
  --no-segmentation \
  --base-dir R
```

Do not use `--no-segmentation` for a normal page image.
