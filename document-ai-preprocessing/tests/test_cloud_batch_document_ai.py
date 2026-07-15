from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cloud_batch_document_ai import chunks, parse_gcs_uri, prepare_documents, submit_batch


class FakeDocumentClient:
    def processor_path(self, project, location, processor):
        return f"projects/{project}/locations/{location}/processors/{processor}"

    def processor_version_path(self, project, location, processor, version):
        return self.processor_path(project, location, processor) + f"/processorVersions/{version}"

    def batch_process_documents(self, request):
        return request


class CloudBatchTests(unittest.TestCase):
    def test_parse_gcs_uri(self):
        self.assertEqual(parse_gcs_uri("gs://bucket/a/b/"), ("bucket", "a/b"))
        with self.assertRaises(ValueError):
            parse_gcs_uri("https://example.test/file")

    def test_batch_size_limit(self):
        self.assertEqual(list(chunks([1, 2, 3], 2)), [[1, 2], [3]])
        with self.assertRaises(ValueError):
            list(chunks([1], 1001))

    def test_prepare_image_as_pdf(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            Image.new("RGB", (20, 30), "white").save(source / "page_1.png")
            documents = prepare_documents(source, "*.png", root / "job")
            self.assertEqual(len(documents), 1)
            self.assertTrue(Path(documents[0]["pdf_path"]).exists())

    def test_submit_builds_batch_request(self):
        try:
            from google.cloud import documentai
        except ModuleNotFoundError:
            self.skipTest("google-cloud-documentai is not installed")

        request = submit_batch(
            FakeDocumentClient(),
            documentai,
            [{"gcs_uri": "gs://bucket/in/page.pdf"}],
            "gs://bucket/out/",
            "project",
            "us",
            "processor",
            "",
            {"return_bounding_boxes": True},
        )
        self.assertEqual(len(request.input_documents.gcs_documents.documents), 1)
        self.assertEqual(request.document_output_config.gcs_output_config.gcs_uri, "gs://bucket/out/")
        self.assertEqual(
            list(request.document_output_config.gcs_output_config.field_mask.paths),
            ["document_layout", "chunked_document"],
        )
        self.assertTrue(request.process_options.layout_config.return_bounding_boxes)


if __name__ == "__main__":
    unittest.main()
