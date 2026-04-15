from __future__ import annotations

import asyncio
import os
import random
import re
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
    trend_topics: list[str]
    trend_source: str
    trend_confidence: float


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


async def fetch_binance_square_topics(limit: int = 12) -> list[str]:
    url = os.getenv("BINANCE_SQUARE_TRENDS_URL", "https://www.binance.com/en/square/trends")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
        ),
    }
    try:
        async with httpx.AsyncClient(timeout=12, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
        html = response.text
        matches = re.findall(r"#([A-Za-z0-9_]{3,40})", html)
        topics: list[str] = []
        for item in matches:
            topic = f"#{item}"
            if topic not in topics:
                topics.append(topic)
            if len(topics) >= limit:
                break
        return topics
    except Exception:
        return []


def _load_allowed_symbols() -> list[str]:
    raw = os.getenv(
        "TREND_ALLOWED_SYMBOLS",
        "BTC,ETH,BNB,SOL,XRP,ADA,DOGE,SUI,TON,INJ,TRX,AVAX,LINK,DOT,ATOM,NEAR,LTC",
    )
    return [item.strip().upper() for item in raw.split(",") if item.strip()]


def _load_blocked_symbols() -> set[str]:
    raw = os.getenv("TREND_BLOCKED_SYMBOLS", "")
    return {item.strip().upper() for item in raw.split(",") if item.strip()}


def _symbol_from_topic(topic: str) -> str | None:
    normalized = topic.upper().replace("#", "")
    compact = re.sub(r"[^A-Z0-9]", "", normalized)
    keyword_map = {
        "BTC": "BTC",
        "BITCOIN": "BTC",
        "ETH": "ETH",
        "ETHEREUM": "ETH",
        "BNB": "BNB",
        "SOL": "SOL",
        "SOLANA": "SOL",
        "XRP": "XRP",
        "DOGE": "DOGE",
        "ADA": "ADA",
        "SUI": "SUI",
        "TON": "TON",
        "INJ": "INJ",
    }
    for key, symbol in keyword_map.items():
        if key in compact:
            return symbol
    if compact.isalpha() and 2 <= len(compact) <= 6:
        return compact
    return None


def build_trend_priority_symbols(topics: list[str], fallback: list[str], limit: int = 6) -> list[str]:
    allowed_symbols = set(_load_allowed_symbols())
    blocked_symbols = _load_blocked_symbols()
    combined: list[str] = []
    for topic in topics:
        symbol = _symbol_from_topic(topic)
        if (
            symbol
            and symbol not in combined
            and symbol in allowed_symbols
            and symbol not in blocked_symbols
        ):
            combined.append(symbol)
        if len(combined) >= limit:
            return combined
    for symbol in fallback:
        if symbol in blocked_symbols:
            continue
        if allowed_symbols and symbol not in allowed_symbols:
            continue
        if symbol not in combined:
            combined.append(symbol)
        if len(combined) >= limit:
            break
    return combined


def score_trend_confidence(trend_topics: list[str], picked: list[str]) -> float:
    if not picked:
        return 0.0
    upper_topics = [topic.upper() for topic in trend_topics]
    hits = 0
    for symbol in picked:
        if any(symbol in topic for topic in upper_topics):
            hits += 1
    return round(hits / max(len(picked), 1), 2)


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


def build_text(
    persona: str,
    tickers: list[str],
    sentiment: str,
    timestamp: str,
    image_url: str,
    trend_topics: list[str],
) -> str:
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
    trend_line = (
        "🔥 Binance Square trends: " + " ".join(trend_topics[:3])
        if trend_topics
        else "🔥 Binance Square trends: #Crypto #BinanceSquare"
    )
    return (
        f"{hook}\n\n"
        f"{trend_line}\n\n"
        f"{insights}\n\n"
        f"📊 Chart: {image_url}\n"
        f"🕒 {timestamp}\n\n"
        f"{engagement}\n\n"
        f"{tags}"
    )


# ---------------------------------------------------------------------------
# Content Generation (Advanced)
# ---------------------------------------------------------------------------
async def fetch_trending_topics() -> list[dict]:
    """Fetch real-time trending topics from Binance Square."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://www.binance.com/bapi/composite/v1/public/pgc/square/trending/topic/list")
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == "000000":
                    return data.get("data", [])[:5]
    except Exception as e:
        pass
    return []

async def generate_content_advanced(persona: str) -> tuple[str, list[str]]:
    from .content_generator import generate_content
    from binance.client import Client
    
    market_data = {}
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    
    if api_key and api_secret:
        try:
            client = Client(api_key, api_secret)
            tickers = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]
            prices = client.get_all_tickers()
            market_data = {p["symbol"].replace("USDT", ""): float(p["price"]) for p in prices if p["symbol"] in tickers}
        except:
            pass

    trending_topics = await fetch_trending_topics()
    content, tickers = await generate_content(persona, market_data, trending_topics)
    return content, tickers

async def build_post() -> ContentPost:
    tz = ZoneInfo("Africa/Nairobi")
    persona = choose_persona()
    
    # Use Advanced Content Generation
    body, picked = await generate_content_advanced(persona)
    
    # Still fetch metadata for tracking
    trend_topics, trending, sentiment = await asyncio.gather(
        fetch_binance_square_topics(),
        fetch_trending_symbols(),
        fetch_sentiment_label(),
    )
    
    trend_source = "gemini-ai-advanced"
    trend_confidence = 0.95
    timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M EAT")
    image_url = build_chart_url(picked[0] if picked else "BTC")
    image_prompt = build_visual_prompt(picked[0] if picked else "BTC", picked[1] if len(picked)>1 else "BNB", sentiment)
    
    return ContentPost(
        persona=persona,
        body=body,
        tickers=picked,
        sentiment=sentiment,
        image_prompt=image_prompt,
        image_url=image_url,
        trend_topics=trend_topics,
        trend_source=trend_source,
        trend_confidence=trend_confidence,
    )
