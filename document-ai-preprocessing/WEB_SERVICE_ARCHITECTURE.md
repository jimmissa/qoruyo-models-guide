# Web Service Architecture

## Recommended Production Flow

```text
Browser
  -> Cloud Run API creates a job and an upload session
  -> Browser uploads the document directly to Cloud Storage
  -> API or Eventarc publishes the job to a worker queue
  -> Cloud Run worker renders PDF pages when necessary
  -> Worker submits page PDFs to Document AI batchProcess
  -> Document AI writes block JSON to Cloud Storage
  -> Worker applies adaptive block classification and image cleaning
  -> Results and decision audit files are written to Cloud Storage
  -> Browser polls job status and receives time-limited download URLs
```

## Why Cloud Storage Is The Boundary

Large documents should not pass repeatedly through the web server. A Cloud Run
API can initiate a resumable upload or issue a short-lived signed URL, allowing
the browser to upload directly to Cloud Storage. Document AI's asynchronous API
also requires Cloud Storage for input/output, so this avoids redundant transfer.

## Services

### API Service

Responsibilities:

- authenticate or rate-limit the user;
- validate filename, MIME type, size, and page limits;
- create a random job identifier;
- create the upload session;
- persist job metadata;
- return job status and result URLs.

It should not wait for OCR or classification inside the upload request.

### Worker Service

Responsibilities:

- render a multipage PDF into page images and one-page PDFs;
- call `run_cloud_batch_job(..., wait=False)`;
- persist `cloud_batch_manifest.json` in Cloud Storage or a database;
- call `refresh_cloud_batch_job(..., wait=False)` on later queue events;
- run `classify_document_pages(...)` after JSON is available;
- create cleaned full pages and body-only crops;
- package output and audit metadata.

The functions are importable; the production worker should call them directly,
not launch these Python files through a shell.

### Persistent Job State

Do not rely on a Cloud Run instance's local filesystem. Persist at least:

- job ID and state;
- source object URI;
- processor and processor-version IDs;
- classifier configuration/version;
- Document AI operation names;
- timestamps and errors;
- result object URIs;
- review-queue count.

Cloud Storage JSON is sufficient for a prototype. Firestore is preferable once
multiple users can poll and update jobs concurrently.

## Security

- Attach a least-privilege service account to Cloud Run.
- Do not ship service-account keys in the container or repository.
- Give users time-limited upload/download capability only for their job paths.
- Use random, unguessable job IDs.
- Validate uploads before submitting billable Document AI work.
- Define automatic Cloud Storage lifecycle deletion for source and intermediate files.

## Deployment Milestones

1. Validate the adaptive classifier on representative pages from several editions.
2. Run the batch module against a dedicated development bucket.
3. Add PDF page rendering and persistent cloud manifests.
4. Wrap the importable functions in a private Cloud Run API and worker.
5. Add the browser interface only after job recovery and audit outputs are stable.
