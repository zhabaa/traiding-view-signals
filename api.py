from __future__ import annotations
from fastapi import FastAPI, Request, HTTPException
from db.database_sqlite import SignalsDB

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import os
import random

import aiohttp
from datetime import datetime, timezone

API_KEY = os.getenv("API_KEY", "")
DB_PATH = os.getenv("DB_PATH", "signals.db")


def iso_to_epoch_seconds(ts: str) -> int:
    # пример: "2026-02-05T15:15:52.695190+00:00"
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return int(dt.timestamp())


db = SignalsDB(DB_PATH)
app = FastAPI()

app.mount("/assets", StaticFiles(directory="website-graph/assets"), name="assets")


@app.get("/")
def index():
    return FileResponse("website-graph/index.html")


@app.get("/api/markers")
def markers(symbol: str = "BTC/USDT", limit: int = 200, since_id: int = 0):
    rows = db.list_signals(limit=limit, symbol=symbol)

    # rows у тебя идут от новых к старым, разворачиваем
    rows = list(reversed(rows))

    out = []
    last_id = since_id

    for r in rows:
        rid = int(r.get("id", 0))
        if rid <= since_id:
            continue

        ts = r.get("timestamp")
        if not ts:
            continue

        t = iso_to_epoch_seconds(ts)
        action = (r.get("action") or "").upper()
        price = r.get("price")

        # position: aboveBar для SELL, belowBar для BUY
        position = "belowBar" if action == "BUY" else "aboveBar"
        shape = "arrowUp" if action == "BUY" else "arrowDown"
        text = f"{r.get('signal_type', 'SIG')} @ {price}" if price is not None else f"{r.get('signal_type', 'SIG')}"

        out.append({
            "time": t,
            "position": position,
            "shape": shape,
            "text": text[:80],
        })

        if rid > last_id:
            last_id = rid

    return {"markers": out, "last_id": last_id}


TF_SECONDS = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "1h": 3600,
}

BINANCE_TF = {
    "1m": "1m",
    "3m": "3m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "2h": "2h",
    "4h": "4h",
    "1d": "1d",
}

def to_binance_symbol(symbol: str) -> str:
    # "BTC/USDT" -> "BTCUSDT"
    return symbol.replace("/", "").replace("-", "").upper()

@app.get("/api/candles")
async def candles(symbol: str = "BTC/USDT", tf: str = "1m", limit: int = 500):
    interval = BINANCE_TF.get(tf, "1m")
    limit = max(10, min(int(limit), 1000))  # Binance limit <= 1000

    bsymbol = to_binance_symbol(symbol)

    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": bsymbol, "interval": interval, "limit": limit}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as r:
                if r.status != 200:
                    text = await r.text()
                    return {"error": f"binance status={r.status}", "details": text[:200]}
                data = await r.json()
    except Exception as e:
        return {"error": "binance request failed", "details": str(e)}

    # Binance kline format:
    # [
    #  [
    #    1499040000000, "0.01634790", "0.80000000", "0.01575800", "0.01577100", ...
    #  ],
    #  ...
    # ]
    out = []
    for k in data:
        open_time_ms = int(k[0])
        o = float(k[1]); h = float(k[2]); l = float(k[3]); c = float(k[4])
        out.append({
            "time": open_time_ms // 1000,  # lightweight-charts ждёт seconds
            "open": o,
            "high": h,
            "low": l,
            "close": c,
        })

    return out


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/api/signals")
async def ingest(req: Request):
    # если нужен ключ — проверяем
    if API_KEY:
        got = req.headers.get("X-API-Key", "")
        if got != API_KEY:
            raise HTTPException(status_code=401, detail="Bad API key")

    payload = await req.json()

    # минимальная валидация
    required = ["chat_id", "message_id", "timestamp", "symbol", "action", "source"]
    for k in required:
        if k not in payload or payload[k] in (None, ""):
            raise HTTPException(status_code=422, detail=f"Missing field: {k}")

    inserted = db.insert_signal(payload)
    # 201 если вставили, 200 если дубль (удобно)
    return {"inserted": inserted}


@app.get("/api/signals")
def list_signals(limit: int = 100, symbol: str | None = None):
    return db.list_signals(limit=limit, symbol=symbol)

# api/signals
# health
