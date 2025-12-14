import unittest
from unittest.mock import patch, MagicMock
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

if __name__ == '__main__':
    unittest.main()
