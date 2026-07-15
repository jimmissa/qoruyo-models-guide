#!/usr/bin/env python3
"""Submit and resume Document AI Layout Parser batches through Cloud Storage.

This module is both importable by a future web backend and usable as a CLI.
It prepares image/PDF inputs, uploads them to GCS, submits asynchronous batches,
persists operation names, and downloads completed JSON responses.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    from run_document_ai_layout import build_process_options, convert_image_to_pdf
except ImportError:
    from .run_document_ai_layout import build_process_options, convert_image_to_pdf

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}
CLOUD_BATCH_VERSION = "document-ai-cloud-batch-v1"
DEFAULT_LAYOUT_FIELD_MASK = "documentLayout,chunkedDocument"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_gcs_uri(uri: str) -> tuple[str, str]:
    match = re.fullmatch(r"gs://([^/]+)(?:/(.*))?", uri.rstrip("/"))
    if not match:
        raise ValueError(f"Invalid GCS URI: {uri}")
    return match.group(1), (match.group(2) or "")


def chunks(items: list[Any], size: int) -> Iterable[list[Any]]:
    if size < 1 or size > 1000:
        raise ValueError("batch_size must be between 1 and Document AI's 1000-file limit")
    for index in range(0, len(items), size):
        yield items[index : index + size]


def prepare_documents(
    source_dir: Path,
    file_glob: str,
    local_job_dir: Path,
    page_number_regex: str | None = None,
    start_page: int | None = None,
    end_page: int | None = None,
) -> list[dict[str, Any]]:
    """Return PDFs ready for Document AI without modifying source files."""

    prepared_dir = local_job_dir / "page_pdfs"
    prepared_dir.mkdir(parents=True, exist_ok=True)
    documents: list[dict[str, Any]] = []

    for source in sorted(source_dir.glob(file_glob)):
        if not source.is_file():
            continue
        page_number = None
        if page_number_regex:
            match = re.search(page_number_regex, source.name)
            if match:
                page_number = int(match.group(1))
        if start_page is not None and (page_number is None or page_number < start_page):
            continue
        if end_page is not None and (page_number is None or page_number > end_page):
            continue
        suffix = source.suffix.lower()
        if suffix == ".pdf":
            pdf_path = source.resolve()
        elif suffix in IMAGE_SUFFIXES:
            pdf_path = prepared_dir / f"{source.stem}.pdf"
            convert_image_to_pdf(source, pdf_path)
        else:
            continue

        documents.append(
            {
                "source_path": str(source.resolve()),
                "pdf_path": str(pdf_path.resolve()),
                "stem": source.stem,
                "page_number": page_number,
            }
        )

    if not documents:
        raise RuntimeError(f"No supported files matched {file_glob!r} in {source_dir}")
    return documents


def create_clients(project_id: str, location: str):
    try:
        from google.api_core.client_options import ClientOptions
        from google.cloud import documentai, storage
    except ImportError as exc:
        raise RuntimeError(
            "Install google-cloud-documentai and google-cloud-storage from requirements_document_ai.txt"
        ) from exc

    document_client = documentai.DocumentProcessorServiceClient(
        client_options=ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
    )
    storage_client = storage.Client(project=project_id)
    return document_client, storage_client, documentai


def upload_documents(
    storage_client: Any,
    documents: list[dict[str, Any]],
    bucket_name: str,
    object_prefix: str,
) -> list[dict[str, Any]]:
    bucket = storage_client.bucket(bucket_name)
    uploaded: list[dict[str, Any]] = []

    for document in documents:
        pdf_path = Path(document["pdf_path"])
        object_name = "/".join(part for part in (object_prefix.strip("/"), pdf_path.name) if part)
        blob = bucket.blob(object_name)
        if not blob.exists(storage_client):
            blob.upload_from_filename(pdf_path, content_type="application/pdf")
        uploaded.append({**document, "gcs_uri": f"gs://{bucket_name}/{object_name}"})

    return uploaded


def _processor_name(client: Any, project_id: str, location: str, processor_id: str, version_id: str):
    if version_id:
        return client.processor_version_path(project_id, location, processor_id, version_id)
    return client.processor_path(project_id, location, processor_id)


def submit_batch(
    document_client: Any,
    documentai: Any,
    documents: list[dict[str, Any]],
    output_gcs_uri: str,
    project_id: str,
    location: str,
    processor_id: str,
    processor_version_id: str,
    request_config: dict[str, Any],
):
    gcs_documents = documentai.GcsDocuments(
        documents=[
            documentai.GcsDocument(gcs_uri=document["gcs_uri"], mime_type="application/pdf")
            for document in documents
        ]
    )
    input_config = documentai.BatchDocumentsInputConfig(gcs_documents=gcs_documents)
    field_mask = request_config.get("field_mask") or DEFAULT_LAYOUT_FIELD_MASK
    output_config = documentai.DocumentOutputConfig(
        gcs_output_config=documentai.DocumentOutputConfig.GcsOutputConfig(
            gcs_uri=output_gcs_uri if output_gcs_uri.endswith("/") else output_gcs_uri + "/",
            field_mask=field_mask,
        )
    )
    request = documentai.BatchProcessRequest(
        name=_processor_name(
            document_client,
            project_id,
            location,
            processor_id,
            processor_version_id,
        ),
        input_documents=input_config,
        document_output_config=output_config,
        process_options=build_process_options(documentai, request_config),
        skip_human_review=True,
    )
    return document_client.batch_process_documents(request=request)


def operation_snapshot(document_client: Any, documentai: Any, operation_name: str) -> dict[str, Any]:
    operation = document_client.transport.operations_client.get_operation(name=operation_name)
    snapshot: dict[str, Any] = {
        "operation_name": operation.name,
        "done": bool(operation.done),
        "checked_at_utc": utc_now(),
    }
    if operation.error and operation.error.code:
        snapshot["error"] = {
            "code": operation.error.code,
            "message": operation.error.message,
        }
    if operation.metadata and operation.metadata.value:
        metadata = documentai.BatchProcessMetadata.deserialize(operation.metadata.value)
        snapshot["state"] = str(metadata.state.name)
        snapshot["state_message"] = metadata.state_message
        snapshot["individual_process_statuses"] = [
            {
                "input_gcs_source": status.input_gcs_source,
                "output_gcs_destination": status.output_gcs_destination,
                "status_code": status.status.code,
                "status_message": status.status.message,
            }
            for status in metadata.individual_process_statuses
        ]
    return snapshot


def wait_for_operation(
    document_client: Any,
    documentai: Any,
    operation_name: str,
    poll_seconds: float = 15.0,
) -> dict[str, Any]:
    while True:
        snapshot = operation_snapshot(document_client, documentai, operation_name)
        if snapshot["done"]:
            return snapshot
        time.sleep(poll_seconds)


def download_operation_results(
    storage_client: Any,
    operation_entry: dict[str, Any],
    raw_json_dir: Path,
) -> list[str]:
    downloaded: list[str] = []
    statuses = operation_entry.get("individual_process_statuses", [])
    raw_json_dir.mkdir(parents=True, exist_ok=True)

    for status in statuses:
        if status.get("status_code") not in (None, 0):
            continue
        input_uri = status.get("input_gcs_source", "")
        output_uri = status.get("output_gcs_destination", "")
        if not input_uri or not output_uri:
            continue

        source_stem = Path(parse_gcs_uri(input_uri)[1]).stem
        bucket_name, prefix = parse_gcs_uri(output_uri)
        blobs = [
            blob
            for blob in storage_client.list_blobs(bucket_name, prefix=prefix)
            if blob.name.lower().endswith(".json")
        ]
        for shard_index, blob in enumerate(sorted(blobs, key=lambda item: item.name)):
            suffix = "" if len(blobs) == 1 else f".shard_{shard_index:04d}"
            local_path = raw_json_dir / f"{source_stem}{suffix}.document.json"
            blob.download_to_filename(local_path)
            payload = read_json(local_path)
            if not any(
                key in payload
                for key in ("document_layout", "documentLayout", "chunked_document", "chunkedDocument")
            ):
                raise RuntimeError(
                    f"Batch output {local_path.name} has no layout data. "
                    f"Top-level fields: {sorted(payload)}. Verify that the output field mask "
                    f"includes {DEFAULT_LAYOUT_FIELD_MASK}."
                )
            downloaded.append(str(local_path))

    return downloaded


def run_cloud_batch_job(
    *,
    source_dir: Path,
    file_glob: str,
    local_jobs_dir: Path,
    job_id: str,
    project_id: str,
    location: str,
    processor_id: str,
    bucket_name: str,
    input_prefix: str = "document-layout-inputs",
    output_prefix: str = "document-layout-outputs",
    processor_version_id: str = "",
    request_config: dict[str, Any] | None = None,
    batch_size: int = 50,
    page_number_regex: str | None = None,
    start_page: int | None = None,
    end_page: int | None = None,
    wait: bool = True,
    poll_seconds: float = 15.0,
) -> Path:
    """Create a resumable cloud job and return its local manifest path."""

    local_job_dir = local_jobs_dir / job_id
    manifest_path = local_job_dir / "cloud_batch_manifest.json"
    request_config = request_config or {}
    documents = prepare_documents(
        source_dir,
        file_glob,
        local_job_dir,
        page_number_regex=page_number_regex,
        start_page=start_page,
        end_page=end_page,
    )
    document_client, storage_client, documentai = create_clients(project_id, location)
    uploaded = upload_documents(
        storage_client,
        documents,
        bucket_name,
        f"{input_prefix.strip('/')}/{job_id}",
    )

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "cloud_batch_version": CLOUD_BATCH_VERSION,
        "job_id": job_id,
        "created_at_utc": utc_now(),
        "updated_at_utc": utc_now(),
        "project_id": project_id,
        "location": location,
        "processor_id": processor_id,
        "processor_version_id": processor_version_id,
        "bucket_name": bucket_name,
        "batch_size": batch_size,
        "page_number_regex": page_number_regex,
        "start_page": start_page,
        "end_page": end_page,
        "request_config": request_config,
        "documents": uploaded,
        "operations": [],
    }
    write_json(manifest_path, manifest)

    for batch_index, batch in enumerate(chunks(uploaded, batch_size), start=1):
        output_uri = (
            f"gs://{bucket_name}/{output_prefix.strip('/')}/{job_id}/batch_{batch_index:04d}/"
        )
        future = submit_batch(
            document_client,
            documentai,
            batch,
            output_uri,
            project_id,
            location,
            processor_id,
            processor_version_id,
            request_config,
        )
        entry: dict[str, Any] = {
            "batch_index": batch_index,
            "operation_name": future.operation.name,
            "submitted_at_utc": utc_now(),
            "output_gcs_uri": output_uri,
            "input_gcs_uris": [document["gcs_uri"] for document in batch],
            "done": False,
        }
        manifest["operations"].append(entry)
        manifest["updated_at_utc"] = utc_now()
        write_json(manifest_path, manifest)

        if wait:
            snapshot = wait_for_operation(
                document_client,
                documentai,
                entry["operation_name"],
                poll_seconds=poll_seconds,
            )
            entry.update(snapshot)
            entry["downloaded_json"] = download_operation_results(
                storage_client,
                entry,
                local_job_dir / "raw_json",
            )
            manifest["updated_at_utc"] = utc_now()
            write_json(manifest_path, manifest)

    return manifest_path


def refresh_cloud_batch_job(
    manifest_path: Path,
    *,
    wait: bool = False,
    poll_seconds: float = 15.0,
) -> dict[str, Any]:
    """Refresh persisted operations; optionally wait for unfinished batches."""

    manifest = read_json(manifest_path)
    document_client, storage_client, documentai = create_clients(
        manifest["project_id"], manifest["location"]
    )
    raw_json_dir = manifest_path.parent / "raw_json"

    for entry in manifest["operations"]:
        if entry.get("done") and entry.get("downloaded_json"):
            continue
        if wait:
            snapshot = wait_for_operation(
                document_client,
                documentai,
                entry["operation_name"],
                poll_seconds=poll_seconds,
            )
        else:
            snapshot = operation_snapshot(document_client, documentai, entry["operation_name"])
        entry.update(snapshot)
        if entry.get("done") and not entry.get("error"):
            entry["downloaded_json"] = download_operation_results(
                storage_client,
                entry,
                raw_json_dir,
            )
        manifest["updated_at_utc"] = utc_now()
        write_json(manifest_path, manifest)

    return manifest


def resume_cloud_batch_job(manifest_path: Path, poll_seconds: float = 15.0) -> dict[str, Any]:
    return refresh_cloud_batch_job(manifest_path, wait=True, poll_seconds=poll_seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Prepare, upload, and submit a new job.")
    run.add_argument("--config", type=Path, required=True)
    run.add_argument("--source-dir", type=Path, required=True)
    run.add_argument("--file-glob", default="*")
    run.add_argument("--job-id", required=True)
    run.add_argument("--page-number-regex")
    run.add_argument("--start-page", type=int)
    run.add_argument("--end-page", type=int)
    run.add_argument("--wait", action=argparse.BooleanOptionalAction, default=True)

    resume = subparsers.add_parser("resume", help="Resume and download an existing job.")
    resume.add_argument("--manifest", type=Path, required=True)
    resume.add_argument("--wait", action=argparse.BooleanOptionalAction, default=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "resume":
        refresh_cloud_batch_job(args.manifest, wait=args.wait)
        print(f"Refreshed: {args.manifest}")
        return 0

    config = read_json(args.config)
    cloud = config.get("cloud_batch", {})
    manifest_path = run_cloud_batch_job(
        source_dir=args.source_dir.expanduser().resolve(),
        file_glob=args.file_glob,
        local_jobs_dir=Path(cloud.get("local_jobs_dir", "cloud_jobs")).expanduser().resolve(),
        job_id=args.job_id,
        project_id=config["project_id"],
        location=config.get("location", "us"),
        processor_id=config["processor_id"],
        processor_version_id=config.get("processor_version_id", ""),
        bucket_name=cloud["bucket_name"],
        input_prefix=cloud.get("input_prefix", "document-layout-inputs"),
        output_prefix=cloud.get("output_prefix", "document-layout-outputs"),
        request_config=config.get("request", {}),
        batch_size=int(cloud.get("batch_size", 50)),
        page_number_regex=args.page_number_regex,
        start_page=args.start_page,
        end_page=args.end_page,
        wait=args.wait,
        poll_seconds=float(cloud.get("poll_seconds", 15.0)),
    )
    print(f"Cloud batch manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
