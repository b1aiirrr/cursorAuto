from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

PERSONA_WEIGHTS = {
    "technical_analyst": 0.30,
    "macro_news": 0.20,
    "educator": 0.20,
    "community": 0.30,
}

PERSONA_PROMPTS = {
    "technical_analyst": [
        "Break down BTC support and resistance with RSI context for intraday traders.",
        "Analyze BNB trend structure with key levels and momentum warning signs.",
        "Create a chartless technical summary with bullish and bearish trigger zones.",
    ],
    "macro_news": [
        "Explain current ETF flow implications for short-term crypto sentiment.",
        "Summarize a global macro development and how it might affect risk assets.",
        "Cover one on-chain or exchange trend with implications for market positioning.",
    ],
    "educator": [
        "Teach one BNB Chain concept with a practical use-case for newcomers.",
        "Explain a Real World Asset tokenization idea in simple terms.",
        "Write an educational thread intro on wallet security and DeFi risk basics.",
    ],
    "community": [
        "Write a reflective community post asking followers about their weekly strategy.",
        "Post a mindset-focused message about discipline, risk, and long-term growth.",
        "Create an engagement question to spark comments from beginner and advanced users.",
    ],
}


@dataclass
class ContentPost:
    persona: str
    body: str
    tickers: list[str]
    sentiment: str
    image_prompt: str
    image_url: str


def choose_persona() -> str:
    personas = list(PERSONA_WEIGHTS.keys())
    weights = list(PERSONA_WEIGHTS.values())
    return random.choices(personas, weights=weights, k=1)[0]


async def fetch_trending_symbols(limit: int = 6) -> list[str]:
    url = "https://api.coingecko.com/api/v3/search/trending"
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.get(url)
            response.raise_for_status()
        payload = response.json()
        coins = payload.get("coins", [])
        symbols: list[str] = []
        for item in coins:
            symbol = item.get("item", {}).get("symbol", "").upper().strip()
            if symbol and symbol.isalpha() and symbol not in symbols:
                symbols.append(symbol)
            if len(symbols) >= limit:
                break
        return symbols
    except Exception:
        return ["BTC", "BNB", "SOL", "INJ", "ETH", "DOGE"]


async def fetch_sentiment_label() -> str:
    url = "https://api.alternative.me/fng/?limit=1&format=json"
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.get(url)
            response.raise_for_status()
        payload = response.json()
        value = int(payload["data"][0]["value"])
        if value >= 75:
            return "Extreme Greed"
        if value >= 56:
            return "Greed"
        if value >= 45:
            return "Neutral"
        if value >= 25:
            return "Fear"
        return "Extreme Fear"
    except Exception:
        return "Neutral"


def build_visual_prompt(primary: str, secondary: str, sentiment: str) -> str:
    return (
        "Dark-mode trading desk scene on a Lenovo ThinkPad T490s, "
        f"candlestick charts for {primary}/USDT and {secondary}/USDT, "
        f"market sentiment={sentiment}, neon cyan accents, high contrast, professional."
    )


def build_chart_url(symbol: str) -> str:
    return f"https://www.tradingview.com/symbols/{symbol}USDT/"


def build_text(persona: str, tickers: list[str], sentiment: str, timestamp: str, image_url: str) -> str:
    a, b, c = tickers[0], tickers[1], tickers[2]
    hooks = [
        f"Smart money is rotating again and ${a} is flashing first.",
        f"If you are still ignoring ${a}, ${b}, ${c}, you are late to the cycle.",
        f"Momentum is not random today - ${a} just pulled the market beta higher.",
    ]
    hook = random.choice(hooks)
    insights = {
        "technical_analyst": (
            f"🧠 ${a} structure still favors continuation while ${b} holds key support and ${c} compresses for breakout. "
            "📉 Dips are buyable only if buyers defend prior reclaim levels; lose that and momentum flips fast."
        ),
        "macro_news": (
            f"🧠 Risk appetite is {sentiment.lower()} and flows are rotating into high-beta names like ${a} and ${b}. "
            f"🚀 ${c} is usually the lagger that catches up once the leaders hold trend."
        ),
        "educator": (
            f"🧠 Watch how ${a} and ${b} react around liquidity zones - this is where entries are made, not in random candles. "
            f"📉 ${c} is a reminder that conviction without risk control gets punished quickly."
        ),
        "community": (
            f"🧠 The edge is not hype, it is execution - ${a}, ${b}, ${c} are giving clean levels if you stay patient. "
            "🚀 Chasing green candles is where most traders donate to the market."
        ),
    }[persona]
    engagement = f"What is your setup right now on ${a} or ${b}? Stay sharp."
    tags = f"#{a} #{b} #BinanceSquare"
    return (
        f"{hook}\n\n"
        f"{insights}\n\n"
        f"📊 Chart: {image_url}\n"
        f"🕒 {timestamp}\n\n"
        f"{engagement}\n\n"
        f"{tags}"
    )


async def build_post() -> ContentPost:
    tz = ZoneInfo("Africa/Nairobi")
    persona = choose_persona()
    _ = random.choice(PERSONA_PROMPTS[persona])
    trending, sentiment = await asyncio.gather(
        fetch_trending_symbols(),
        fetch_sentiment_label(),
    )
    picked = trending[:3] if len(trending) >= 3 else ["BTC", "BNB", "SOL"]
    timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M EAT")
    image_url = build_chart_url(picked[0])
    image_prompt = build_visual_prompt(picked[0], picked[1], sentiment)
    body = build_text(persona, picked, sentiment, timestamp, image_url)
    return ContentPost(
        persona=persona,
        body=body,
        tickers=picked,
        sentiment=sentiment,
        image_prompt=image_prompt,
        image_url=image_url,
    )
