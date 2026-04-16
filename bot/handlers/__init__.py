from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from bot.loader import bot
from business.models import Business, Branch, Service
from ticket.models import Ticket, Session, SessionStatus
from user.models import MyUser, UserTypes
from django.utils import timezone


def create_main_keyboard():
    """Asosiy keyboard yaratish"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🏢 Bizneslar"))
    keyboard.add(KeyboardButton("🎫 Mening ticketlarim"))
    keyboard.add(KeyboardButton("ℹ️ Yordam"))
    return keyboard


def create_businesses_keyboard(businesses):
    """Bizneslar uchun keyboard"""
    keyboard = InlineKeyboardMarkup()
    for business in businesses:
        keyboard.add(InlineKeyboardButton(
            business.title,
            callback_data=f"business_{business.id}"
        ))
    return keyboard


def create_branches_keyboard(branches):
    """Filiallar uchun keyboard"""
    keyboard = InlineKeyboardMarkup()
    for branch in branches:
        keyboard.add(InlineKeyboardButton(
            branch.title,
            callback_data=f"branch_{branch.id}"
        ))
    return keyboard


def create_services_keyboard(services):
    """Xizmatlar uchun keyboard"""
    keyboard = InlineKeyboardMarkup()
    for service in services:
        keyboard.add(InlineKeyboardButton(
            f"{service.title} ({service.estimated_time_minutes} daq)",
            callback_data=f"service_{service.id}"
        ))
    return keyboard


@bot.message_handler(commands=['start'])
def start_handler(message):
    """Botni ishga tushirish"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # Check if user exists in our system
    try:
        user = MyUser.objects.get(phone=f"tg_{user_id}")
        bot.send_message(
            message.chat.id,
            f"Salom, {user.first_name}! QueuePro botiga xush kelibsiz.",
            reply_markup=create_main_keyboard()
        )
    except MyUser.DoesNotExist:
        # Create new user
        user = MyUser.objects.create_user(
            phone=f"tg_{user_id}",
            password=MyUser.objects.make_random_password(),
            first_name=username,
            user_type=UserTypes.CLIENT
        )
        bot.send_message(
            message.chat.id,
            f"Salom, {username}! QueuePro botiga xush kelibsiz.\n"
            "Siz avtomatik ravishda ro'yxatdan o'tdingiz.",
            reply_markup=create_main_keyboard()
        )


@bot.message_handler(func=lambda message: message.text == "🏢 Bizneslar")
def businesses_handler(message):
    """Bizneslar ro'yxatini ko'rsatish"""
    businesses = Business.objects.all()[:10]  # Limit to 10 for performance
    
    if not businesses:
        bot.send_message(message.chat.id, "Hozircha bizneslar mavjud emas.")
        return
    
    text = "Qaysi biznes uchun navbat olishni xohlaysiz?"
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=create_businesses_keyboard(businesses)
    )


@bot.message_handler(func=lambda message: message.text == "🎫 Mening ticketlarim")
def my_tickets_handler(message):
    """Foydalanuvchi ticketlarini ko'rsatish"""
    user_id = message.from_user.id
    try:
        user = MyUser.objects.get(phone=f"tg_{user_id}")
        tickets = Ticket.objects.filter(customer=user).order_by('-created_at')[:5]
        
        if not tickets:
            bot.send_message(message.chat.id, "Sizda hali ticketlar yo'q.")
            return
        
        text = "Sizning ticketlaringiz:\n\n"
        for ticket in tickets:
            status_emoji = {
                'waiting': '⏳',
                'process': '🔄',
                'done': '✅',
                'cancel': '❌',
                'skipped': '⏭️'
            }.get(ticket.status, '❓')
            
            text += f"{status_emoji} {ticket.number} - {ticket.session.service.title}\n"
            text += f"   Holat: {ticket.get_status_display()}\n"
            if ticket.status == 'waiting':
                waiting_ahead = Ticket.objects.filter(
                    session=ticket.session,
                    status='waiting',
                    created_at__lt=ticket.created_at
                ).count()
                text += f"   Oldinda: {waiting_ahead} kishi\n"
            text += "\n"
        
        bot.send_message(message.chat.id, text)
        
    except MyUser.DoesNotExist:
        bot.send_message(message.chat.id, "Siz ro'yxatdan o'tmagansiz.")


@bot.message_handler(func=lambda message: message.text == "ℹ️ Yordam")
def help_handler(message):
    """Yordam xabari"""
    text = """
🤖 QueuePro Telegram Bot

Bu bot orqali siz:
• Bizneslar va ularning filiallarini ko'rishingiz
• Kerakli xizmat uchun navbat olishingiz  
• O'z ticketlaringiz holatini kuzatishingiz mumkin

📋 Buyruqlar:
/start - Botni qayta ishga tushirish

Agar savollaringiz bo'lsa, admin bilan bog'laning.
"""
    bot.send_message(message.chat.id, text)


@bot.callback_query_handler(func=lambda call: call.data.startswith('business_'))
def business_callback_handler(call):
    """Biznes tanlanganda"""
    business_id = call.data.split('_')[1]
    try:
        business = Business.objects.get(id=business_id)
        branches = Branch.objects.filter(business=business, is_active=True)
        
        if not branches:
            bot.answer_callback_query(call.id, "Bu biznesda faol filiallar yo'q.")
            return
        
        text = f"🏢 {business.title}\n\nQaysi filialni tanlaysiz?"
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_branches_keyboard(branches)
        )
        
    except Business.DoesNotExist:
        bot.answer_callback_query(call.id, "Biznes topilmadi.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('branch_'))
def branch_callback_handler(call):
    """Filial tanlanganda"""
    branch_id = call.data.split('_')[1]
    try:
        branch = Branch.objects.get(id=branch_id, is_active=True)
        services = Service.objects.filter(branch=branch, status='active')
        
        if not services:
            bot.answer_callback_query(call.id, "Bu filialda faol xizmatlar yo'q.")
            return
        
        text = f"🏢 {branch.business.title} - {branch.title}\n\nQaysi xizmat kerak?"
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_services_keyboard(services)
        )
        
    except Branch.DoesNotExist:
        bot.answer_callback_query(call.id, "Filial topilmadi.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('service_'))
def service_callback_handler(call):
    """Xizmat tanlanganda"""
    service_id = call.data.split('_')[1]
    user_id = call.from_user.id
    
    try:
        service = Service.objects.get(id=service_id, status='active')
        user = MyUser.objects.get(phone=f"tg_{user_id}")
        
        # Find active session for this service
        active_session = Session.objects.filter(
            service=service,
            status=SessionStatus.ACTIVE
        ).first()
        
        if not active_session:
            bot.answer_callback_query(
                call.id, 
                "Bu xizmat hozir faol emas. Keyinroq urinib ko'ring."
            )
            return
        
        # Create ticket
        ticket = Ticket.objects.create(
            session=active_session,
            customer=user
        )
        
        text = f"""
🎫 Ticket yaratildi!

📋 Raqam: {ticket.number}
🏢 Biznes: {service.branch.business.title}
🏪 Filial: {service.branch.title}
🛍️ Xizmat: {service.title}

Sizning navbatingizni operator chaqirguncha kuting.
Holatingizni tekshirish uchun "Mening ticketlarim" tugmasini bosing.
"""
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id
        )
        
        bot.answer_callback_query(call.id, f"Ticket #{ticket.number} yaratildi!")
        
    except Service.DoesNotExist:
        bot.answer_callback_query(call.id, "Xizmat topilmadi.")
    except MyUser.DoesNotExist:
        bot.answer_callback_query(call.id, "Foydalanuvchi topilmadi.")
    except Exception as e:
        bot.answer_callback_query(call.id, "Xatolik yuz berdi. Qayta urinib ko'ring.")
