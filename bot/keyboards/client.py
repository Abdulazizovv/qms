"""
Keyboard builders for the client bot.
All functions accept an optional `lang` parameter for i18n.
"""
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,
)
from bot.texts import t


def lang_selection() -> InlineKeyboardMarkup:
    """Inline keyboard for language selection (shown before phone request)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbek",  callback_data="lang:uz"),
            InlineKeyboardButton(text="🇷🇺 Русский",  callback_data="lang:ru"),
            InlineKeyboardButton(text="🇬🇧 English",  callback_data="lang:en"),
        ]
    ])


def request_contact(lang: str = 'uz') -> ReplyKeyboardMarkup:
    """Reply keyboard with phone-share button."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang, 'phone_btn'), request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def main_menu(lang: str = 'uz') -> ReplyKeyboardMarkup:
    """Two-button main menu: Bizneslar | Navbatlarim."""
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text=t(lang, 'btn_biz')),
            KeyboardButton(text=t(lang, 'btn_tickets')),
        ]],
        resize_keyboard=True,
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


# ── Inline keyboards ──────────────────────────────────────────────────────────

def business_list(businesses, lang: str = 'uz') -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"🏢 {b.title}", callback_data=f"biz:{b.pk}")]
        for b in businesses
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def branch_list(branches, biz_pk: int, lang: str = 'uz') -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"🏪 {b.title}  ({b.location})", callback_data=f"branch:{b.pk}")]
        for b in branches
    ]
    buttons.append([InlineKeyboardButton(text=t(lang, 'back'), callback_data=f"biz:{biz_pk}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def service_list(services, branch_pk: int, lang: str = 'uz') -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"[{s.ticket_prefix}] {s.title}",
            callback_data=f"svc:{s.pk}"
        )]
        for s in services
    ]
    buttons.append([InlineKeyboardButton(text=t(lang, 'back'), callback_data=f"branch:{branch_pk}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def take_ticket_confirm(service_pk: int, lang: str = 'uz') -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, 'confirm_take'), callback_data=f"take:{service_pk}")],
        [InlineKeyboardButton(text=t(lang, 'cancel'),       callback_data="cancel")],
    ])


def timeslot_list(slots, service_pk: int, lang: str = 'uz') -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"{s.start_time.strftime('%H:%M')}–{s.end_time.strftime('%H:%M')}  ({s.available_count} joy)",
            callback_data=f"slot:{s.pk}"
        )]
        for s in slots if not s.is_full
    ]
    if not buttons:
        buttons = [[InlineKeyboardButton(text="😔 Bo'sh joy yo'q", callback_data="cancel")]]
    buttons.append([InlineKeyboardButton(text=t(lang, 'back'), callback_data=f"svc:{service_pk}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_booking(slot_pk: int, lang: str = 'uz') -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, 'confirm_book'), callback_data=f"book:{slot_pk}")],
        [InlineKeyboardButton(text=t(lang, 'cancel'),       callback_data="cancel")],
    ])
