import unittest
import requests
from unittest.mock import patch, Mock
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from _core.http_client import HttpClient, get_http_client, close_http_client, _http_client


class TestHttpClient(unittest.TestCase):
    """Test cases for the HttpClient class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Reset global client state before each test
        global _http_client
        if _http_client is not None:
            _http_client.close()
            _http_client = None

    def tearDown(self):
        """Clean up after each test method."""
        # Reset global client state after each test
        global _http_client
        if _http_client is not None:
            _http_client.close()
            _http_client = None

    @patch('_core.http_client.config')
    def test_init_creates_session_with_config(self, mock_config):
        """Test that HttpClient initializes with proper session configuration."""
        # Mock config values
        mock_config.__getitem__.side_effect = lambda key: {
            "requests": {
                "user_agent": "Test-Agent/1.0",
                "timeout": 25
            }
        }[key]
        
        client = HttpClient()
        
        # Verify session is created
        self.assertIsInstance(client.session, requests.Session)
        
        # Verify user agent is set
        self.assertEqual(
            client.session.headers["User-Agent"], 
            "Test-Agent/1.0"
        )
        
        # Verify timeout is set
        self.assertEqual(client.timeout, 25)

    @patch('_core.http_client.config')
    def test_get_request_with_default_timeout(self, mock_config):
        """Test that GET request uses configured timeout by default."""
        mock_config.__getitem__.side_effect = lambda key: {
            "requests": {
                "user_agent": "Test-Agent/1.0",
                "timeout": 30
            }
        }[key]
        
        client = HttpClient()
        
        # Mock the session.get method
        mock_response = Mock()
        client.session.get = Mock(return_value=mock_response)
        
        # Make GET request
        result = client.get("https://test.com")
        
        # Verify session.get was called with timeout
        client.session.get.assert_called_once_with(
            "https://test.com", 
            timeout=30
        )
        self.assertEqual(result, mock_response)

    @patch('_core.http_client.config')
    def test_get_request_with_custom_timeout(self, mock_config):
        """Test that GET request can override default timeout."""
        mock_config.__getitem__.side_effect = lambda key: {
            "requests": {
                "user_agent": "Test-Agent/1.0",
                "timeout": 30
            }
        }[key]
        
        client = HttpClient()
        
        # Mock the session.get method
        mock_response = Mock()
        client.session.get = Mock(return_value=mock_response)
        
        # Make GET request with custom timeout
        result = client.get("https://test.com", timeout=60)
        
        # Verify session.get was called with custom timeout
        client.session.get.assert_called_once_with(
            "https://test.com", 
            timeout=60
        )
        self.assertEqual(result, mock_response)

    @patch('_core.http_client.config')
    def test_get_request_with_additional_kwargs(self, mock_config):
        """Test that GET request passes through additional kwargs."""
        mock_config.__getitem__.side_effect = lambda key: {
            "requests": {
                "user_agent": "Test-Agent/1.0",
                "timeout": 30
            }
        }[key]
        
        client = HttpClient()
        
        # Mock the session.get method
        mock_response = Mock()
        client.session.get = Mock(return_value=mock_response)
        
        # Make GET request with additional kwargs
        result = client.get(
            "https://test.com", 
            headers={"Custom": "Header"}, 
            params={"key": "value"}
        )
        
        # Verify session.get was called with all kwargs
        client.session.get.assert_called_once_with(
            "https://test.com",
            headers={"Custom": "Header"},
            params={"key": "value"},
            timeout=30
        )
        self.assertEqual(result, mock_response)

    @patch('_core.http_client.config')
    def test_head_request_with_default_timeout(self, mock_config):
        """Test that HEAD request uses configured timeout by default."""
        mock_config.__getitem__.side_effect = lambda key: {
            "requests": {
                "user_agent": "Test-Agent/1.0",
                "timeout": 30
            }
        }[key]
        
        client = HttpClient()
        
        # Mock the session.head method
        mock_response = Mock()
        client.session.head = Mock(return_value=mock_response)
        
        # Make HEAD request
        result = client.head("https://test.com")
        
        # Verify session.head was called with timeout
        client.session.head.assert_called_once_with(
            "https://test.com", 
            timeout=30
        )
        self.assertEqual(result, mock_response)

    @patch('_core.http_client.config')
    def test_head_request_with_custom_timeout(self, mock_config):
        """Test that HEAD request can override default timeout."""
        mock_config.__getitem__.side_effect = lambda key: {
            "requests": {
                "user_agent": "Test-Agent/1.0",
                "timeout": 30
            }
        }[key]
        
        client = HttpClient()
        
        # Mock the session.head method
        mock_response = Mock()
        client.session.head = Mock(return_value=mock_response)
        
        # Make HEAD request with custom timeout
        result = client.head("https://test.com", timeout=45)
        
        # Verify session.head was called with custom timeout
        client.session.head.assert_called_once_with(
            "https://test.com", 
            timeout=45
        )
        self.assertEqual(result, mock_response)

    @patch('_core.http_client.config')
    def test_head_request_with_additional_kwargs(self, mock_config):
        """Test that HEAD request passes through additional kwargs."""
        mock_config.__getitem__.side_effect = lambda key: {
            "requests": {
                "user_agent": "Test-Agent/1.0",
                "timeout": 30
            }
        }[key]
        
        client = HttpClient()
        
        # Mock the session.head method
        mock_response = Mock()
        client.session.head = Mock(return_value=mock_response)
        
        # Make HEAD request with additional kwargs
        result = client.head(
            "https://test.com", 
            headers={"Authorization": "Bearer token"}
        )
        
        # Verify session.head was called with all kwargs
        client.session.head.assert_called_once_with(
            "https://test.com",
            headers={"Authorization": "Bearer token"},
            timeout=30
        )
        self.assertEqual(result, mock_response)

    @patch('_core.http_client.config')
    def test_close_closes_session(self, mock_config):
        """Test that close method closes the session."""
        mock_config.__getitem__.side_effect = lambda key: {
            "requests": {
                "user_agent": "Test-Agent/1.0",
                "timeout": 30
            }
        }[key]
        
        client = HttpClient()
        
        # Mock the session.close method
        client.session.close = Mock()
        
        # Call close
        client.close()
        
        # Verify session.close was called
        client.session.close.assert_called_once()


class TestGlobalHttpClient(unittest.TestCase):
    """Test cases for the global HTTP client functions."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Reset global client state before each test
        global _http_client
        if _http_client is not None:
            _http_client.close()
            _http_client = None

    def tearDown(self):
        """Clean up after each test method."""
        # Reset global client state after each test
        global _http_client
        if _http_client is not None:
            _http_client.close()
            _http_client = None

    @patch('_core.http_client.config')
    def test_get_http_client_creates_instance_first_time(self, mock_config):
        """Test that get_http_client creates instance on first call."""
        mock_config.__getitem__.side_effect = lambda key: {
            "requests": {
                "user_agent": "Test-Agent/1.0",
                "timeout": 30
            }
        }[key]
        
        # First call should create new instance
        client1 = get_http_client()
        
        # Verify instance is created
        self.assertIsInstance(client1, HttpClient)

    @patch('_core.http_client.config')
    def test_get_http_client_returns_same_instance(self, mock_config):
        """Test that get_http_client returns the same instance on subsequent calls."""
        mock_config.__getitem__.side_effect = lambda key: {
            "requests": {
                "user_agent": "Test-Agent/1.0",
                "timeout": 30
            }
        }[key]
        
        # Get client twice
        client1 = get_http_client()
        client2 = get_http_client()
        
        # Verify it's the same instance
        self.assertIs(client1, client2)

    @patch('_core.http_client.config')
    def test_close_http_client_closes_and_resets(self, mock_config):
        """Test that close_http_client closes session and resets global variable."""
        mock_config.__getitem__.side_effect = lambda key: {
            "requests": {
                "user_agent": "Test-Agent/1.0",
                "timeout": 30
            }
        }[key]
        
        # Create client instance
        client = get_http_client()
        
        # Mock the close method
        client.close = Mock()
        
        # Close the global client
        close_http_client()
        
        # Verify close was called
        client.close.assert_called_once()
        
        # Verify global variable is reset
        global _http_client
        self.assertIsNone(_http_client)

    def test_close_http_client_when_none_does_nothing(self):
        """Test that close_http_client does nothing when no client exists."""
        # Ensure no client exists
        global _http_client
        _http_client = None
        
        # This should not raise any exception
        close_http_client()
        
        # Global variable should still be None
        self.assertIsNone(_http_client)

    @patch('_core.http_client.config')
    def test_multiple_close_calls_safe(self, mock_config):
        """Test that calling close_http_client multiple times is safe."""
        mock_config.__getitem__.side_effect = lambda key: {
            "requests": {
                "user_agent": "Test-Agent/1.0",
                "timeout": 30
            }
        }[key]
        
        # Create and close client
        client = get_http_client()
        client.close = Mock()
        
        close_http_client()
        
        # Multiple closes should not raise exceptions
        close_http_client()
        close_http_client()
        
        # Verify global variable is still None
        global _http_client
        self.assertIsNone(_http_client)

    @patch('_core.http_client.config')
    def test_get_client_after_close_creates_new_instance(self, mock_config):
        """Test that get_http_client creates new instance after close."""
        mock_config.__getitem__.side_effect = lambda key: {
            "requests": {
                "user_agent": "Test-Agent/1.0",
                "timeout": 30
            }
        }[key]
        
        # Create and close client
        client1 = get_http_client()
        close_http_client()
        
        # Get client again - should create new instance
        client2 = get_http_client()
        
        # Verify it's a different instance
        self.assertIsNot(client1, client2)
        self.assertIsInstance(client2, HttpClient)


if __name__ == "__main__":
    unittest.main()
