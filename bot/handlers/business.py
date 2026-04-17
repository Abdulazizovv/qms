from telebot import types
from bot.loader import bot


@bot.callback_query_handler()
def business_handler(call: types.CallbackQuery):
    print("Ishladi")