import os
import unittest
from contextlib import redirect_stdout
from io import StringIO
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from pycsghub.cli import download


class TestSnapshotDryRun(unittest.TestCase):
    @patch("pycsghub.snapshot_download.http_get", side_effect=AssertionError("dry-run downloaded a file"))
    @patch("pycsghub.snapshot_download.utils.get_repo_info")
    def test_csg_snapshot_reports_metadata_without_downloading(self, repo_info, http_get):
        repo_info.return_value = SimpleNamespace(
            sha="abc123",
            siblings=[
                SimpleNamespace(rfilename="config.json", size=120),
                SimpleNamespace(rfilename="weights.bin", size=1000),
            ],
        )
        output = StringIO()
        with TemporaryDirectory() as root, redirect_stdout(output), patch.dict(
            os.environ, {"CSGHUB_DISABLE_XNET": "true"}
        ):
            download(
                "test/repo",
                dry_run=True,
                quiet=True,
                token="test-token",
                cache_dir=root,
                local_dir=os.path.join(root, "out"),
                allow_patterns=["*.json"],
            )

        http_get.assert_not_called()
        self.assertTrue(repo_info.call_args.kwargs["files_metadata"])
        self.assertIn("config.json", output.getvalue())
        self.assertIn("120", output.getvalue())
        self.assertNotIn("weights.bin", output.getvalue())

    @patch("huggingface_hub.snapshot_download", return_value=[])
    def test_xnet_snapshot_forwards_dry_run(self, snapshot_download):
        with patch.dict(os.environ, {"CSGHUB_DISABLE_XNET": "false"}):
            download("test/repo", dry_run=True, token="test-token")

        self.assertIs(snapshot_download.call_args.kwargs.get("dry_run"), True)
