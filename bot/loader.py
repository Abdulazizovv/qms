import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = os.environ.get('TOKEN', '')

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp  = Dispatcher(storage=MemoryStorage())
