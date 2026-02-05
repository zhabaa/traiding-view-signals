from __future__ import annotations
import sqlite3
import json
from typing import Any, Dict, Optional, List, Tuple


class SignalsDB:
    def __init__(self, path: str = "signals.db") -> None:
        self.path = path
        self._init()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row

        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init(self) -> None:
        conn = self.connect()
        try:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                source TEXT NOT NULL,
                channel TEXT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                price REAL,
                signal_type TEXT,
                strength INTEGER,
                extra_json TEXT,
                raw_text TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            """)
            conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS ux_signals_chat_msg
            ON signals(chat_id, message_id);
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS ix_signals_ts ON signals(timestamp);")
            conn.execute("CREATE INDEX IF NOT EXISTS ix_signals_symbol ON signals(symbol);")
            conn.execute("CREATE INDEX IF NOT EXISTS ix_signals_source ON signals(source);")
            conn.commit()
        finally:
            conn.close()

    def insert_signal(self, s: Dict[str, Any]) -> bool:
        """
        Возвращает True если вставили, False если дубль (chat_id, message_id уже есть)
        """
        conn = self.connect()
        try:
            extra_json = json.dumps(s.get("extra", {}), ensure_ascii=False)
            raw_text = s.get("raw_text")

            cur = conn.execute("""
                INSERT OR IGNORE INTO signals (
                    chat_id, message_id, source, channel, timestamp,
                    symbol, action, price, signal_type, strength,
                    extra_json, raw_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                int(s["chat_id"]),
                int(s["message_id"]),
                s.get("source", "UNKNOWN"),
                s.get("channel"),
                s.get("timestamp"),
                s.get("symbol"),
                s.get("action"),
                s.get("price"),
                s.get("signal_type"),
                s.get("strength"),
                extra_json,
                raw_text
            ))
            conn.commit()
            return cur.rowcount == 1
        finally:
            conn.close()

    def list_signals(self, limit: int = 100, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self.connect()
        try:
            if symbol:
                rows = conn.execute("""
                    SELECT * FROM signals
                    WHERE symbol = ?
                    ORDER BY id DESC
                    LIMIT ?
                """, (symbol, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM signals
                    ORDER BY id DESC
                    LIMIT ?
                """, (limit,)).fetchall()

            out: List[Dict[str, Any]] = []
            for r in rows:
                d = dict(r)
                # распарсим extra_json обратно в dict
                try:
                    d["extra"] = json.loads(d.get("extra_json") or "{}")
                except:
                    d["extra"] = {}
                out.append(d)
            return out
        finally:
            conn.close()
