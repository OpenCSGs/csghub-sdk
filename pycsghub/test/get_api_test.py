import unittest
from unittest.mock import patch, MagicMock, call
from pycsghub.api_client import get_csghub_api, CsghubApi, CsgXnetApi


class TestGetCsghubApi(unittest.TestCase):

    @patch('pycsghub.api_client.disable_xnet')
    @patch('pycsghub.api_client.get_token_to_send')
    @patch('pycsghub.api_client.get_endpoint')
    def test_get_csghub_api_xnet_enabled(self, mock_endpoint, mock_token, mock_disable_xnet):
        # Setup
        mock_disable_xnet.return_value = False
        mock_token.return_value = "fake_token"
        mock_endpoint.return_value = "https://example.com"

        # Call
        api = get_csghub_api(token="fake_token", endpoint="https://example.com")

        # Assert
        self.assertIsInstance(api, CsgXnetApi)
        self.assertEqual(api._token, "fake_token")
        # In CsgXnetApi, endpoint is modified via get_xnet_endpoint which appends '/hf' (assuming XNET_API_PATH is 'hf')
        # However, we are mocking get_endpoint, but CsgXnetApi calls get_xnet_endpoint internally.
        # Since we didn't mock get_xnet_endpoint, it will use the real one which appends 'hf'
        # So we expect "https://example.com/hf"
        self.assertEqual(api._endpoint, "https://example.com/hf")

    @patch('pycsghub.api_client.disable_xnet')
    @patch('pycsghub.api_client.get_token_to_send')
    @patch('pycsghub.api_client.get_endpoint')
    def test_get_csghub_api_xnet_disabled(self, mock_endpoint, mock_token, mock_disable_xnet):
        # Setup
        mock_disable_xnet.return_value = True
        mock_token.return_value = "fake_token"
        mock_endpoint.return_value = "https://example.com"

        # Call
        api = get_csghub_api(token="fake_token", endpoint="https://example.com")

        # Assert
        self.assertIsInstance(api, CsghubApi)
        self.assertEqual(api._token, "fake_token")
        self.assertEqual(api._endpoint, "https://example.com")

    @patch('pycsghub.api_client.disable_xnet')
    @patch('pycsghub.api_client.get_token_to_send')
    @patch('pycsghub.api_client.get_endpoint')
    def test_csgxnetapi_no_token_returns_false(self, mock_endpoint, mock_token, mock_disable_xnet):
        """When get_token_to_send returns None (no CSGHub token available),
        CsgXnetApi should store False instead of None to prevent HuggingFace's
        implicit token fallback (Issue #129)."""
        # Setup
        mock_disable_xnet.return_value = False
        mock_token.return_value = None  # No CSGHub token found
        mock_endpoint.return_value = "https://example.com"

        # Call
        api = get_csghub_api(endpoint="https://example.com")

        # Assert
        self.assertIsInstance(api, CsgXnetApi)
        self.assertEqual(api._token, False)  # None → False to prevent HF fallback

    @patch('pycsghub.api_client.disable_xnet')
    @patch('pycsghub.api_client.get_token_to_send')
    @patch('pycsghub.api_client.get_endpoint')
    def test_csgxnetapi_with_token_stores_string(self, mock_endpoint, mock_token, mock_disable_xnet):
        """When a valid CSGHub token is provided, CsgXnetApi should store it as-is."""
        # Setup
        mock_disable_xnet.return_value = False
        mock_token.return_value = "my_csg_token"
        mock_endpoint.return_value = "https://example.com"

        # Call
        api = get_csghub_api(token="my_csg_token", endpoint="https://example.com")

        # Assert
        self.assertIsInstance(api, CsgXnetApi)
        self.assertEqual(api._token, "my_csg_token")

    @patch('pycsghub.api_client.disable_xnet')
    @patch('pycsghub.api_client.get_token_to_send')
    @patch('pycsghub.api_client.get_endpoint')
    def test_csgxnetapi_snapshot_download_no_token_passes_false(self, mock_endpoint, mock_token, mock_disable_xnet):
        """When CsgXnetApi has no token (self._token=False), snapshot_download
        should pass token=False to HuggingFace's snapshot_download, NOT token=None,
        to prevent implicit HF token fallback (Issue #129)."""
        # Setup
        mock_disable_xnet.return_value = False
        mock_token.return_value = None  # No CSGHub token
        mock_endpoint.return_value = "https://example.com"

        api = get_csghub_api(endpoint="https://example.com")

        # Mock the origin_snapshot_download to capture kwargs
        with patch('huggingface_hub.snapshot_download') as mock_snapshot:
            mock_snapshot.return_value = "/fake/path"
            api.snapshot_download(repo_id="test/repo")

            # Verify that token=False was passed (not None)
            call_kwargs = mock_snapshot.call_args[1]
            self.assertEqual(call_kwargs['token'], False)

    @patch('pycsghub.api_client.disable_xnet')
    @patch('pycsghub.api_client.get_token_to_send')
    @patch('pycsghub.api_client.get_endpoint')
    def test_csgxnetapi_snapshot_download_with_token_passes_string(self, mock_endpoint, mock_token, mock_disable_xnet):
        """When CsgXnetApi has a token, snapshot_download should pass it correctly."""
        # Setup
        mock_disable_xnet.return_value = False
        mock_token.return_value = "my_csg_token"
        mock_endpoint.return_value = "https://example.com"

        api = get_csghub_api(token="my_csg_token", endpoint="https://example.com")

        # Mock the origin_snapshot_download to capture kwargs
        with patch('huggingface_hub.snapshot_download') as mock_snapshot:
            mock_snapshot.return_value = "/fake/path"
            api.snapshot_download(repo_id="test/repo")

            # Verify that the CSGHub token was passed
            call_kwargs = mock_snapshot.call_args[1]
            self.assertEqual(call_kwargs['token'], "my_csg_token")

    @patch('pycsghub.api_client.disable_xnet')
    @patch('pycsghub.api_client.get_token_to_send')
    @patch('pycsghub.api_client.get_endpoint')
    def test_csgxnetapi_hf_hub_download_no_token_passes_false(self, mock_endpoint, mock_token, mock_disable_xnet):
        """When CsgXnetApi has no token (self._token=False), hf_hub_download
        should pass token=False to HuggingFace's hf_hub_download (Issue #129)."""
        # Setup
        mock_disable_xnet.return_value = False
        mock_token.return_value = None  # No CSGHub token
        mock_endpoint.return_value = "https://example.com"

        api = get_csghub_api(endpoint="https://example.com")

        # Mock the origin_hf_hub_download (functional fallback path)
        with patch('huggingface_hub.hf_hub_download') as mock_download:
            mock_download.return_value = "/fake/file"
            # The method first tries super().hf_hub_download which will also
            # hit the mock since we're patching at the module level.
            # We need to also mock the super call so it fails and falls through
            # to the functional call.
            with patch.object(type(api).__bases__[0], 'hf_hub_download', side_effect=TypeError("mocked")):
                api.hf_hub_download(repo_id="test/repo", filename="config.json")

                # Verify that token=False was passed in the fallback path
                call_kwargs = mock_download.call_args[1]
                self.assertEqual(call_kwargs['token'], False)

    @patch('pycsghub.api_client.disable_xnet')
    @patch('pycsghub.api_client.get_token_to_send')
    @patch('pycsghub.api_client.get_endpoint')
    def test_csgxnetapi_hf_hub_download_token_none_in_kwargs_overridden(self, mock_endpoint, mock_token, mock_disable_xnet):
        """When kwargs contains token=None (e.g., from CLI passing -k without value),
        CsgXnetApi should override it with self._token (False) to prevent HF fallback."""
        # Setup
        mock_disable_xnet.return_value = False
        mock_token.return_value = None  # No CSGHub token
        mock_endpoint.return_value = "https://example.com"

        api = get_csghub_api(endpoint="https://example.com")

        # Mock the super call to capture kwargs
        with patch.object(type(api).__bases__[0], 'hf_hub_download', return_value="/fake/file") as mock_super:
            api.hf_hub_download(repo_id="test/repo", filename="config.json", token=None)

            # Verify that token was overridden from None to False
            call_kwargs = mock_super.call_args[1]
            self.assertEqual(call_kwargs['token'], False)

    @patch('pycsghub.api_client.disable_xnet')
    @patch('pycsghub.api_client.get_token_to_send')
    @patch('pycsghub.api_client.get_endpoint')
    def test_csgxnetapi_explicit_token_not_overridden(self, mock_endpoint, mock_token, mock_disable_xnet):
        """When kwargs contains an explicit token string, CsgXnetApi should NOT override it."""
        # Setup
        mock_disable_xnet.return_value = False
        mock_token.return_value = "default_csg_token"
        mock_endpoint.return_value = "https://example.com"

        api = get_csghub_api(token="default_csg_token", endpoint="https://example.com")

        # Mock the super call to capture kwargs
        with patch.object(type(api).__bases__[0], 'hf_hub_download', return_value="/fake/file") as mock_super:
            api.hf_hub_download(repo_id="test/repo", filename="config.json", token="explicit_override_token")

            # Verify that the explicit token was preserved
            call_kwargs = mock_super.call_args[1]
            self.assertEqual(call_kwargs['token'], "explicit_override_token")


if __name__ == '__main__':
    unittest.main()
