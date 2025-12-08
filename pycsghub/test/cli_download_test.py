import unittest
from unittest.mock import patch, MagicMock
from pycsghub.cli import download
from pycsghub.cmd.repo_types import RepoType
from pycsghub.api_client import CsghubApi
from huggingface_hub import HfApi

class TestCliDownload(unittest.TestCase):
    
    @patch('pycsghub.cli.get_csghub_api')
    @patch('pycsghub.cli.print_download_result')
    def test_download_single_file_hf(self, mock_print, mock_get_api):
        # Setup mock for HfApi
        mock_api = MagicMock(spec=HfApi)
        mock_get_api.return_value = mock_api
        
        # Call download with single file
        download(
            repo_id="test/repo",
            filenames=["config.json"],
            repo_type=RepoType.MODEL,
            revision="main",
            endpoint="https://example.com",
            token="fake_token"
        )
        
        # Verify hf_hub_download called with correct args
        mock_api.hf_hub_download.assert_called_once()
        call_kwargs = mock_api.hf_hub_download.call_args[1]
        self.assertEqual(call_kwargs['repo_id'], "test/repo")
        self.assertEqual(call_kwargs['filename'], "config.json")
        self.assertEqual(call_kwargs['repo_type'], "model")
        # Ensure extra args NOT passed to HfApi
        self.assertNotIn('quiet', call_kwargs)
        self.assertNotIn('source', call_kwargs)

    @patch('pycsghub.cli.get_csghub_api')
    @patch('pycsghub.cli.print_download_result')
    def test_download_single_file_csg(self, mock_print, mock_get_api):
        # Setup mock for CsghubApi
        mock_api = MagicMock(spec=CsghubApi)
        mock_get_api.return_value = mock_api
        
        # Call download
        download(
            repo_id="test/repo",
            filenames=["config.json"],
            source="csg",
            quiet=True
        )
        
        # Verify extra args passed to CsghubApi
        mock_api.hf_hub_download.assert_called_once()
        call_kwargs = mock_api.hf_hub_download.call_args[1]
        self.assertEqual(call_kwargs['source'], "csg")
        self.assertEqual(call_kwargs['quiet'], True)

    @patch('pycsghub.cli.get_csghub_api')
    @patch('pycsghub.cli.print_download_result')
    def test_download_snapshot_hf(self, mock_print, mock_get_api):
        mock_api = MagicMock(spec=HfApi)
        mock_get_api.return_value = mock_api
        
        download(repo_id="test/repo")
        
        mock_api.snapshot_download.assert_called_once()
        call_kwargs = mock_api.snapshot_download.call_args[1]
        self.assertNotIn('quiet', call_kwargs)

    @patch('pycsghub.cli.get_csghub_api')
    @patch('pycsghub.cli.print_download_result')
    def test_download_snapshot_csg(self, mock_print, mock_get_api):
        mock_api = MagicMock(spec=CsghubApi)
        mock_get_api.return_value = mock_api
        
        download(repo_id="test/repo", quiet=True)
        
        mock_api.snapshot_download.assert_called_once()
        call_kwargs = mock_api.snapshot_download.call_args[1]
        self.assertEqual(call_kwargs['quiet'], True)

    @patch('pycsghub.cli.get_csghub_api')
    @patch('pycsghub.cli.print_download_result')
    def test_download_multiple_files(self, mock_print, mock_get_api):
        mock_api = MagicMock(spec=HfApi)
        mock_get_api.return_value = mock_api
        
        files = ["file1.txt", "file2.txt"]
        download(repo_id="test/repo", filenames=files)
        
        # Should call snapshot_download with allow_patterns
        mock_api.snapshot_download.assert_called_once()
        call_kwargs = mock_api.snapshot_download.call_args[1]
        self.assertEqual(call_kwargs['allow_patterns'], files)

if __name__ == '__main__':
    unittest.main()
