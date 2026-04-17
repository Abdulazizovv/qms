from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


main_menu = InlineKeyboardMarkup()

btn1 = InlineKeyboardButton(text="Bizneslar🏢", callback_data="businesses")
btn2 = InlineKeyboardButton(text="Navbatlarim🎟", callback_data="tickets")
btn3 = InlineKeyboardButton(text="Profil👤", callback_data="profile")

main_menu.add(btn1, btn2)
main_menu.add(btn3)