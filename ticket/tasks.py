"""
Celery async tasks for the ticket app.
All tasks are side-effect only — they don't return values.
"""
from celery import shared_task


# ─── Telegram notifications ───────────────────────────────────────────────────

@shared_task(ignore_result=True)
def send_telegram_message(chat_id: str, text: str):
    """Low-level: send a Telegram message via the bot."""
    from django.conf import settings
    import asyncio
    from aiogram import Bot

    async def _send():
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        try:
            await bot.send_message(chat_id=int(chat_id), text=text, parse_mode='HTML')
        finally:
            await bot.session.close()

    asyncio.run(_send())


@shared_task(ignore_result=True)
def notify_ticket_called(ticket_id: int):
    """Notify client via Telegram when their ticket is called."""
    from ticket.models import Ticket
    from botapp.models import BotUser

    try:
        ticket = Ticket.objects.select_related(
            'customer', 'service__branch'
        ).get(pk=ticket_id)
    except Ticket.DoesNotExist:
        return

    if not ticket.customer:
        return

    bot_user = BotUser.objects.filter(
        phone_number=ticket.customer.phone
    ).first()
    if not bot_user:
        return

    text = (
        f"🔔 <b>Navbatingiz keldi!</b>\n\n"
        f"🎫 Chipta: <code>{ticket.number}</code>\n"
        f"💼 {ticket.service.title}\n"
        f"📍 {ticket.service.branch.title}\n\n"
        f"Iltimos, <b>darhol</b> operatorga yaqinlashing!"
    )
    send_telegram_message.delay(bot_user.user_id, text)


@shared_task(ignore_result=True)
def notify_appointment_confirmed(appointment_id: int):
    """Notify client when their appointment is confirmed."""
    from ticket.models import Appointment
    from botapp.models import BotUser

    try:
        apt = Appointment.objects.select_related(
            'time_slot__service__branch', 'customer'
        ).get(pk=appointment_id)
    except Appointment.DoesNotExist:
        return

    if not apt.customer:
        return

    bot_user = BotUser.objects.filter(phone_number=apt.customer.phone).first()
    if not bot_user:
        return

    slot = apt.time_slot
    text = (
        f"✅ <b>Qabul tasdiqlandi!</b>\n\n"
        f"📅 Sana: {slot.date.strftime('%d.%m.%Y')}\n"
        f"🕐 Vaqt: {slot.start_time.strftime('%H:%M')}–{slot.end_time.strftime('%H:%M')}\n"
        f"💼 {slot.service.title}\n"
        f"📍 {slot.service.branch.title}"
    )
    send_telegram_message.delay(bot_user.user_id, text)


@shared_task(ignore_result=True)
def send_appointment_reminder(appointment_id: int):
    """Send reminder 30 minutes before appointment time."""
    from ticket.models import Appointment, AppointmentStatus
    from botapp.models import BotUser

    try:
        apt = Appointment.objects.select_related(
            'time_slot__service__branch', 'customer'
        ).get(pk=appointment_id)
    except Appointment.DoesNotExist:
        return

    if apt.status not in (AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED):
        return

    if not apt.customer:
        return

    bot_user = BotUser.objects.filter(phone_number=apt.customer.phone).first()
    if not bot_user:
        return

    slot = apt.time_slot
    text = (
        f"⏰ <b>Eslatma!</b>\n\n"
        f"30 daqiqadan so'ng qabulingiz boshlanadi.\n\n"
        f"🕐 Vaqt: {slot.start_time.strftime('%H:%M')}\n"
        f"💼 {slot.service.title}\n"
        f"📍 {slot.service.branch.title}\n\n"
        f"Kechikmaslikka harakat qiling!"
    )
    send_telegram_message.delay(bot_user.user_id, text)
    apt.telegram_notified = True
    apt.save(update_fields=['telegram_notified'])


# ─── Periodic maintenance ─────────────────────────────────────────────────────

@shared_task(ignore_result=True)
def cleanup_old_sessions():
    """Auto-close sessions that weren't closed at end of day."""
    from django.utils import timezone
    from ticket.models import Session, SessionStatus
    from ticket import services

    yesterday = timezone.now().date() - timezone.timedelta(days=1)
    stale = Session.objects.filter(status=SessionStatus.ACTIVE, date__lt=yesterday)
    for session in stale:
        services.close_session(session)


@shared_task(ignore_result=True)
def send_daily_owner_report():
    """Send each owner a daily summary of their queue stats."""
    from django.utils import timezone
    from business.models import Business
    from ticket.models import Ticket, StatusTypes
    from botapp.models import BotUser

    today = timezone.now().date()
    for biz in Business.objects.select_related('owner'):
        if not biz.owner:
            continue
        bot_user = BotUser.objects.filter(phone_number=biz.owner.phone).first()
        if not bot_user:
            continue

        tickets = Ticket.objects.filter(
            service__branch__business=biz,
            created_at__date=today,
        )
        total   = tickets.count()
        done    = tickets.filter(status=StatusTypes.DONE).count()
        skipped = tickets.filter(status=StatusTypes.SKIPPED).count()

        text = (
            f"📊 <b>{biz.title} — Kunlik hisobot</b>\n"
            f"📅 {today.strftime('%d.%m.%Y')}\n\n"
            f"🎫 Jami chiptalar: <b>{total}</b>\n"
            f"✅ Bajarildi: <b>{done}</b>\n"
            f"↷ O'tkazildi: <b>{skipped}</b>\n"
            f"📈 Samaradorlik: <b>"
            + (f"{done*100//total}%" if total else "—") +
            f"</b>"
        )
        send_telegram_message.delay(bot_user.user_id, text)
