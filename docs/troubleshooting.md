# Troubleshooting and validation

## Correct characters, wrong line order

Confirm that the segmentation step contains:

```text
-d horizontal-rl
```

This is a page-layout problem, not necessarily a recognition problem.

## Lines look reversed

Set:

```text
ocr --base-dir R
```

Keep code-point reordering enabled, then inspect the file in more than one
bidi-aware editor before reversing anything manually.

## Segmentation is implausible

- Confirm `segment -bl` is being used.
- Confirm the segmentation model, not a recognition model, follows `segment
  -i`.
- Confirm the page layout matches the chosen manuscript model.
- Try `--input-pad` if text touches the image boundary.
- Inspect PageXML or ALTO rather than only plain text.

## Marginalia or page numbers disappear

The Sophro Mhiro segmentation records state that their training data focused
on the main text block and excluded marginalia, page numbers, and other page
features. Their omission may therefore reflect model scope rather than a
software failure.

## Vowels or uncommon signs disappear

The Sophro Mhiro recognition record reports that its ground truth excluded
vowels and permitted only limited diacritics and punctuation. Use a different
or fine-tuned model when diplomatic transcription of those signs is required.

## Complex columns fail

- Select the correct one-, two-, or four-column manuscript model.
- For printed pages, remember that the Qoruyo segmentation model reports lower
  accuracy for four-column layouts.
- Inspect region coordinates and reading order in structured output.

## OCR is slow

After confirming accuracy, experiment with:

```text
ocr --batch-size 8 --num-line-workers 4
```

Memory requirements and optimal values depend on hardware and image size.

## Minimum validation protocol

Before processing a collection:

1. Select representative clean, noisy, damaged, and multi-column pages.
2. Run OCR with the intended production command.
3. Compare image order, plain-text order, and structured-output coordinates.
4. Manually transcribe a sample and estimate character and line-order errors.
5. Record Kraken version, model DOI, command, direction options, and any image
   preprocessing.
6. Preserve raw OCR separately from corrected text.

For academic reproducibility, report the exact model DOI rather than only the
model family name.
