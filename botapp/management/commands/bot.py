from django.core.management.base import BaseCommand
from bot.loader import bot
from bot import handlers


class Command(BaseCommand):
    help = 'Telegram-bot'

    def handle(self, *args, **options):
        print('Bot ishga tushmoqda...')
        bot.infinity_polling()