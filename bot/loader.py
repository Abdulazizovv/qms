import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage


def _get_token() -> str:
    """Read bot token from env var, falling back to Django settings."""
    token = os.environ.get('TOKEN', '').strip()
    if not token:
        try:
            from django.conf import settings
            token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '').strip()
        except Exception:
            pass
    return token


bot = Bot(
    token=_get_token(),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher(storage=MemoryStorage())
