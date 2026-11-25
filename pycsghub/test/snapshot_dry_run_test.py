import os
import unittest
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from huggingface_hub.file_download import DryRunFileInfo
from typer.testing import CliRunner

from pycsghub.cli import app


class TestDownloadDryRun(unittest.TestCase):
    def run_dry_run(self, disable_xnet, filenames):
        with TemporaryDirectory() as root, patch.dict(
            os.environ, {"CSGHUB_DISABLE_XNET": str(disable_xnet).lower()}
        ):
            result = CliRunner().invoke(
                app,
                ["download", "test/repo", *filenames, "--dry-run", "--token", "test-token",
                 "--cache-dir", root, "--local-dir", os.path.join(root, "out")],
            )
            self.assertFalse(os.path.exists(os.path.join(root, "out")))
        return result

    @patch("pycsghub.snapshot_download.http_get", side_effect=AssertionError("unexpected transfer"))
    @patch("pycsghub.file_download.http_get", side_effect=AssertionError("unexpected transfer"))
    @patch("pycsghub.utils.get_repo_info")
    def test_csg_routes_report_metadata_without_transferring(self, repo_info, file_get, snapshot_get):
        repo_info.return_value = SimpleNamespace(
            sha="abc123",
            siblings=[SimpleNamespace(rfilename="config.json", size=120)],
        )
        for filenames in ([], ["config.json"]):
            with self.subTest(filenames=filenames):
                result = self.run_dry_run(True, filenames)
                self.assertEqual(result.exit_code, 0, result.output)
                self.assertIn("config.json", result.output)
                self.assertIn("120", result.output)
                self.assertTrue(repo_info.call_args.kwargs["files_metadata"])
        file_get.assert_not_called()
        snapshot_get.assert_not_called()

    @patch("huggingface_hub.snapshot_download")
    @patch("huggingface_hub.hf_hub_download")
    @patch("huggingface_hub.HfApi.hf_hub_download")
    def test_xnet_routes_report_metadata_without_transferring(self, hf_api_download, hf_download, snapshot_download):
        def dry_run_result(**kwargs):
            self.assertIs(kwargs.get("dry_run"), True)
            return DryRunFileInfo("abc123", 120, "config.json", "", False, True)

        hf_api_download.side_effect = dry_run_result
        hf_download.side_effect = dry_run_result
        snapshot_download.side_effect = lambda **kwargs: [dry_run_result(**kwargs)]
        for filenames in ([], ["config.json"]):
            with self.subTest(filenames=filenames):
                result = self.run_dry_run(False, filenames)
                self.assertEqual(result.exit_code, 0, result.output)
                self.assertIn("config.json", result.output)
                self.assertIn("120", result.output)
