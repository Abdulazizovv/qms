"""
Common handlers: /start, contact sharing, /help
"""
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.keyboards.client import main_menu, request_contact

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):
    import django
    django.setup()              # ensure Django ORM is ready
    from botapp.models import BotUser

    user, _ = await BotUser.objects.aupdate_or_create(
        user_id=str(message.from_user.id),
        defaults={
            'full_name': message.from_user.full_name,
            'username':  message.from_user.username or '',
        },
    )

    if not user.phone_number:
        await message.answer(
            f"Salom, <b>{message.from_user.first_name}</b>! 👋\n\n"
            "QueuePro botiga xush kelibsiz.\n"
            "Davom etish uchun telefon raqamingizni yuboring:",
            reply_markup=request_contact(),
        )
    else:
        await message.answer(
            f"Xush kelibsiz, <b>{message.from_user.first_name}</b>! 👋\n\n"
            "Quyidagi menyudan foydalaning:",
            reply_markup=main_menu(),
        )


@router.message(F.contact)
async def contact_handler(message: Message):
    from botapp.models import BotUser

    phone = message.contact.phone_number
    if not phone.startswith('+'):
        phone = '+' + phone

    await BotUser.objects.filter(
        user_id=str(message.from_user.id)
    ).aupdate(phone_number=phone)

    await message.answer(
        "✅ Telefon raqam saqlandi!\n\n"
        "Endi barcha xizmatlardan foydalanishingiz mumkin.",
        reply_markup=main_menu(),
    )
