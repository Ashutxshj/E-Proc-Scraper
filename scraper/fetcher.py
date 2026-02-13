"""
HTTP fetcher with rate limiting, retries, and session management
"""
import time
import requests
from typing import Optional, Dict, Any
from config.settings import (
    BASE_URL, RATE_LIMIT, MAX_RETRIES, 
    TIMEOUT_SECONDS, USER_AGENT
)
from utils.retry import retry_with_backoff
from utils.logger import RunLogger


class Fetcher:
    """Handles HTTP requests with rate limiting and retries"""

    def __init__(self, logger: RunLogger, rate_limit: float = RATE_LIMIT):
        self.logger = logger
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create configured requests session"""
        session = requests.Session()
        session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": BASE_URL,
        })
        return session

    def _apply_rate_limit(self):
        """Apply rate limiting between requests"""
        if self.rate_limit > 0:
            elapsed = time.time() - self.last_request_time
            sleep_time = (1.0 / self.rate_limit) - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
        self.last_request_time = time.time()

    @retry_with_backoff(max_retries=MAX_RETRIES, base_delay=1.0)
    def fetch_page(self, url: str) -> str:
        """
        Fetch a page and return HTML content
        
        Args:
            url: Full URL to fetch
            
        Returns:
            HTML content as string
        """
        self._apply_rate_limit()
        self.logger.info(f"Fetching: {url}")

        response = self.session.get(url, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()

        return response.text

    @retry_with_backoff(max_retries=MAX_RETRIES, base_delay=1.0)
    def fetch_api(
        self, 
        endpoint: str, 
        method: str = "POST",
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fetch JSON data from API endpoint
        
        Args:
            endpoint: API endpoint path
            method: HTTP method (POST, GET)
            data: Request payload
            
        Returns:
            JSON response as dictionary
        """
        self._apply_rate_limit()
        url = f"{BASE_URL}{endpoint}"
        self.logger.info(f"API call: {method} {url}")

        if method == "POST":
            response = self.session.post(
                url, 
                json=data or {}, 
                timeout=TIMEOUT_SECONDS
            )
        else:
            response = self.session.get(url, params=data, timeout=TIMEOUT_SECONDS)

        response.raise_for_status()
        return response.json()

    def close(self):
        """Close the session"""
        self.session.close()
    