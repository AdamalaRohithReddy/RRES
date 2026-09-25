"""Hardened, secure HTTP client for Government APIs using httpx with strict security boundaries."""

from __future__ import annotations

import ipaddress
import logging
import random
import time
from typing import Any, Dict, Optional, Set
from urllib.parse import urlparse

import httpx

from src.config.settings import get_settings
from src.government_api.exceptions import (
    AuthenticationError,
    AuthorizationError,
    GovernmentAPIError,
    NetworkError,
    RateLimitError,
    ResponseTooLargeError,
    SecurityViolationError,
    ServerError,
    TimeoutError,
)

logger = logging.getLogger(__name__)

# Strict domain whitelist for official government APIs
ALLOWED_DOMAINS: Set[str] = {
    "apisetu.gov.in",
    "partners.apisetu.gov.in",
    "directory.apisetu.gov.in",
    "data.gov.in",
    "api.data.gov.in",
}

# Maximum permissible response payload size: 2 MB
MAX_RESPONSE_BYTES: int = 2 * 1024 * 1024


class TokenBucketRateLimiter:
    """Thread-safe token bucket rate limiter for external requests."""

    def __init__(self, rate_per_second: float = 5.0, burst_capacity: int = 10):
        self._rate = rate_per_second
        self._capacity = burst_capacity
        self._tokens = float(burst_capacity)
        self._last_update = time.time()

    def acquire(self) -> None:
        """Acquire 1 token, sleeping briefly if rate is exceeded."""
        now = time.time()
        elapsed = now - self._last_update
        self._last_update = now

        # Replenish tokens
        self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
        if self._tokens < 1.0:
            sleep_needed = (1.0 - self._tokens) / self._rate
            time.sleep(sleep_needed)
            self._tokens = 0.0
        else:
            self._tokens -= 1.0


class GovernmentAPIClient:
    """Secure client for communicating with official government endpoints."""

    def __init__(
        self,
        connect_timeout: float = 3.0,
        read_timeout: float = 7.0,
        max_retries: int = 2,
        rate_limit_per_sec: float = 5.0,
    ):
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.max_retries = max_retries
        self._rate_limiter = TokenBucketRateLimiter(rate_per_second=rate_limit_per_sec)

        # Configure httpx client
        timeout = httpx.Timeout(
            timeout=connect_timeout + read_timeout,
            connect=connect_timeout,
            read=read_timeout,
            write=read_timeout,
        )
        self.session = httpx.Client(timeout=timeout, follow_redirects=True)

    def validate_url(self, url: str) -> None:
        """Enforce HTTPS, strict domain whitelist, and SSRF prevention rules."""
        if not url:
            raise SecurityViolationError("URL cannot be empty.")

        parsed = urlparse(url)
        # Rule 1: HTTPS only
        if parsed.scheme.lower() != "https":
            raise SecurityViolationError(f"Protocol violation: Only HTTPS endpoints are permitted, got '{parsed.scheme}'.")

        hostname = (parsed.hostname or "").lower()
        if not hostname:
            raise SecurityViolationError("Invalid URL: Missing hostname.")

        # Rule 2: SSRF prevention — Reject IP literals and private address spaces
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                raise SecurityViolationError(f"SSRF violation: Access to private or reserved IP address '{hostname}' is blocked.")
            raise SecurityViolationError(f"Security violation: Direct IP address access is forbidden for government endpoints ({hostname}).")
        except ValueError:
            # Hostname is a domain name, not an IP literal
            pass

        # Rule 3: Domain whitelist
        if hostname not in ALLOWED_DOMAINS and not any(hostname.endswith("." + d) for d in ALLOWED_DOMAINS):
            raise SecurityViolationError(
                f"Domain access denied: Host '{hostname}' is not in the approved government domain whitelist. "
                f"Permitted domains: {', '.join(sorted(ALLOWED_DOMAINS))}"
            )

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Perform a hardened, rate-limited HTTP GET request with retry backoff."""
        self.validate_url(url)
        self._rate_limiter.acquire()

        req_headers = {
            "Accept": "application/json",
            "User-Agent": "UnifiedCitizenAIAgent/1.0",
        }
        if headers:
            req_headers.update(headers)

        attempt = 0
        while True:
            try:
                with self.session.stream("GET", url, params=params, headers=req_headers) as response:
                    # Check Content-Length header
                    content_length = response.headers.get("Content-Length")
                    if content_length and int(content_length) > MAX_RESPONSE_BYTES:
                        raise ResponseTooLargeError(
                            f"Response payload exceeds maximum size of {MAX_RESPONSE_BYTES} bytes (Content-Length: {content_length})."
                        )

                    # Stream chunks and enforce size cap
                    body_bytes = b""
                    for chunk in response.iter_bytes(chunk_size=8192):
                        body_bytes += chunk
                        if len(body_bytes) > MAX_RESPONSE_BYTES:
                            raise ResponseTooLargeError(f"Response stream exceeded {MAX_RESPONSE_BYTES} bytes.")

                    status_code = response.status_code
                    if status_code == 200:
                        content_type = response.headers.get("Content-Type", "").lower()
                        if "application/json" not in content_type and "application/xml" not in content_type and "text/xml" not in content_type:
                            logger.warning("Unexpected Content-Type '%s' received from %s", content_type, url)

                        try:
                            import json
                            return json.loads(body_bytes.decode("utf-8"))
                        except Exception as json_err:
                            raise GovernmentAPIError(f"Failed to parse JSON response: {str(json_err)}", status_code=status_code)

                    elif status_code == 401:
                        raise AuthenticationError("Official Government API authentication failed (401 Unauthorized).", status_code=status_code)
                    elif status_code == 403:
                        raise AuthorizationError("Official Government API access forbidden / subscription inactive (403 Forbidden).", status_code=status_code)
                    elif status_code == 404:
                        raise GovernmentAPIError(f"Resource not found on government portal (404 Not Found): {url}", status_code=status_code)
                    elif status_code == 429:
                        raise RateLimitError("Government API rate limit exceeded (HTTP 429).", status_code=status_code)
                    elif status_code in (500, 502, 503, 504):
                        raise ServerError(f"Government service returned server error (HTTP {status_code}).", status_code=status_code)
                    else:
                        raise GovernmentAPIError(f"Unexpected response from government API (HTTP {status_code}).", status_code=status_code)

            except (RateLimitError, ServerError, httpx.TimeoutException, httpx.NetworkError) as exc:
                attempt += 1
                if attempt > self.max_retries:
                    if isinstance(exc, httpx.TimeoutException):
                        raise TimeoutError(f"Request to {url} timed out after {self.connect_timeout + self.read_timeout}s.") from exc
                    if isinstance(exc, httpx.NetworkError):
                        raise NetworkError(f"Failed to connect to government endpoint: {str(exc)}") from exc
                    raise

                backoff_time = (0.5 * (2 ** (attempt - 1))) + random.uniform(0.05, 0.25)
                logger.info("Transient error %s calling %s. Retrying in %.2fs (attempt %d/%d)", type(exc).__name__, url, backoff_time, attempt, self.max_retries)
                time.sleep(backoff_time)
