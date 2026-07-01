# Right-to-left behavior

Syriac OCR involves two related but distinct direction problems.

## Page reading order

Set the principal text direction during segmentation:

```text
segment -d horizontal-rl
```

This controls how Kraken orders detected page regions and lines. Omitting it
can yield plausible individual lines in an incorrect page sequence.

## Text direction inside recognized lines

Set the OCR base direction explicitly:

```text
ocr --base-dir R
```

Kraken normally reorders code points into logical text order. Keep its default
reordering behavior unless diagnosing a specific bidirectional-text problem.

## Recommended combination

```bash
segment -bl -i SEGMENTATION_MODEL -d horizontal-rl \
ocr -m RECOGNITION_MODEL --base-dir R
```

## How to validate direction

Do not rely only on how text appears in a terminal, because terminal and editor
bidirectional rendering differs. Compare:

1. the source image;
2. line order in the plain-text file;
3. logical Unicode order in a bidi-aware editor; and
4. PageXML or ALTO coordinates and reading order.

Inspect at least ten pages from each distinct layout or source collection.
Check openings, page transitions, headings, columns, footnotes, and damaged
pages rather than sampling only clean body text.

## Mixed-direction content

Page numbers, Latin shelfmarks, Arabic numerals, punctuation, and embedded
foreign-language text can render differently across applications. A visually
odd line is not necessarily stored backward. Examine code-point order before
manually reversing OCR text.
