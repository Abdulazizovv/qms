from telebot import types
from bot.loader import bot
from botapp.models import BotUser
from bot.keyboards import main_menu

@bot.message_handler(commands=["start"])
def start_handler(message: types.Message):
    user, created = BotUser.objects.update_or_create(
        defaults={
            "full_name": message.from_user.full_name,
            "username": message.from_user.username
        },
        user_id=message.from_user.id
    )

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Telefon raqamni jo'natish📞", request_contact=True)
    markup.add(btn1)

    if not user.phone_number:
        bot.send_message(
            user.user_id,
            "Assalomu alaykum\n"\
            "Ro'yxatdan o'tish uchun pastdagi tugma orqali telefon raqamingizni yuboring👇",
            reply_markup=markup
        )
        return
    
    bot.send_message(
        message.from_user.id,
        "<b>SmartNavbat</b>ga xush kelibsiz🤗\n"\
        "O'zingizga kerakli xizmatni tanlang va qulay navbat oling!",
        reply_markup=main_menu,
        parse_mode="HTML"
    )


@bot.message_handler(content_types=["contact"])
def get_user_phone(message: types.Message):
    phone_number = message.contact.phone_number

    user, created = BotUser.objects.get_or_create(
        defaults={
            "full_name": message.from_user.full_name,
            "username": message.from_user.username
        },
        user_id=message.from_user.id
    )
    if not user.phone_number:
        user.phone_number = phone_number
        user.save()
        bot.send_message(
            message.from_user.id,
            "Ro'yxatdan o'tdingiz! Endi botdan to'liq foydalanishingiz mumkin!\n"\
            "Bosh menyu",
            reply_markup=main_menu,
            parse_mode="HTML"
        )
        return