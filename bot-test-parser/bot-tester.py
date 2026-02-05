import os
import random
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
import logging

# -------------------- load dotenv ----------------

from dotenv import load_dotenv

load_dotenv()

# ---------- logger -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("BOT_TESTER")


BOT_TOKEN = os.getenv("BOT_TOKEN_TESTER")

if not BOT_TOKEN:
    raise RuntimeError("Set BOT_TOKEN env var")

bot = Bot(BOT_TOKEN, parse_mode=None)
dp = Dispatcher()


def _dt_str() -> str:
    # формат как в Telegram "05.01.2026 17:07" — бот не может менять системный заголовок,
    # но сам текст будет очень похож.
    return datetime.now().strftime("%d.%m.%Y %H:%M")


def msg_tsb_report() -> str:
    bid = random.choice([120, 150, 180, 220])
    growth = random.choice(["10-15%", "8-12%", "12-18%"])
    price = round(random.uniform(84000, 87000), 2)
    report = f"{random.randint(1, 9)}/{random.randint(1, 9)}"
    zone = random.choice(["Отличная зона лонгов по альтмаркету", "Хорошая зона лонгов по альтмаркету"])

    log.info(f"msg_tsb_report")

    return (
        f"Ⓜ️ TSB LONG Report #{report}\n\n"
        f"🟩🟩 {zone}\n\n"
        f"BID строки > {bid}\n\n"
        f"⚠️ Расчетный рост по альтам {growth}\n"
        f"___\n"
        f"#Report #LongReport\n"
        f"___\n\n"
        f"BTC/USDT-SPOT: {price}\n"
    )


def msg_long_combo() -> str:
    strength = random.choice([2, 3, 4])
    horizon = random.choice(["6–12 ч", "12–36 ч", "24+ ч", "2–5 дн"])
    target = random.choice(["1–2.5%", "2–4%", "3–5%", "4–8%"])
    tip = random.choice([
        "⚠️ Сигнал только по тренду",
        "⚠️ Можно рассмотреть в контртренд",
        "",
    ])
    price = round(random.uniform(85000, 87000), 2)
    emoji = "🟢" * strength
    combo_n = strength  # в твоих примерах combo номер совпадал
    typ = random.choice(["Интрадей", "Интрадей+", "Свинг"])

    log.info(f"msg_long_combo")

    return (
        f"{emoji} LONG COMBO {combo_n}\n\n"
        f"Направление: LONG\n"
        f"Тип: {typ}\n\n"
        f"🎯 Горизонт: {horizon} | Цель: {target}\n"
        f"{tip}\n"
        f"___\n\n"
        f"BTC/USDT-SPOT: {price}\n"
    )


def msg_btc_zone() -> str:
    level = random.choice(["2️⃣", "3️⃣", "1️⃣"])
    horizon = random.choice(["12–36 ч", "24+ ч", "6–12 ч"])
    target = random.choice(["3–5%", "4-6%", "1–2.5%"])
    price = round(random.uniform(85000, 86500), 2)
    emoji = "🟢" * random.choice([2, 3])
    direction = "LONG"  # можно расширить SHORT позже

    log.info(f"msg_btc_zone")


    return (
        f"{emoji}\n"
        f"🧠 BTC Signal\n\n"
        f"Стратегия: ZONE\n"
        f"Уровень: {level}\n"
        f"Направление: {direction}\n\n"
        f"🎯 Горизонт: {horizon} | Цель: {target}\n"
        f"___\n"
        f"Цена актива:\n\n"
        f"BTC/USDT-SPOT: {price}\n"
    )


def msg_eth_ai() -> str:
    strategy = "COMBO"
    level = random.choice([1, 3, 4, 5])
    typ = random.choice(["Scalp", "Intraday", "Swing"])
    side = random.choice(["🟢 LONG", "🔴 SHORT"])
    # силы
    strength_main = random.choice([20, 60, 80, 100])
    strength_alt = random.choice([14, 26, 78, 100])
    price = round(random.uniform(2750, 2950), 2)

    trend = random.choice(["LONG (manual)", "LONG (auto)"])
    horizon = random.choice(["1 дн.", "2-3 дн.", "3-7 дн."])

    log.info(f"msg_eth_ai")


    conclusion = random.choice([
        "🚨🚨🚨 SUPER LONG",
        "SUPER LONG",
        "GOOD LONG",
        "⚖️ BALANCE (контртренд)",
        "⚖️ BALANCE",
    ])

    # иконка силы зависит от side
    icon = "🟢" if "LONG" in side else "🔴"

    return (
        f"🧠 ETH AI v2\n\n"
        f"Стратегия: {strategy}\n"
        f"Уровень: {level}\n"
        f"Тип: {typ}\n"
        f"Направление: {side}\n\n"
        f"🔥 Сила сигнала: {icon} {strength_main} / 100\n"
        f"(уверенность ETH AI v2)\n\n"
        f"ETH/USDT-SPOT: {price}\n\n"
        f"База: GLOBAL @ 3 310.00 (∞)\n"
        f"Дивергенция: -{round(random.uniform(10, 16), 2)}%\n\n"
        f"Глобальный тренд: {trend}\n\n"
        f"🎯 Горизонт: {horizon}\n\n"
        f"Окно 6ч: L {random.randint(0, 400)} / S {random.randint(0, 400)} | NET {random.randint(-200, 200)}\n"
        f"Окно 12ч: L {random.randint(0, 400)} / S {random.randint(0, 400)} | NET {random.randint(-200, 200)}\n\n"
        f"Сила: {strength_alt}/100\n\n"
        f"Вывод: {conclusion}\n"
    )


def msg_noise() -> str:
    samples = [
        "Ребят, кто смотрит рынок? 🤔",
        "Не сигнал. Просто мысль: волатильность растёт.",
        "Напоминание: риск-менеджмент важнее всего.",
        "Проверьте новости, может быть импульс.",
        "Лонг/шорт — не уверен, жду подтверждение.",
        "Админ закрепил сообщение.",
    ]
    log.info(f"msg_noise")

    return random.choice(samples)


MSG_FACTORY = {
    "tsb": msg_tsb_report,
    "combo": msg_long_combo,
    "btc_zone": msg_btc_zone,
    "eth_ai": msg_eth_ai,
    "noise": msg_noise,
}


async def send_generated(chat_id: int, kind: str) -> None:
    text = MSG_FACTORY[kind]()
    await bot.send_message(chat_id, text)


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Я тест-бот для генерации сигналов.\n\n"
        "Команды:\n"
        "/send <tsb|combo|btc_zone|eth_ai>\n"
        "/pack <type> <n> <delay_sec>\n"
        "/mix <n> <delay_sec>\n"
        "/noise <n> <delay_sec>\n"
        "/chatid\n\n"
        "Пример: /pack eth_ai 10 1.0"
    )


@dp.message(Command("ping"))
async def ping(m: Message):
    await m.answer("pong ✅")


@dp.message(Command("chatid"))
async def cmd_chatid(message: Message):
    await message.answer(f"chat_id: {message.chat.id}")


@dp.message(Command("send"))
async def cmd_send(message: Message, command: CommandObject):
    if not command.args:
        return await message.answer("Формат: /send <tsb|combo|btc_zone|eth_ai>")
    kind = command.args.strip().lower()

    if kind not in ("tsb", "combo", "btc_zone", "eth_ai"):
        return await message.answer("Неизвестный тип. Доступно: tsb, combo, btc_zone, eth_ai")

    await send_generated(message.chat.id, kind)


@dp.message(Command("pack"))
async def cmd_pack(message: Message, command: CommandObject):
    if not command.args:
        return await message.answer("Формат: /pack <type> <n> <delay_sec>\nНапример: /pack combo 20 0.7")

    parts = command.args.split()
    if len(parts) < 3:
        return await message.answer("Формат: /pack <type> <n> <delay_sec>")

    kind = parts[0].lower()
    if kind not in ("tsb", "combo", "btc_zone", "eth_ai", "noise"):
        return await message.answer("Тип: tsb|combo|btc_zone|eth_ai|noise")

    try:
        n = int(parts[1])
        delay = float(parts[2])
    except ValueError:
        return await message.answer("n должно быть int, delay_sec должно быть float")

    n = max(1, min(n, 200))  # ограничим, чтоб не улететь в бан
    delay = max(0.1, min(delay, 10.0))

    await message.answer(f"Ок, отправляю {n} сообщений типа {kind} с задержкой {delay}s…")

    for _ in range(n):
        await send_generated(message.chat.id, kind)
        await asyncio.sleep(delay)


@dp.message(Command("mix"))
async def cmd_mix(message: Message, command: CommandObject):
    if not command.args:
        return await message.answer("Формат: /mix <n> <delay_sec>\nНапример: /mix 30 0.5")

    parts = command.args.split()

    if len(parts) < 2:
        return await message.answer("Формат: /mix <n> <delay_sec>")

    try:
        n = int(parts[0])
        delay = float(parts[1])

    except ValueError:
        return await message.answer("n должно быть int, delay_sec должно быть float")

    n = max(1, min(n, 300))
    delay = max(0.1, min(delay, 10.0))

    kinds = ["tsb", "combo", "btc_zone", "eth_ai", "noise"]
    await message.answer(f"Ок, отправляю микс {n} сообщений с задержкой {delay}s…")

    for _ in range(n):
        kind = random.choice(kinds)
        await send_generated(message.chat.id, kind)
        await asyncio.sleep(delay)


@dp.message(Command("noise"))
async def cmd_noise(message: Message, command: CommandObject):
    if not command.args:
        return await message.answer("Формат: /noise <n> <delay_sec>\nНапример: /noise 50 0.3")
    parts = command.args.split()
    if len(parts) < 2:
        return await message.answer("Формат: /noise <n> <delay_sec>")

    try:
        n = int(parts[0])
        delay = float(parts[1])
    except ValueError:
        return await message.answer("n должно быть int, delay_sec должно быть float")

    n = max(1, min(n, 500))
    delay = max(0.1, min(delay, 10.0))

    await message.answer(f"Шум: {n} сообщений, delay={delay}s…")

    for _ in range(n):
        await send_generated(message.chat.id, "noise")
        await asyncio.sleep(delay)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
