# Prepared Page Crops

This directory contains the direct page-body crops supplied to Kraken/Qoruyo
for OCR.

The crops were produced by the Google Document AI Layout Parser workflow. The
workflow uses Document AI layout coordinates and page-level visual boundaries
to retain the main Syriac text region while excluding running headers,
page-number regions, and critical apparatus where those can be identified.

The images are direct crops of the original page images. No white masking or
painting over rejected layout blocks is applied.

Filenames preserve the source page number, for example:

```text
Bedjan_page_49.png
```

The corresponding OCR files will later be placed in:

```text
../03_qoruyo_ocr/
```
