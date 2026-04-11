from telebot import TeleBot
from environs import Env

env = Env()
env.read_env()

TOKEN = env.str('TOKEN', None)

if not TOKEN:
    raise Exception('Token sozlanmagan')

bot = TeleBot(token=TOKEN)