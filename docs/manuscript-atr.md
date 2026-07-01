# Manuscript ATR with Sophro Mhiro

## Choose by page layout

Use the segmentation model matching the manuscript page:

- one column: `syr_1col_182pp_99_segmonto.mlmodel`
- two columns: `syr_2col_469_plusheb_georg_79_segmonto.mlmodel`
- four columns: `syr_4col_99_segmonto.mlmodel`

All three layouts use the same recognition model:

```text
syr_41transcribathon_docs_d_3.mlmodel
```

The recognition model covers manuscript Serto, Estrangela, and Eastern Syriac.

## One-column example

```bash
kraken \
  -i manuscript.png manuscript.txt \
  segment \
  -bl \
  -i syr_1col_182pp_99_segmonto.mlmodel \
  -d horizontal-rl \
  ocr \
  -m syr_41transcribathon_docs_d_3.mlmodel \
  --base-dir R
```

Replace the segmentation model for two- or four-column pages.

## Training-scope limitations

The segmentation records explicitly state that training focused on the main
text block. Marginalia, page numbers, and other page features were not included
in the training data. Do not assume that these features will be detected or
excluded reliably on new pages.

The recognition record reports a restricted character inventory:

- Syriac consonants;
- spaces regularized in the transcriptions;
- limited punctuation;
- very limited diacritics; and
- no vowels.

Consequently, a successful consonantal transcription should not be mistaken
for diplomatic reproduction of vocalization or all manuscript signs.

## Validation

Evaluate representative pages from each manuscript before a full run. At a
minimum, inspect:

- column separation;
- column order;
- line order within columns;
- omitted marginalia or headers;
- script and hand variation;
- vowel and diacritic loss; and
- character error rate against a manually checked sample.

Structured PageXML or ALTO output is strongly preferable during layout
validation.
