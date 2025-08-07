import requests
import atexit
from typing import Optional
from .config import config
from .logger import get_logger

logger = get_logger(__name__)


class HttpClient:
    """Shared HTTP client with configured session."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config["requests"]["user_agent"]})
        self.timeout = config["requests"]["timeout"]

    def get(self, url: str, **kwargs) -> requests.Response:
        """Make a GET request with configured timeout."""
        kwargs.setdefault("timeout", self.timeout)
        return self.session.get(url, **kwargs)

    def head(self, url: str, **kwargs) -> requests.Response:
        """Make a HEAD request with configured timeout."""
        kwargs.setdefault("timeout", self.timeout)
        return self.session.head(url, **kwargs)

    def close(self):
        """Close the session."""
        self.session.close()


# Global instance to be shared across modules
_http_client: Optional[HttpClient] = None


def get_http_client() -> HttpClient:
    """Get the global HTTP client instance."""
    global _http_client
    if _http_client is None:
        _http_client = HttpClient()
        # Ensure cleanup on exit
        atexit.register(close_http_client)
    return _http_client


def close_http_client():
    """Close the global HTTP client."""
    global _http_client
    if _http_client is not None:
        _http_client.close()
        _http_client = None
