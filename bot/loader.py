import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = os.environ.get('TOKEN', '')

bot = Bot(token="8553368129:AAEBEtfmX-MCwYwngB-v6I3rpqAfq7Kv5UM")
dp  = Dispatcher(storage=MemoryStorage())
