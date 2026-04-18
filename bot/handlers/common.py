"""
Common handlers: /start, language selection, contact sharing.
Flow:
  /start
    → if no BotUser or no language → show language inline keyboard
    → after lang chosen → show phone-share button
    → after phone received → show main menu
    → if already registered → show main menu
"""
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.texts import t
from bot.keyboards.client import lang_selection, main_menu, request_contact

router = Router()


class RegState(StatesGroup):
    lang  = State()   # waiting for language choice
    phone = State()   # waiting for contact


async def _get_or_create_user(tg_user):
    from botapp.models import BotUser
    user, _ = await BotUser.objects.aupdate_or_create(
        user_id=str(tg_user.id),
        defaults={
            'full_name': tg_user.full_name or '',
            'username':  tg_user.username  or '',
        },
    )
    return user


# ─── /start ──────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    bot_user = await _get_or_create_user(message.from_user)
    name = message.from_user.first_name or message.from_user.full_name or "Foydalanuvchi"

    # Already fully registered → show main menu
    if bot_user.phone_number and bot_user.language:
        lang = bot_user.language
        await message.answer(
            t(lang, 'welcome', name=name),
            reply_markup=main_menu(lang),
        )
        return

    # Need language selection first
    await state.set_state(RegState.lang)
    await message.answer(
        t('uz', 'choose_lang'),   # language picker itself in uz/ru/en
        reply_markup=lang_selection(),
    )


# ─── Language selection ───────────────────────────────────────────────────────

@router.callback_query(RegState.lang, F.data.startswith("lang:"))
async def language_chosen(call: CallbackQuery, state: FSMContext):
    lang = call.data.split(":")[1]   # uz / ru / en
    if lang not in ('uz', 'ru', 'en'):
        lang = 'uz'

    bot_user = await _get_or_create_user(call.from_user)
    await bot_user.__class__.objects.filter(
        user_id=str(call.from_user.id)
    ).aupdate(language=lang)

    await call.answer()
    name = call.from_user.first_name or call.from_user.full_name or "Foydalanuvchi"

    # If already has phone, go straight to menu
    if bot_user.phone_number:
        await call.message.edit_text(t(lang, 'welcome', name=name))
        await call.message.answer(
            t(lang, 'welcome', name=name),
            reply_markup=main_menu(lang),
        )
        await state.clear()
        return

    # Ask for phone
    await state.set_state(RegState.phone)
    await call.message.edit_text(t(lang, 'send_phone', name=name))
    await call.message.answer(
        t(lang, 'send_phone', name=name),
        reply_markup=request_contact(lang),
    )


# Language can also be changed from main menu (no FSM state required)
@router.callback_query(F.data.startswith("lang:"))
async def language_change(call: CallbackQuery, state: FSMContext):
    lang = call.data.split(":")[1]
    if lang not in ('uz', 'ru', 'en'):
        lang = 'uz'
    await call.answer()
    from botapp.models import BotUser
    await BotUser.objects.filter(user_id=str(call.from_user.id)).aupdate(language=lang)

    bot_user = await BotUser.objects.filter(user_id=str(call.from_user.id)).afirst()
    name = call.from_user.first_name or call.from_user.full_name or "Foydalanuvchi"

    if bot_user and not bot_user.phone_number:
        await state.set_state(RegState.phone)
        await call.message.edit_text(t(lang, 'send_phone', name=name))
        await call.message.answer(
            t(lang, 'send_phone', name=name),
            reply_markup=request_contact(lang),
        )
    else:
        await call.message.edit_text(t(lang, 'welcome', name=name))
        await call.message.answer(
            t(lang, 'welcome', name=name),
            reply_markup=main_menu(lang),
        )
        await state.clear()


# ─── Contact / Phone sharing ─────────────────────────────────────────────────

@router.message(F.contact)
async def contact_handler(message: Message, state: FSMContext):
    from botapp.models import BotUser

    phone = message.contact.phone_number
    if not phone.startswith('+'):
        phone = '+' + phone

    await BotUser.objects.filter(
        user_id=str(message.from_user.id)
    ).aupdate(phone_number=phone)

    bot_user = await BotUser.objects.filter(
        user_id=str(message.from_user.id)
    ).afirst()
    lang = bot_user.language if bot_user else 'uz'

    await state.clear()
    await message.answer(
        t(lang, 'phone_saved'),
        reply_markup=main_menu(lang),
    )
