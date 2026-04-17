from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,
)


def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏢 Bizneslar"),       KeyboardButton(text="🎫 Chiptalarim")],
            [KeyboardButton(text="📅 Qabullarim"),      KeyboardButton(text="👤 Profil")],
        ],
        resize_keyboard=True,
    )


def request_contact():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def remove_keyboard():
    return ReplyKeyboardRemove()


def business_list(businesses):
    buttons = [
        [InlineKeyboardButton(text=f"🏢 {b.title}", callback_data=f"biz:{b.pk}")]
        for b in businesses
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def branch_list(branches, biz_pk):
    buttons = [
        [InlineKeyboardButton(
            text=f"🏪 {b.title}  ({b.location})",
            callback_data=f"branch:{b.pk}"
        )]
        for b in branches
    ]
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"biz:{biz_pk}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def service_list(services, branch_pk):
    buttons = [
        [InlineKeyboardButton(
            text=f"[{s.ticket_prefix}] {s.title}",
            callback_data=f"svc:{s.pk}"
        )]
        for s in services
    ]
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"branch:{branch_pk}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def take_ticket_confirm(service_pk):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha, navbat olish",  callback_data=f"take:{service_pk}")],
        [InlineKeyboardButton(text="❌ Bekor qilish",      callback_data="cancel")],
    ])


def timeslot_list(slots, service_pk):
    buttons = [
        [InlineKeyboardButton(
            text=f"{s.start_time.strftime('%H:%M')}–{s.end_time.strftime('%H:%M')}  ({s.available_count} joy)",
            callback_data=f"slot:{s.pk}"
        )]
        for s in slots if not s.is_full
    ]
    if not buttons:
        buttons = [[InlineKeyboardButton(text="😔 Bo'sh joy yo'q", callback_data="cancel")]]
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"svc:{service_pk}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_booking(slot_pk):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Yozilish",     callback_data=f"book:{slot_pk}")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")],
    ])
