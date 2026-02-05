from __future__ import annotations

import os
import json
import re
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

# -------------------- load dotenv ----------------

from dotenv import load_dotenv
load_dotenv()


# -------------------- logging --------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("watchdog_aiogram_mvp")


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_config(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        template = {
            "api_endpoint": "http://localhost:8000/api/signals",
            "api_key": "",
            "skip_keywords": ["pin", "закреп", "pinned", "admin", "реклама", "#Report", "LongReport"],
            "chats": {
                "-1001111111111": "TOTAL",
                "-1002222222222": "BITCOIN",
                "-1003333333333": "ETH"
            }
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        raise SystemExit(f"Создан шаблон {path}. Заполни chat_id и запусти снова.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# region parsers
# -------------------- parsers (под твои примеры) --------------------
RE_TSB = re.compile(r"Ⓜ️\s*TSB\s*(LONG|SHORT)\s*Report\s*#([0-9]+/[0-9]+)", re.IGNORECASE)
RE_BID = re.compile(r"BID\s*строки\s*[>≥]?\s*(\d+)", re.IGNORECASE)
RE_GROWTH = re.compile(r"Расчетный\s*(?:рост|отскок).*?(\d+(?:-\d+)?%)", re.IGNORECASE)

RE_LONG_COMBO = re.compile(r"(🟢+)\s*LONG\s*COMBO\s*(\d+)", re.IGNORECASE)
RE_HORIZON = re.compile(r"Горизонт:\s*(.+?)(?:\s*\|?\s*Цель:|$)", re.IGNORECASE)
RE_TARGET = re.compile(r"Цель:\s*(.+?)(?:\n|$)", re.IGNORECASE)

RE_BTC_SIGNAL = re.compile(r"🧠\s*BTC\s*Signal", re.IGNORECASE)
RE_ZONE_STRATEGY = re.compile(r"Стратегия:\s*(\w+)", re.IGNORECASE)
RE_ZONE_LEVEL = re.compile(r"Уровень:\s*([0-9]️⃣|[0-9])", re.IGNORECASE)
RE_ZONE_DIR = re.compile(r"Направление:\s*(LONG|SHORT)", re.IGNORECASE)

RE_ETH_AI = re.compile(r"🧠\s*ETH\s*AI\s*v2", re.IGNORECASE)
RE_ETH_STRATEGY = re.compile(r"Стратегия:\s*(\w+)", re.IGNORECASE)
RE_ETH_LEVEL = re.compile(r"Уровень:\s*(\d+)", re.IGNORECASE)
RE_ETH_TYPE = re.compile(r"Тип:\s*(\w+)", re.IGNORECASE)
RE_ETH_DIR = re.compile(r"Направление:\s*([🟢🔴])\s*(LONG|SHORT)", re.IGNORECASE)
RE_AI_STRENGTH = re.compile(r"Сила\s*сигнала:.*?(\d+)\s*/\s*100", re.IGNORECASE)
RE_CONCLUSION = re.compile(r"Вывод:\s*(.+?)(?:\n|$)", re.IGNORECASE)

# endregion

def extract_spot_price(text: str, symbol: str) -> Optional[float]:
    m = re.search(rf"{symbol}/USDT-SPOT:\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def normalize_action(long_or_short: str) -> str:
    return "BUY" if long_or_short.upper() == "LONG" else "SELL"


def emoji_digit_to_int(s: str) -> Optional[int]:
    m = re.search(r"(\d)", s)
    return int(m.group(1)) if m else None


def parse_total(text: str) -> Optional[Dict[str, Any]]:
    m = RE_TSB.search(text)
    if not m:
        return None

    side = m.group(1).upper()
    report_no = m.group(2)

    bid_lines = None
    mb = RE_BID.search(text)
    if mb:
        bid_lines = int(mb.group(1))

    growth = None
    mg = RE_GROWTH.search(text)
    if mg:
        growth = mg.group(1)

    price = extract_spot_price(text, "BTC")

    return {
        "symbol": "ALTS/USDT",
        "action": normalize_action(side),
        "price": price,
        "signal_type": f"TSB_REPORT_{report_no}",
        "strength": None,
        "extra": {"bid_lines": bid_lines, "expected_growth": growth},
        "raw_text": text[:1000],
    }


def parse_bitcoin_combo(text: str) -> Optional[Dict[str, Any]]:
    m = RE_LONG_COMBO.search(text)
    if not m:
        return None

    emojis = m.group(1)
    combo_n = int(m.group(2))
    strength = len(emojis)

    price = extract_spot_price(text, "BTC")
    horizon = (RE_HORIZON.search(text).group(1).strip() if RE_HORIZON.search(text) else None)
    target = (RE_TARGET.search(text).group(1).strip() if RE_TARGET.search(text) else None)

    return {
        "symbol": "BTC/USDT",
        "action": "BUY",
        "price": price,
        "signal_type": f"LONG_COMBO_{combo_n}",
        "strength": strength,
        "extra": {"horizon": horizon, "target": target},
        "raw_text": text[:1000],
    }


def parse_bitcoin_zone(text: str) -> Optional[Dict[str, Any]]:
    if not RE_BTC_SIGNAL.search(text):
        return None

    strategy = "ZONE"
    ms = RE_ZONE_STRATEGY.search(text)
    if ms:
        strategy = ms.group(1).strip()

    level = None
    ml = RE_ZONE_LEVEL.search(text)
    if ml:
        level = emoji_digit_to_int(ml.group(1))

    md = RE_ZONE_DIR.search(text)
    if not md:
        return None
    side = md.group(1).upper()

    price = extract_spot_price(text, "BTC")

    return {
        "symbol": "BTC/USDT",
        "action": normalize_action(side),
        "price": price,
        "signal_type": f"{strategy}_LEVEL_{level}" if level is not None else strategy,
        "strength": level,
        "extra": {"strategy": strategy, "level": level},
        "raw_text": text[:1000],
    }


def parse_eth_ai(text: str) -> Optional[Dict[str, Any]]:
    if not RE_ETH_AI.search(text):
        return None

    strategy = (RE_ETH_STRATEGY.search(text).group(1).strip() if RE_ETH_STRATEGY.search(text) else "UNKNOWN")
    level = (int(RE_ETH_LEVEL.search(text).group(1)) if RE_ETH_LEVEL.search(text) else None)
    typ = (RE_ETH_TYPE.search(text).group(1).strip() if RE_ETH_TYPE.search(text) else None)

    md = RE_ETH_DIR.search(text)
    if not md:
        return None
    side = md.group(2).upper()

    price = extract_spot_price(text, "ETH")
    ai_strength = (int(RE_AI_STRENGTH.search(text).group(1)) if RE_AI_STRENGTH.search(text) else None)
    conclusion = (RE_CONCLUSION.search(text).group(1).strip() if RE_CONCLUSION.search(text) else None)

    return {
        "symbol": "ETH/USDT",
        "action": normalize_action(side),
        "price": price,
        "signal_type": f"ETH_AI_{strategy}_LEVEL_{level}" if level is not None else f"ETH_AI_{strategy}",
        "strength": level,
        "extra": {"strategy": strategy, "level": level, "eth_type": typ, "ai_strength": ai_strength, "conclusion": conclusion},
        "raw_text": text[:1000],
    }


GROUP_PARSERS = {
    "TOTAL": [parse_total],
    "BITCOIN": [parse_bitcoin_combo, parse_bitcoin_zone],
    "ETH": [parse_eth_ai],
}


# -------------------- app --------------------
CONFIG_PATH = os.getenv("WATCHDOG_CONFIG", "watchdog_config.json")
config = load_config(CONFIG_PATH)

API_ENDPOINT = os.getenv("API_ENDPOINT", config.get("api_endpoint", "http://localhost:8000/api/signals"))
API_KEY = os.getenv("API_KEY", config.get("api_key", ""))

SKIP_KEYWORDS: List[str] = [s.lower() for s in config.get("skip_keywords", [])]
CHAT_GROUP: Dict[int, str] = {int(k): v for k, v in config.get("chats", {}).items()}

BOT_TOKEN = os.getenv("BOT_TOKEN_PARSER")

# TODO:

if not BOT_TOKEN:
    raise RuntimeError("Нужно задать BOT_TOKEN в env")


bot = Bot(BOT_TOKEN)
dp = Dispatcher()

_http: Optional[aiohttp.ClientSession] = None


def should_skip(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in SKIP_KEYWORDS)


def parse_by_group(text: str, group: str) -> Optional[Dict[str, Any]]:
    for fn in GROUP_PARSERS.get(group, []):
        sig = fn(text)
        if sig:
            return sig
    return None


async def send_to_api(payload: Dict[str, Any]) -> bool:
    global _http
    if _http is None:
        _http = aiohttp.ClientSession()

    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY

    try:
        async with _http.post(API_ENDPOINT, json=payload, headers=headers, timeout=10) as r:
            if r.status in (200, 201):
                return True
            body = await r.text()
            log.warning("API error status=%s body=%s", r.status, body[:300])
            return False
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        log.warning("API network error: %s", e)
        return False


@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer(
        "Watchdog MVP (aiogram).\n"
        "Команды:\n"
        "/chatid — узнать chat_id\n\n"
        "Чтобы бот видел ВСЕ сообщения в группе: выключи Privacy Mode в BotFather."
    )


@dp.message(Command("chatid"))
async def chatid_cmd(message: Message):
    await message.answer(f"chat_id = {message.chat.id}")


@dp.message(F.text)
async def on_text(message: Message):

    log.info("INCOMING: chat_id=%s text=%r", message.chat.id, (message.text or "")[:40]) # получает ли сообщения вообще
    # слушаем только чаты из конфига
    group = CHAT_GROUP.get(message.chat.id)

    if not group:
        log.info("SKIP: chat_id %s not in config chats", message.chat.id) # есть ли чат вообще()
        return

    text = message.text or ""
    text = message.text or ""
    if not text or should_skip(text):
        return

    sig = parse_by_group(text, group)
    if not sig:
        return

    payload = {
        "source": group,
        "channel": message.chat.title or message.chat.username or str(message.chat.id),
        "chat_id": message.chat.id,
        "message_id": message.message_id,
        "timestamp": utc_iso(),
        "symbol": sig["symbol"],
        "action": sig["action"],
        "price": sig.get("price"),
        "signal_type": sig.get("signal_type", "UNKNOWN"),
        "strength": sig.get("strength"),
        "extra": sig.get("extra", {}),
        "raw_text": sig.get("raw_text", text[:1000]),
    }

    ok = await send_to_api(payload)
    if ok:
        log.info("OK: %s %s (%s) chat=%s msg=%s", payload["action"], payload["symbol"], payload["signal_type"], payload["chat_id"], payload["message_id"])
    else:
        log.error("FAIL: %s %s (%s) chat=%s msg=%s", payload["action"], payload["symbol"], payload["signal_type"], payload["chat_id"], payload["message_id"])


async def main():
    global _http
    try:
        await dp.start_polling(bot, allowed_updates=["message"])
    finally:
        if _http and not _http.closed:
            await _http.close()


if __name__ == "__main__":
    asyncio.run(main())
