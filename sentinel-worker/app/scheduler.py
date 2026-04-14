from __future__ import annotations

import asyncio
import os
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from .engine import build_post
from .publisher import BinanceSquarePublisher, PublisherError
from .state import SharedState, load_posts, save_posts

MIN_JITTER_MINUTES = 17
MAX_JITTER_MINUTES = 78
MIN_POSTS = 30
MAX_POSTS = 50


def is_modern_post(post: dict) -> bool:
    required_keys = ("tickers", "sentiment", "image_prompt", "image_url")
    return all(key in post for key in required_keys)


def normalize_post(post: dict) -> dict:
    normalized = dict(post)
    normalized.setdefault("trend_topics", [])
    normalized.setdefault("trend_source", "legacy")
    normalized.setdefault("trend_confidence", 0.0)
    return normalized


class Scheduler:
    def __init__(self, state: SharedState, posts_path: Path) -> None:
        load_dotenv()
        self.state = state
        self.posts_path = posts_path
        self.tz = ZoneInfo(os.getenv("TIMEZONE", "Africa/Nairobi"))
        self.sleep_start = self._parse_clock(os.getenv("SLEEP_WINDOW_START", "02:00"))
        self.sleep_end = self._parse_clock(os.getenv("SLEEP_WINDOW_END", "07:00"))
        self.target_posts_today = random.randint(MIN_POSTS, MAX_POSTS)
        self.publisher = BinanceSquarePublisher()

    def _parse_clock(self, value: str) -> time:
        hour, minute = value.split(":")
        return time(hour=int(hour), minute=int(minute))

    def _in_sleep_window(self, now: datetime) -> bool:
        current = now.timetz().replace(tzinfo=None)
        return self.sleep_start <= current <= self.sleep_end

    def _next_wakeup(self, now: datetime) -> datetime:
        wake = datetime.combine(now.date(), self.sleep_end, tzinfo=self.tz)
        if wake <= now:
            wake = wake + timedelta(days=1)
        return wake

    async def _publish(self, payload: dict[str, str]) -> None:
        if self.publisher.is_configured():
            response = await self.publisher.publish(
                payload["body"], image_url=payload.get("image_url")
            )
            nested_data = response.get("data", {}) if isinstance(response, dict) else {}
            reference = (
                response.get("id")
                or response.get("postId")
                or nested_data.get("id")
                or nested_data.get("postId")
                or "unknown"
            )
            await self.state.add_log(
                "info",
                f"Published {payload['persona']} post to Primary Binance Square (ref: {reference})",
            )

            if self.publisher.friend_square_api_key:
                try:
                    friend_response = await self.publisher.publish_to_friend(
                        payload["body"], image_url=payload.get("image_url")
                    )
                    friend_nested = friend_response.get("data", {}) if isinstance(friend_response, dict) else {}
                    friend_ref = (
                        friend_response.get("id")
                        or friend_response.get("postId")
                        or friend_nested.get("id")
                        or friend_nested.get("postId")
                        or "unknown"
                    )
                    await self.state.add_log(
                        "info",
                        f"Cross-posted {payload['persona']} post to Friend Binance Square (ref: {friend_ref})",
                    )
                except PublisherError as exc:
                    await self.state.add_log(
                        "error",
                        f"Failed to cross-post to Friend account: {exc}",
                    )
            return

        if self.publisher.enabled:
            raise PublisherError(
                "BINANCE_REAL_POSTING=true but required publisher env is missing."
            )

        await asyncio.sleep(random.uniform(0.4, 1.4))
        await self.state.add_log(
            "warn",
            "Real posting disabled; running in simulation mode.",
        )
        await self.state.add_log(
            "info", f"Simulated publish for {payload['persona']} post to Binance Square"
        )

    async def run(self) -> None:
        loaded_posts = load_posts(self.posts_path)
        posts = [normalize_post(post) for post in loaded_posts if is_modern_post(post)]
        if len(posts) != len(loaded_posts):
            save_posts(self.posts_path, posts)
            await self.state.add_log(
                "warn",
                f"Pruned {len(loaded_posts) - len(posts)} legacy posts from history",
            )

        for post in posts[-200:]:
            await self.state.add_post(post)

        await self.state.add_log("info", f"Daily target set to {self.target_posts_today} posts")

        while True:
            now = datetime.now(self.tz)
            posted_today = [
                p for p in posts if p.get("posted_date") == now.date().isoformat()
            ]
            if len(posted_today) >= self.target_posts_today:
                self.target_posts_today = random.randint(MIN_POSTS, MAX_POSTS)
                await self.state.add_log("info", f"Daily target reached. Resetting next target to {self.target_posts_today} posts")
                await asyncio.sleep(60)
                continue

            if self._in_sleep_window(now):
                self.state.status = "sleeping"
                wakeup = self._next_wakeup(now)
                self.state.next_post_at = wakeup
                await self.state.add_log("warn", f"Sleep window active until {wakeup.isoformat()}")
                await asyncio.sleep(max((wakeup - now).total_seconds(), 60))
                continue

            self.state.status = "posting"
            post = await build_post()
            payload = {
                "persona": post.persona,
                "body": post.body,
                "tickers": post.tickers,
                "sentiment": post.sentiment,
                "image_prompt": post.image_prompt,
                "image_url": post.image_url,
                "trend_topics": post.trend_topics,
                "trend_source": post.trend_source,
                "trend_confidence": post.trend_confidence,
                "posted_at": now.isoformat(),
                "posted_date": now.date().isoformat(),
                "channel": "binance-square",
            }

            try:
                await self._publish(payload)
            except PublisherError as exc:
                self.state.status = "offline"
                await self.state.add_log("error", str(exc))
                await asyncio.sleep(60)
                continue

            posts.append(payload)
            save_posts(self.posts_path, posts)
            await self.state.add_post(payload)

            wait_minutes = random.randint(MIN_JITTER_MINUTES, MAX_JITTER_MINUTES)
            next_at = datetime.now(self.tz) + timedelta(minutes=wait_minutes)
            self.state.next_post_at = next_at
            await self.state.add_log("info", f"Next post scheduled in {wait_minutes} minutes")
            await asyncio.sleep(wait_minutes * 60)
