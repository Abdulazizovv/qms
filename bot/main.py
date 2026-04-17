"""
Entry point for the Telegram bot process.
Run as:  python -m bot.main
Or via Docker service 'bot'.

Sets up Django ORM before starting aiogram polling.
"""
import asyncio
import os
import sys

# Make sure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from bot.loader import bot, dp
from bot.handlers import common, client   # registers all routers


async def main():
    dp.include_router(common.router)
    dp.include_router(client.router)

    print("Bot started (polling mode)...")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    asyncio.run(main())
