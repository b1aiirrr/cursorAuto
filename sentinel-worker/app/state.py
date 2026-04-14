from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import BaseModel


class LogEntry(BaseModel):
    ts: str
    level: str
    message: str


class SharedState:
    def __init__(self) -> None:
        self.tz = ZoneInfo("Africa/Nairobi")
        self.status: str = "offline"
        self.next_post_at: datetime | None = None
        self.last_post_at: datetime | None = None
        self.post_history: list[dict[str, Any]] = []
        self.logs: list[LogEntry] = []
        self.subscribers: set[asyncio.Queue[str]] = set()
        self.lock = asyncio.Lock()

    async def add_log(self, level: str, message: str) -> None:
        entry = LogEntry(ts=datetime.now(self.tz).isoformat(), level=level, message=message)
        payload = json.dumps(entry.model_dump())
        async with self.lock:
            self.logs.append(entry)
            if len(self.logs) > 500:
                self.logs = self.logs[-500:]
            stale: list[asyncio.Queue[str]] = []
            for queue in self.subscribers:
                try:
                    queue.put_nowait(payload)
                except asyncio.QueueFull:
                    stale.append(queue)
            for queue in stale:
                self.subscribers.discard(queue)

    async def add_post(self, post: dict[str, Any]) -> None:
        async with self.lock:
            self.post_history.append(post)
            if len(self.post_history) > 1000:
                self.post_history = self.post_history[-1000:]
            self.last_post_at = datetime.now(self.tz)

    async def snapshot(self) -> dict[str, Any]:
        async with self.lock:
            today = datetime.now(self.tz).date().isoformat()
            today_posts = [p for p in self.post_history if p.get("posted_date") == today]
            confidence_values = [
                float(p.get("trend_confidence", 0.0))
                for p in today_posts
                if isinstance(p.get("trend_confidence", 0.0), (int, float))
            ]
            avg_confidence = (
                round(sum(confidence_values) / len(confidence_values), 2)
                if confidence_values
                else 0.0
            )
            binance_priority_count = sum(
                1 for p in today_posts if p.get("trend_source") == "binance-square-priority"
            )
            return {
                "status": self.status,
                "next_post_at": self.next_post_at.isoformat() if self.next_post_at else None,
                "last_post_at": self.last_post_at.isoformat() if self.last_post_at else None,
                "posts_today": len(today_posts),
                "history_size": len(self.post_history),
                "trend_confidence_today_avg": avg_confidence,
                "trend_priority_posts_today": binance_priority_count,
                "recent_logs": [entry.model_dump() for entry in self.logs[-25:]],
            }


def load_posts(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_posts(path: Path, posts: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(posts, indent=2), encoding="utf-8")
