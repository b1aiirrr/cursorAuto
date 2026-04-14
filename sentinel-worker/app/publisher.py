from __future__ import annotations

import os

import httpx


class PublisherError(Exception):
    pass


class BinanceSquarePublisher:
    def __init__(self) -> None:
        self.square_open_api_key = os.getenv("BINANCE_SQUARE_OPENAPI_KEY", "").strip()
        self.friend_square_api_key = os.getenv("FRIEND_SQUARE_API_KEY", "").strip()
        self.post_url = os.getenv(
            "BINANCE_SQUARE_POST_URL",
            "https://www.binance.com/bapi/composite/v1/public/pgc/openApi/content/add",
        ).strip()
        self.enabled = os.getenv("BINANCE_REAL_POSTING", "false").lower() == "true"
        self.timeout = float(os.getenv("BINANCE_HTTP_TIMEOUT_SECONDS", "20"))
        self.media_post_url = os.getenv("BINANCE_SQUARE_MEDIA_POST_URL", "").strip()

    def is_configured(self) -> bool:
        return self.enabled and bool(self.square_open_api_key and self.post_url)

    async def _post(self, url: str, payload: dict, headers: dict) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.post(url, json=payload, headers=headers)

    async def publish(self, content: str, image_url: str | None = None) -> dict:
        if not self.enabled:
            raise PublisherError("Real posting disabled. Set BINANCE_REAL_POSTING=true.")
        if not self.square_open_api_key:
            raise PublisherError("Missing BINANCE_SQUARE_OPENAPI_KEY.")

        headers = {
            "X-Square-OpenAPI-Key": self.square_open_api_key,
            "Content-Type": "application/json",
            "clienttype": "binanceSkill",
        }
        payload = {"bodyTextOnly": content}
        response = await self._post(self.post_url, payload, headers)

        # Optional media endpoint: if configured and image URL provided, try media post first.
        if image_url and self.media_post_url:
            media_payload = {"bodyTextOnly": content, "imageUrl": image_url}
            media_response = await self._post(self.media_post_url, media_payload, headers)
            if media_response.status_code < 400:
                response = media_response

        if response.status_code >= 400:
            raise PublisherError(
                f"Binance publish failed ({response.status_code}): {response.text[:300]}"
            )

        try:
            data = response.json()
        except ValueError:
            return {"ok": True, "raw": response.text[:500]}

        if str(data.get("code")) != "000000":
            raise PublisherError(
                f"Binance publish rejected (code={data.get('code')}): {data.get('message')}"
            )
        return data

    async def publish_to_friend(self, content: str, image_url: str | None = None) -> dict:
        """Publish content to the friend's account."""
        if not self.enabled:
            raise PublisherError("Real posting disabled. Set BINANCE_REAL_POSTING=true.")
        if not self.friend_square_api_key:
            raise PublisherError("Missing FRIEND_SQUARE_API_KEY.")

        headers = {
            "X-Square-OpenAPI-Key": self.friend_square_api_key,
            "Content-Type": "application/json",
            "clienttype": "binanceSkill",
        }
        payload = {"bodyTextOnly": content}
        response = await self._post(self.post_url, payload, headers)

        if response.status_code >= 400:
            raise PublisherError(
                f"Friend publish failed ({response.status_code}): {response.text[:300]}"
            )

        try:
            data = response.json()
        except ValueError:
            return {"ok": True, "raw": response.text[:500]}

        if str(data.get("code")) != "000000":
            raise PublisherError(
                f"Friend publish rejected (code={data.get('code')}): {data.get('message')}"
            )
        return data
