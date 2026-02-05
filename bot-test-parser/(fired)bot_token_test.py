import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot

load_dotenv()

async def main():
    token = os.getenv("BOT_TOKEN_TESTER")
    print("BOT_TOKEN_TESTER:", "OK" if token else "NONE")
    if not token:
        return
    bot = Bot(token)
    me = await bot.get_me()
    print("Bot username:", me.username)

if __name__ == "__main__":
    asyncio.run(main())
