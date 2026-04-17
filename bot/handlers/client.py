"""
Client-facing handlers:
  - Browse businesses / branches / services
  - Take a real-time ticket
  - Book an appointment time slot
  - Check ticket / appointment status
"""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.keyboards import client as kb

router = Router()


# ─── Menu shortcuts ───────────────────────────────────────────────────────────

@router.message(F.text == "🏢 Bizneslar")
async def menu_businesses(message: Message):
    from business.models import Business
    businesses = [b async for b in Business.objects.filter(branches__is_active=True).distinct()]
    if not businesses:
        await message.answer("Hozircha bizneslar yo'q.")
        return
    await message.answer("Biznesni tanlang:", reply_markup=kb.business_list(businesses))


@router.message(F.text == "🎫 Chiptalarim")
async def menu_my_tickets(message: Message):
    from botapp.models import BotUser
    from ticket.models import StatusTypes, Ticket

    bot_user = await BotUser.objects.filter(
        user_id=str(message.from_user.id)
    ).afirst()
    if not bot_user or not bot_user.phone_number:
        await message.answer("Iltimos avval /start buyrug'ini yuboring.")
        return

    from user.models import MyUser
    user = await MyUser.objects.filter(phone=bot_user.phone_number).afirst()
    if not user:
        await message.answer("Siz hali ro'yxatdan o'tmagansiz. Veb-saytda ro'yxatdan o'ting.")
        return

    tickets = [
        t async for t in Ticket.objects
        .filter(customer=user, status__in=[StatusTypes.WAITING, StatusTypes.PROCESS])
        .select_related('service__branch')
        .order_by('-created_at')[:5]
    ]
    if not tickets:
        await message.answer("Sizda hozircha faol chipta yo'q.")
        return

    lines = []
    for t in tickets:
        pos = t.queue_position() if t.status == StatusTypes.WAITING else 0
        lines.append(
            f"🎫 <code>{t.number}</code> — {t.service.title}\n"
            f"   Holat: <b>{t.get_status_display()}</b>"
            + (f" | Navbat: {pos}" if pos else "")
        )
    await message.answer("\n\n".join(lines))


@router.message(F.text == "📅 Qabullarim")
async def menu_my_appointments(message: Message):
    from botapp.models import BotUser
    from django.utils import timezone

    bot_user = await BotUser.objects.filter(user_id=str(message.from_user.id)).afirst()
    if not bot_user or not bot_user.phone_number:
        await message.answer("Iltimos avval /start buyrug'ini yuboring.")
        return

    from user.models import MyUser
    from ticket.models import Appointment, AppointmentStatus

    user = await MyUser.objects.filter(phone=bot_user.phone_number).afirst()
    if not user:
        await message.answer("Siz hali ro'yxatdan o'tmagansiz.")
        return

    today = timezone.now().date()
    appointments = [
        a async for a in Appointment.objects
        .filter(customer=user, time_slot__date__gte=today,
                status__in=[AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
        .select_related('time_slot__service__branch')
        .order_by('time_slot__date', 'time_slot__start_time')[:5]
    ]
    if not appointments:
        await message.answer("Sizda kelgusi qabullar yo'q.")
        return

    lines = []
    for a in appointments:
        slot = a.time_slot
        lines.append(
            f"📅 {slot.date.strftime('%d.%m.%Y')} "
            f"{slot.start_time.strftime('%H:%M')}–{slot.end_time.strftime('%H:%M')}\n"
            f"   {slot.service.title} — {slot.service.branch.title}\n"
            f"   Holat: <b>{a.get_status_display()}</b>"
        )
    await message.answer("\n\n".join(lines))


@router.message(F.text == "👤 Profil")
async def menu_profile(message: Message):
    from botapp.models import BotUser
    bot_user = await BotUser.objects.filter(user_id=str(message.from_user.id)).afirst()
    phone = bot_user.phone_number if bot_user else "—"
    await message.answer(
        f"👤 <b>Profil</b>\n\n"
        f"Ism: {message.from_user.full_name}\n"
        f"Telefon: {phone}\n"
        f"Telegram: @{message.from_user.username or '—'}"
    )


# ─── Business / Branch / Service navigation ────────────────────────────────────

@router.callback_query(F.data.startswith("biz:"))
async def show_branches(call: CallbackQuery):
    biz_pk = int(call.data.split(":")[1])
    from business.models import Branch
    branches = [b async for b in Branch.objects.filter(business_id=biz_pk, is_active=True)]
    if not branches:
        await call.answer("Bu biznesda faol filiallar yo'q", show_alert=True)
        return
    await call.message.edit_text(
        "Filialni tanlang:",
        reply_markup=kb.branch_list(branches, biz_pk),
    )


@router.callback_query(F.data.startswith("branch:"))
async def show_services(call: CallbackQuery):
    branch_pk = int(call.data.split(":")[1])
    from business.models import Service
    services = [s async for s in Service.objects.filter(branch_id=branch_pk, status='active')]
    if not services:
        await call.answer("Bu filialda faol xizmatlar yo'q", show_alert=True)
        return
    await call.message.edit_text(
        "Xizmatni tanlang:",
        reply_markup=kb.service_list(services, branch_pk),
    )


@router.callback_query(F.data.startswith("svc:"))
async def show_service_options(call: CallbackQuery):
    svc_pk = int(call.data.split(":")[1])
    from business.models import Service, QueueType
    from ticket.models import StatusTypes, Ticket

    svc = await Service.objects.select_related('branch').aget(pk=svc_pk)
    waiting = await Ticket.objects.filter(service=svc, status=StatusTypes.WAITING).acount()

    text = (
        f"<b>{svc.title}</b>\n"
        f"📍 {svc.branch.title}\n"
        f"⏱ ~{svc.estimated_time_minutes} daqiqa\n"
        f"🎫 Navbatda: {waiting} kishi"
    )

    if svc.queue_type in (QueueType.REALTIME, QueueType.BOTH):
        await call.message.edit_text(text, reply_markup=kb.take_ticket_confirm(svc_pk))
    elif svc.queue_type == QueueType.APPOINTMENT:
        from django.utils import timezone
        today = timezone.now().date()
        from business.models import TimeSlot
        slots = [s async for s in TimeSlot.objects.filter(
            service=svc, date__gte=today, is_active=True
        ).order_by('date', 'start_time')[:10]]
        await call.message.edit_text(
            text + "\n\nVaqt tanlang:",
            reply_markup=kb.timeslot_list(slots, svc_pk),
        )


# ─── Take ticket (real-time) ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("take:"))
async def take_ticket(call: CallbackQuery):
    svc_pk = int(call.data.split(":")[1])
    from botapp.models import BotUser
    from user.models import MyUser
    from business.models import Service
    from ticket.models import Ticket, StatusTypes
    from django.utils import timezone

    bot_user = await BotUser.objects.filter(user_id=str(call.from_user.id)).afirst()
    if not bot_user or not bot_user.phone_number:
        await call.answer("Avval telefon raqamingizni yuboring (/start).", show_alert=True)
        return

    user = await MyUser.objects.filter(phone=bot_user.phone_number).afirst()
    if not user:
        await call.answer("Veb-saytda ro'yxatdan o'tish talab etiladi.", show_alert=True)
        return

    svc = await Service.objects.aget(pk=svc_pk)
    today = timezone.now().date()

    existing = await Ticket.objects.filter(
        customer=user, service=svc,
        status__in=[StatusTypes.WAITING, StatusTypes.PROCESS],
        created_at__date=today,
    ).afirst()

    if existing:
        pos = existing.queue_position()
        await call.message.edit_text(
            f"Sizda allaqachon <code>{existing.number}</code> raqamli chipta bor.\n"
            f"Navbatingiz: {pos}-o'rin"
        )
        return

    ticket = await Ticket.objects.acreate(service=svc, customer=user)
    pos    = ticket.queue_position()
    await call.message.edit_text(
        f"✅ <b>Chipta olindi!</b>\n\n"
        f"🎫 Raqam: <code>{ticket.number}</code>\n"
        f"💼 {svc.title}\n"
        f"📍 {svc.branch.title}\n"
        f"👥 Navbatingiz: <b>{pos + 1}</b>-o'rin\n"
        f"⏱ Taxminiy kutish: <b>~{ticket.estimated_wait_minutes()} daq</b>"
    )
    await call.answer("Chipta muvaffaqiyatli olindi! ✅")


# ─── Book appointment ─────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("slot:"))
async def show_slot_confirm(call: CallbackQuery):
    slot_pk = int(call.data.split(":")[1])
    from business.models import TimeSlot
    slot = await TimeSlot.objects.select_related('service__branch').aget(pk=slot_pk)
    await call.message.edit_text(
        f"<b>Qabulni tasdiqlang</b>\n\n"
        f"📅 {slot.date.strftime('%d.%m.%Y')}\n"
        f"🕐 {slot.start_time.strftime('%H:%M')}–{slot.end_time.strftime('%H:%M')}\n"
        f"💼 {slot.service.title}\n"
        f"📍 {slot.service.branch.title}",
        reply_markup=kb.confirm_booking(slot_pk),
    )


@router.callback_query(F.data.startswith("book:"))
async def book_slot(call: CallbackQuery):
    slot_pk = int(call.data.split(":")[1])
    from botapp.models import BotUser
    from user.models import MyUser
    from business.models import TimeSlot
    from ticket.models import Appointment, AppointmentStatus
    from ticket.services import confirm_appointment

    bot_user = await BotUser.objects.filter(user_id=str(call.from_user.id)).afirst()
    if not bot_user or not bot_user.phone_number:
        await call.answer("Avval telefon raqamingizni yuboring.", show_alert=True)
        return

    user = await MyUser.objects.filter(phone=bot_user.phone_number).afirst()
    if not user:
        await call.answer("Veb-saytda ro'yxatdan o'ting.", show_alert=True)
        return

    slot = await TimeSlot.objects.select_related('service__branch').aget(pk=slot_pk)

    if slot.is_full:
        await call.answer("Kechirasiz, bu vaqt band bo'ldi.", show_alert=True)
        return

    existing = await Appointment.objects.filter(
        time_slot=slot, customer=user
    ).afirst()
    if existing:
        await call.answer("Siz bu vaqtga allaqachon yozilgansiz.", show_alert=True)
        return

    apt = await Appointment.objects.acreate(
        time_slot=slot, customer=user,
        status=AppointmentStatus.CONFIRMED,
    )

    await call.message.edit_text(
        f"✅ <b>Qabul muvaffaqiyatli yozildi!</b>\n\n"
        f"📅 {slot.date.strftime('%d.%m.%Y')}\n"
        f"🕐 {slot.start_time.strftime('%H:%M')}–{slot.end_time.strftime('%H:%M')}\n"
        f"💼 {slot.service.title}\n"
        f"📍 {slot.service.branch.title}\n\n"
        f"Qabuldan 30 daqiqa oldin eslatma yuboriladi."
    )
    await call.answer("Yozilindi! ✅")


@router.callback_query(F.data == "cancel")
async def cancel_action(call: CallbackQuery):
    await call.message.edit_text("Bekor qilindi.")
    await call.answer()
