import asyncio
import logging
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}


class HttpClient:
    _client: Optional[httpx.AsyncClient] = None

    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None or cls._client.is_closed:
            cls._client = httpx.AsyncClient(
                headers=DEFAULT_HEADERS,
                timeout=httpx.Timeout(20.0, connect=10.0),
                follow_redirects=True,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
            )
        return cls._client

    @classmethod
    async def close(cls) -> None:
        if cls._client is not None and not cls._client.is_closed:
            await cls._client.aclose()
            cls._client = None

    @classmethod
    async def get(
        cls,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        retries: int = 3,
        backoff_factor: float = 0.5,
    ) -> str:
        client = await cls.get_client()
        request_headers = DEFAULT_HEADERS.copy()
        if headers:
            request_headers.update(headers)

        for attempt in range(1, retries + 1):
            try:
                response = await client.get(url, headers=request_headers)
                response.raise_for_status()
                return response.text
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                logger.warning(f"GET request to {url} failed on attempt {attempt}/{retries}: {e}")
                if attempt == retries:
                    raise
                await asyncio.sleep(backoff_factor * (2 ** (attempt - 1)))
        raise RuntimeError(f"Failed to GET {url} after {retries} retries")

    @classmethod
    async def post_json(
        cls,
        url: str,
        json_data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        retries: int = 3,
        backoff_factor: float = 0.5,
    ) -> Dict[str, Any]:
        client = await cls.get_client()
        request_headers = DEFAULT_HEADERS.copy()
        request_headers["Content-Type"] = "application/json"
        if headers:
            request_headers.update(headers)

        for attempt in range(1, retries + 1):
            try:
                response = await client.post(url, json=json_data, headers=request_headers)
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                logger.warning(f"POST JSON to {url} failed on attempt {attempt}/{retries}: {e}")
                if attempt == retries:
                    raise
                await asyncio.sleep(backoff_factor * (2 ** (attempt - 1)))
        raise RuntimeError(f"Failed to POST {url} after {retries} retries")
