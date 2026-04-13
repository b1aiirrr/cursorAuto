from __future__ import annotations

import hashlib
import hmac
import os
import time
from urllib.parse import urlencode

import httpx


class PublisherError(Exception):
    pass


class BinanceSquarePublisher:
    def __init__(self) -> None:
        self.api_key = os.getenv("BINANCE_API_KEY", "").strip()
        self.api_secret = os.getenv("BINANCE_API_SECRET", "").strip()
        self.post_url = os.getenv("BINANCE_SQUARE_POST_URL", "").strip()
        self.enabled = os.getenv("BINANCE_REAL_POSTING", "false").lower() == "true"
        self.timeout = float(os.getenv("BINANCE_HTTP_TIMEOUT_SECONDS", "20"))

    def is_configured(self) -> bool:
        return self.enabled and bool(self.api_key and self.api_secret and self.post_url)

    def _signature(self, payload: dict[str, str]) -> str:
        query = urlencode(payload)
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    async def publish(self, content: str) -> dict:
        if not self.enabled:
            raise PublisherError("Real posting disabled. Set BINANCE_REAL_POSTING=true.")
        if not self.post_url:
            raise PublisherError("Missing BINANCE_SQUARE_POST_URL.")
        if not self.api_key or not self.api_secret:
            raise PublisherError("Missing BINANCE_API_KEY or BINANCE_API_SECRET.")

        payload = {
            "content": content,
            "timestamp": str(int(time.time() * 1000)),
        }
        signature = self._signature(payload)
        signed_payload = {**payload, "signature": signature}

        headers = {
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.post_url, data=signed_payload, headers=headers)

        if response.status_code >= 400:
            raise PublisherError(
                f"Binance publish failed ({response.status_code}): {response.text[:300]}"
            )

        try:
            return response.json()
        except ValueError:
            return {"ok": True, "raw": response.text[:500]}
