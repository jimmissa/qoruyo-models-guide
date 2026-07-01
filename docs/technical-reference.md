# Advanced Qoruyo Syriac OCR Models: Kraken Usage Reference

> This is an independent technical appendix. Its author did not create or
> train the Qoruyo models. Beth Mardutho is the creator listed by the original
> Zenodo records, which remain authoritative.

This document records the practical command-line interface for running the
downloaded Qoruyo Syriac `.mlmodel` files with Kraken. It was assembled from:

- the Kraken command-line interface
- embedded metadata inside the downloaded `.mlmodel` files
- the public Zenodo records for the four Qoruyo models

Kraken version inspected: `kraken 7.0.2`.

## Model Inventory

### `syr_print_seg03_91.mlmodel`

- Task: segmentation.
- Intended use: printed Syriac page segmentation. Trained for one- and
  two-column printed Syriac; four-column layouts are supported with lower
  accuracy.
- Zenodo record: <https://zenodo.org/records/17406626>
- DOI: `10.5281/zenodo.17406626`

### `serto_print_best_02.mlmodel`

- Task: OCR recognition.
- Intended use: printed Syriac in Serto script.
- Zenodo record: <https://zenodo.org/records/17406677>
- DOI: `10.5281/zenodo.17406677`

### `SyrEstr_02_34.mlmodel`

- Task: OCR recognition.
- Intended use: printed Syriac in Estrangela script.
- Zenodo record: <https://zenodo.org/records/17406703>
- DOI: `10.5281/zenodo.17406703`

### `SyrEastSyr_01_18.mlmodel`

- Task: OCR recognition.
- Intended use: printed Syriac in Eastern Syriac script, i.e.
  Madhnaya/Madnhaya.
- Zenodo record: <https://zenodo.org/records/17406690>
- DOI: `10.5281/zenodo.17406690`

All four Zenodo records list Beth Mardutho as creator, resource type `Model`,
open access, and license `CC-BY-4.0`.

## Embedded Model Metadata

The following metadata was read from downloaded model files using Kraken/CoreML
metadata loaders.

### `syr_print_seg03_91.mlmodel`

- Kraken model type: `segmentation`.
- Segmentation type: none.
- Channel mode: `1`.
- Completed epochs: 91.
- Codec/classes: region/baseline classes.
- Last embedded accuracy entry: `[16289, 0.7363362046962798]`.

### `serto_print_best_02.mlmodel`

- Kraken model type: `recognition`.
- Segmentation type: `baselines`.
- Channel mode: `None`.
- Completed epochs: 124.
- Codec/classes: 123 codec entries.
- Last embedded accuracy entry: `[135408, 0.9848312867609121]`.

### `SyrEstr_02_34.mlmodel`

- Kraken model type: `recognition`.
- Segmentation type: `baselines`.
- Channel mode: `L`.
- Completed epochs: 34.
- Codec/classes: 170 codec entries.
- Last embedded accuracy entry: `[9316, 0.9898156503803016]`.

### `SyrEastSyr_01_18.mlmodel`

- Kraken model type: `recognition`.
- Segmentation type: `baselines`.
- Channel mode: `1`.
- Completed epochs: 18.
- Codec/classes: 170 codec entries.
- Last embedded accuracy entry: `[15876, 0.9901288503013881]`.

The segmentation model contains these embedded classes:

```text
aux:
  _start_separator: 0
  _end_separator: 1
baselines:
  default: 2
regions:
  Foreign: 3
  Running Header: 4
  Main: 5
  Footnotes: 6
```

Important consequence: the OCR recognition models are baseline-recognition
models, so the normal page workflow should use Kraken's neural baseline
segmenter:

```text
segment -bl -i syr_print_seg03_91.mlmodel
```

not the legacy box segmenter.

## Direction Handling

For Syriac printed pages, use:

```text
segment -d horizontal-rl
```

or equivalently:

```text
segment --text-direction horizontal-rl
```

This was the critical option for correcting Qoruyo/Kraken output order on
right-to-left Syriac page images. The option belongs to `segment`, not `ocr`.

There is a second, separate OCR option:

```text
ocr --base-dir R
```

This sets the base bidirectional text direction for recognition output. For
Syriac OCR it is safest to set this explicitly to `R`, especially in plain text
workflows. Kraken's `ocr --reorder` option is enabled by default, meaning code
points are reordered into logical output order. Keep the default unless you are
debugging text-direction behavior.

Recommended direction setup for Syriac page OCR:

```text
segment -bl -i syr_print_seg03_91.mlmodel -d horizontal-rl
ocr -m <RECOGNITION_MODEL> --base-dir R
```

## Recommended Commands

The examples below assume this generic project layout:

```text
project/
  models/
    syr_print_seg03_91.mlmodel
    serto_print_best_02.mlmodel
    SyrEstr_02_34.mlmodel
    SyrEastSyr_01_18.mlmodel
  images/
    page_001.jpg
    page_002.jpg
  output/
```

They also assume that `kraken` is on your shell `PATH`. If not, replace
`kraken` with the path to your virtual environment's Kraken executable, for
example `./.venv/bin/kraken`.

### Eastern Syriac / Madhnaya/Madnhaya Page OCR

Use this for printed Eastern Syriac/Madhnaya pages:

```bash
kraken \
  -i images/page_002.jpg output/page_002.txt \
  segment \
  -bl \
  -i models/syr_print_seg03_91.mlmodel \
  -d horizontal-rl \
  ocr \
  -m models/SyrEastSyr_01_18.mlmodel \
  --base-dir R
```

### Serto Page OCR

```bash
kraken \
  -i images/page_001.png output/page_001.txt \
  segment \
  -bl \
  -i models/syr_print_seg03_91.mlmodel \
  -d horizontal-rl \
  ocr \
  -m models/serto_print_best_02.mlmodel \
  --base-dir R
```

### Estrangela Page OCR

```bash
kraken \
  -i images/page_001.png output/page_001.txt \
  segment \
  -bl \
  -i models/syr_print_seg03_91.mlmodel \
  -d horizontal-rl \
  ocr \
  -m models/SyrEstr_02_34.mlmodel \
  --base-dir R
```

### Segmentation Only

To inspect segmentation output without recognizing text:

```bash
kraken \
  -i images/page_001.png output/page_001_segmentation.json \
  segment \
  -bl \
  -i models/syr_print_seg03_91.mlmodel \
  -d horizontal-rl
```

The native segmentation output is JSON.

### OCR Only on a Single Line Image

If the input image is already a single text line rather than a full page:

```bash
kraken \
  -i images/line_001.png output/line_001.txt \
  ocr \
  -m models/SyrEastSyr_01_18.mlmodel \
  --no-segmentation \
  --base-dir R
```

Swap in the Serto or Estrangela recognition model as needed.

### Binarize Before Segmentation/OCR

Kraken can chain preprocessing before segmentation:

```bash
kraken \
  -i images/page_001.png output/page_001.txt \
  binarize \
  segment \
  -bl \
  -i models/syr_print_seg03_91.mlmodel \
  -d horizontal-rl \
  ocr \
  -m models/SyrEastSyr_01_18.mlmodel \
  --base-dir R
```

Binarization is optional. Use it when pages are noisy, uneven, or low contrast.
For already clean/cropped images it may not help.

### Batch OCR with Many Explicit Input/Output Pairs

Kraken accepts repeated `-i input output` pairs before the processing chain:

```bash
kraken \
  -i images/page_001.jpg output/page_001.txt \
  -i images/page_002.jpg output/page_002.txt \
  -i images/page_003.jpg output/page_003.txt \
  segment \
  -bl \
  -i models/syr_print_seg03_91.mlmodel \
  -d horizontal-rl \
  ocr \
  -m models/SyrEastSyr_01_18.mlmodel \
  --base-dir R
```

This is the most controllable style for batch/background processing because
each output path is explicit.

### Batch OCR with a Glob

Kraken also supports batch input globs:

```bash
kraken \
  -I "images/*.jpg" \
  -o ".txt" \
  segment \
  -bl \
  -i models/syr_print_seg03_91.mlmodel \
  -d horizontal-rl \
  ocr \
  -m models/SyrEastSyr_01_18.mlmodel \
  --base-dir R
```

Use explicit `-i input output` pairs when you need exact page-numbered filenames.

## Output Formats

The default/native OCR output is plain text. Kraken can also write structured
outputs by using global flags before the chain:

- `-n`, `--native`: native output. This means plain text for OCR and JSON for
  segmentation.
- `-h`, `--hocr`: hOCR.
- `-a`, `--alto`: ALTO XML.
- `-x`, `--pagexml`: PageXML.
- `-y`, `--abbyy`: ABBYY XML.

Example PageXML OCR:

```bash
kraken \
  --pagexml \
  -i images/page_001.png output/page_001.xml \
  segment \
  -bl \
  -i models/syr_print_seg03_91.mlmodel \
  -d horizontal-rl \
  ocr \
  -m models/SyrEastSyr_01_18.mlmodel \
  --base-dir R
```

Note that `-x` has two meanings depending on position:

- before the processing command chain, global `-x` means PageXML output
- after `segment`, `-x` means the legacy box segmenter

To avoid ambiguity, prefer spelling out `--pagexml`.

## Kraken Global Options

Global options appear before the processing command chain.

```text
kraken [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...
```

- `--version`: print Kraken version.
- `-i`, `--input <FILE FILE>...`: one or more input-output file pairs.
- `-I`, `--batch-input TEXT`: glob expression for many input files.
- `-o`, `--suffix TEXT`: suffix for outputs from batch/PDF inputs.
- `-v`, `--verbose`: increase verbosity.
- `-f`, `--format-type [image|alto|page|pdf|xml]`: input type. Default:
  `image`.
- `-p`, `--pdf-format TEXT`: format string for PDF page output names.
- `-h`, `--hocr`: hOCR output.
- `-a`, `--alto`: ALTO output.
- `-y`, `--abbyy`: ABBYY XML output.
- `-x`, `--pagexml`: PageXML output.
- `-n`, `--native`: native output.
- `-t`, `--template FILE`: output template.
- `-d`, `--device TEXT`: inference device, e.g. `cpu`, `cuda:0`. Default:
  `auto`.
- `--precision ...`: inference precision. Default: `32-true`.
- `-r`, `--raise-on-error` / `--no-raise-on-error`: raise exception on
  processing error.
- `--threads INTEGER`: OpenMP/BLAS thread pool size. Default: `1`.
- `--subline-segmentation` / `--no-subline-segmentation`: enable/disable
  subline segmentation in serialization output.

Useful batch/debug defaults:

```bash
--raise-on-error --threads 1 --device auto
```

## `segment` Options

```text
kraken segment [OPTIONS]
```

- `-i`, `--model TEXT`: baseline/region detection model(s). For Qoruyo, use
  `models/syr_print_seg03_91.mlmodel`.
- `-x`, `--boxes`: legacy box segmenter. Do not use this for the Qoruyo neural
  baseline workflow.
- `-bl`, `--baseline`: neural baseline segmenter. Use this for Qoruyo.
- `-d`, `--text-direction [horizontal-lr|horizontal-rl|vertical-lr|vertical-rl]`:
  principal text direction. Use `horizontal-rl` for Syriac.
- `--scale FLOAT`: scaling parameter. Usually leave default.
- `-m`, `--maxcolseps INTEGER`: maximum column separators. Default: `2`.
  Increase only for complex multi-column pages.
- `-b`, `--black-colseps` / `-w`, `--white_colseps`: column separator color
  assumption. Default: white. Usually leave default.
- `-r`, `--remove-hlines` / `-l`, `--hlines`: remove or retain horizontal
  lines. Default: remove. Usually leave default.
- `-p`, `--pad INTEGER`: left/right padding around lines. Only for the BBox
  segmenter, so it is not relevant when using `-bl`.
- `--input-pad INTEGER`: padding around input image. Default: `0`. Useful if
  text touches the crop boundary.

## `ocr` Options

```text
kraken ocr [OPTIONS]
```

- `-m`, `--model TEXT`: recognition model weights. Use one of the three
  script-specific OCR models.
- `-B`, `--batch-size INTEGER`: lines per forward pass. Default: `1`. Increase
  for speed if memory allows.
- `-p`, `--pad INTEGER`: left/right padding around extracted lines. Default:
  `16`. Usually leave default.
- `-t`, `--temperature FLOAT`: softmax temperature. Default: `1.0`. Usually
  leave default.
- `--num-line-workers INTEGER`: line extraction worker processes. Default: `2`.
  Increase cautiously for batch speed.
- `-n`, `--reorder` / `--no-reorder`: reorder code points to logical order.
  Default: reorder. Keep default `--reorder`.
- `--base-dir [L|R|auto]`: base text direction. Use `R` for Syriac.
- `-s`, `--no-segmentation`: treat input as one whole line. Use only for
  pre-cropped line images.
- `-d`, `--text-direction [horizontal-tb|vertical-lr|vertical-rl]`:
  serialization output direction. Usually leave default for plain text.
- `--no-legacy-polygons`: disable legacy polygon extractor. Usually leave
  default.

## `binarize` Options

```text
kraken binarize [OPTIONS]
```

- `--threshold FLOAT`: default `0.5`.
- `--zoom FLOAT`: default `0.5`.
- `--escale FLOAT`: default `1.0`.
- `--border FLOAT`: default `0.1`.
- `--perc INTEGER`: default `80`.
- `--range INTEGER`: default `20`.
- `--low INTEGER`: default `5`.
- `--high INTEGER`: default `90`.

## Repository Commands

These are Kraken model-repository commands. They are not needed when the models
are already downloaded, but they are useful for discovery.

```bash
kraken list --all
kraken list --recognition --script Syrc
kraken list --segmentation --script Syrc
kraken get <MODEL_ID_OR_DOI>
kraken show <MODEL_ID_OR_DOI>
```

In this Kraken version, `kraken show` expects a repository ID/DOI. It does not
show metadata for a downloaded `.mlmodel` path.

## Inspecting Model Metadata

Use this script to print compact metadata for every downloaded model:

```bash
python - <<'PY'
from pathlib import Path
from coremltools.models import MLModel
import json

for p in sorted(Path("models").glob("*.mlmodel")):
    m = MLModel(str(p))
    md = dict(m.user_defined_metadata)
    meta = json.loads(md.get("kraken_meta", "{}"))
    codec = json.loads(md.get("codec", "{}")) if "codec" in md else None
    print(p.name)
    print("  type:", meta.get("model_type"))
    print("  seg_type:", meta.get("seg_type"))
    print("  one_channel_mode:", meta.get("one_channel_mode"))
    print("  completed_epochs:", meta.get("hyper_params", {}).get("completed_epochs"))
    print("  codec_size:", len(codec) if codec else None)
    print("  class_mapping:", meta.get("class_mapping"))
    acc = meta.get("accuracy") or []
    print("  last_accuracy:", acc[-1] if acc else None)
    print("  vgsl:", md.get("vgsl", "")[:300])
PY
```

To print the full OCR codec for a recognition model:

```bash
python - <<'PY'
from coremltools.models import MLModel
import json

model_path = "models/SyrEastSyr_01_18.mlmodel"
m = MLModel(model_path)
codec = json.loads(m.user_defined_metadata["codec"])
for char, ids in codec.items():
    print(repr(char), ids)
PY
```

## Corrected Batch Processing Pattern

For scripted or background processing, the essential correction is that the
batch command must include `-d horizontal-rl` in the `segment` step and should
set `--base-dir R` in the `ocr` step.

```python
cmd.extend([
    "segment",
    "-bl",
    "-i", str(seg_model),
    "-d", "horizontal-rl",
    "ocr",
    "-m", str(ocr_model),
    "--base-dir", "R",
])
```

This is the corrected equivalent of the earlier minimal command:

```bash
kraken -i page1.png syriac1.txt \
  segment -bl -i syr_print_seg03_91.mlmodel \
  ocr -m serto_print_best_02.mlmodel
```

The old command can run, but it leaves Kraken at its default segmentation text
direction (`horizontal-lr`), which is wrong for Syriac page reading order.

## Troubleshooting

### Output text looks reversed or line/page order is wrong

Use both:

```text
segment -d horizontal-rl
ocr --base-dir R
```

Keep OCR codepoint reordering enabled, which is Kraken's default:

```text
ocr --reorder
```

### Recognition model works but segmentation is strange

Confirm that `segment` is using:

```text
-bl -i models/syr_print_seg03_91.mlmodel
```

Do not use the default legacy box segmenter (`segment -x`) for the Qoruyo neural
segmentation model.

### Page has text near the crop edge

Try:

```text
segment --input-pad 20 ...
```

or crop with a slightly larger margin before OCR.

### Page has multiple columns

The segmentation Zenodo record says one- and two-column Syriac printed texts are
the main training target. Four-column layout is supported but less accurate.
The `segment --maxcolseps` option defaults to `2`; experimenting with a higher
value may help complex multi-column pages.

### Need faster OCR

Try increasing:

```text
ocr --batch-size 8 --num-line-workers 4
```

Adjust downward if memory use or instability increases.

### Need structured outputs for proofreading

Use `--pagexml` or `--alto` globally. Structured output makes it easier to
inspect coordinates, regions, and line order than plain text.
