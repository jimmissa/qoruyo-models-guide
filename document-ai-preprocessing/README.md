# Document AI preprocessing

This directory contains independent helper software for preparing page images
for OCR with Kraken and Qoruyo. It uses Google Cloud Document AI's Layout
Parser to identify page blocks, applies an adaptive coordinate-based classifier
to derive a body-text crop, and produces an optional human review PDF.

The intended processing chain is:

```text
original page images
  -> Document AI Layout Parser
  -> adaptive block classification
  -> body-only page crops
  -> human crop review
  -> Qoruyo/Kraken OCR
```

The code is independent of any particular author, edition, or local directory
layout. It does not include credentials, source images, generated JSON, or
generated crops.

## Install

From this directory, create an isolated environment and install the required
packages:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Authenticate with Google Application Default Credentials. The account must
have permission to use the selected Document AI processor and, for batch mode,
the selected Cloud Storage bucket:

```bash
gcloud auth application-default login
```

## Configure a local run

Copy the example configuration and fill in the project, processor, and input
settings. Do not commit the local copy:

```bash
cp document_ai_config.example.json document_ai_config.local.json
```

The Layout Parser processor ID is found in the Google Cloud Document AI
console. Keep the local project and processor identifiers in the local config
or provide them through command-line arguments; neither belongs in a public
repository.

## Process page images

The synchronous runner converts each input page to a one-page PDF, sends it to
Document AI, saves the raw response, and derives the body candidate using the
adaptive classifier:

```bash
python run_document_ai_layout.py \
  --config document_ai_config.local.json \
  --source-dir /path/to/page-images \
  --output-dir /path/to/document-ai-output \
  --file-glob 'page_*.png' \
  --page-number-regex 'page_(\d+)'
```

The output directory includes raw Document AI JSON, extracted layout
elements, body-text candidates, block decisions, body crops, manifests, and a
combined body-text file. The classifier uses block coordinates and page-level
relationships; it does not rely on fixed crop coordinates for a particular
edition.

For a previously exported Document AI response, reprocess it locally without
making another API request:

```bash
python run_document_ai_layout.py \
  --config document_ai_config.local.json \
  --raw-json-file /path/to/page.document.json \
  --image-file /path/to/page.png \
  --output-dir /path/to/reprocessed-output
```

## Human crop review

The review utility creates an interleaved PDF: each page crop is followed by
its matching original page. PDF viewers that honor the embedded preference
open the document in two-page view, placing each pair side by side. The
default is 600 pixels maximum dimension with JPEG quality 75, which is intended
for visual boundary checking rather than archival reproduction.

```bash
python make_crop_review_pdf.py \
  --source-dir /path/to/original-page-images \
  --cropped-dir /path/to/document-ai-output/body_crops \
  --output /path/to/document-ai-output/crop-review.pdf \
  --source-glob 'page_*.png' \
  --cropped-glob 'page_*.body.png' \
  --page-regex 'page_(\d+)'
```

The utility refuses to run if source and crop page numbers do not match. Use
`--start-page` and `--end-page` for a partial review, or adjust
`--max-pixels` and `--jpeg-quality` when a different size/quality tradeoff is
needed.

## Cloud batch mode

For larger jobs, asynchronous Document AI batch processing uses Cloud Storage.
Copy the example configuration, fill in the bucket and processor settings, and
run:

```bash
cp cloud_batch_config.example.json cloud_batch_config.local.json

python cloud_batch_document_ai.py run \
  --config cloud_batch_config.local.json \
  --source-dir /path/to/page-images \
  --file-glob 'page_*.png' \
  --job-id my-document \
  --page-number-regex 'page_(\d+)' \
  --wait
```

The batch module is importable for a web backend. A production service should
call its functions directly, persist job state outside the local filesystem,
and use short-lived or scoped access to uploaded files and results. See
[`WEB_SERVICE_ARCHITECTURE.md`](WEB_SERVICE_ARCHITECTURE.md).

Document AI usage and Cloud Storage may incur Google Cloud charges. Check the
current Google Cloud pricing and quotas before processing a large collection.

## Testing

The classifier and cloud request helpers have unit tests:

```bash
python -m unittest discover -s tests -v
```

The tests do not submit documents to Google Cloud.

## Relationship to Qoruyo

This package prepares images; it does not contain or redistribute the Qoruyo
model files. After reviewing the body crops, run the appropriate Qoruyo Kraken
workflow documented in the parent repository. The Document AI classifier is a
heuristic preprocessing step, so the review PDF remains an important human
quality-control stage before OCR.

## Privacy and repository hygiene

Keep the following local and out of version control:

- service-account keys and ADC files;
- `document_ai_config.local.json` and `cloud_batch_config.local.json`;
- source images and generated outputs;
- raw Document AI JSON responses and job manifests containing project or
  bucket identifiers.

Only the example configurations, reusable code, tests, and documentation
belong in this public repository.
