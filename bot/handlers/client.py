"""
Client-facing handlers:
  - Browse businesses → branches → services
  - Take a real-time ticket
  - Book an appointment time slot
  - View active tickets (text format)
"""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.keyboards import client as kb
from bot.texts import t

router = Router()


async def _get_lang(tg_id: int) -> str:
    """Return user's language preference, defaulting to 'uz'."""
    from botapp.models import BotUser
    bu = await BotUser.objects.filter(user_id=str(tg_id)).afirst()
    return bu.language if bu else 'uz'


async def _require_user(tg_id: int):
    """
    Returns (bot_user, web_user).
    bot_user is None if BotUser doesn't exist or has no phone.
    web_user is None if no MyUser with that phone.
    """
    from botapp.models import BotUser
    from user.models import MyUser

    bu = await BotUser.objects.filter(user_id=str(tg_id)).afirst()
    if not bu or not bu.phone_number:
        return bu, None

    web = await MyUser.objects.filter(phone=bu.phone_number).afirst()
    return bu, web


# ─── Main menu: Bizneslar ─────────────────────────────────────────────────────

@router.message(F.text.in_({
    "Bizneslar 🏢", "Бизнесы 🏢", "Businesses 🏢"
}))
async def menu_businesses(message: Message):
    from business.models import Business
    lang = await _get_lang(message.from_user.id)
    businesses = [b async for b in Business.objects.filter(
        branches__is_active=True
    ).distinct().order_by('title')]
    if not businesses:
        await message.answer(t(lang, 'no_businesses'))
        return
    await message.answer(t(lang, 'choose_biz'), reply_markup=kb.business_list(businesses, lang))


# ─── Main menu: Navbatlarim ───────────────────────────────────────────────────

@router.message(F.text.in_({
    "Navbatlarim 📋", "Мои талоны 📋", "My Tickets 📋"
}))
async def menu_my_tickets(message: Message):
    from ticket.models import StatusTypes, Ticket
    lang = await _get_lang(message.from_user.id)

    bu, web_user = await _require_user(message.from_user.id)
    if not bu or not bu.phone_number:
        await message.answer("/start buyrug'ini yuboring.")
        return
    if not web_user:
        await message.answer(t(lang, 'need_register'))
        return

    tickets = [
        tk async for tk in Ticket.objects
        .filter(customer=web_user, status__in=[StatusTypes.WAITING, StatusTypes.PROCESS])
        .select_related('service__branch')
        .order_by('-created_at')[:10]
    ]

    if not tickets:
        await message.answer(t(lang, 'no_tickets'))
        return

    lines = [t(lang, 'tickets_hdr')]
    for tk in tickets:
        pos_text = ''
        if tk.status == StatusTypes.WAITING:
            pos = tk.queue_position()
            pos_text = t(lang, 'ticket_pos', n=pos + 1)
        lines.append(t(lang, 'ticket_row',
                       num=tk.number,
                       svc=tk.service.title,
                       branch=tk.service.branch.title,
                       status=tk.get_status_display(),
                       pos=pos_text))

    await message.answer("".join(lines))


# ─── Navigation: business → branches ─────────────────────────────────────────

@router.callback_query(F.data.startswith("biz:"))
async def show_branches(call: CallbackQuery):
    lang = await _get_lang(call.from_user.id)
    biz_pk = int(call.data.split(":")[1])
    from business.models import Branch
    branches = [b async for b in Branch.objects.filter(
        business_id=biz_pk, is_active=True
    ).order_by('title')]
    if not branches:
        await call.answer(t(lang, 'no_branches'), show_alert=True)
        return
    await call.message.edit_text(
        t(lang, 'choose_branch'),
        reply_markup=kb.branch_list(branches, biz_pk, lang),
    )


# ─── Navigation: branch → services ───────────────────────────────────────────

@router.callback_query(F.data.startswith("branch:"))
async def show_services(call: CallbackQuery):
    lang = await _get_lang(call.from_user.id)
    branch_pk = int(call.data.split(":")[1])
    from business.models import Service
    services = [s async for s in Service.objects.filter(
        branch_id=branch_pk, status='active'
    ).order_by('title')]
    if not services:
        await call.answer(t(lang, 'no_services'), show_alert=True)
        return
    await call.message.edit_text(
        t(lang, 'choose_svc'),
        reply_markup=kb.service_list(services, branch_pk, lang),
    )


# ─── Service detail ───────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("svc:"))
async def show_service_options(call: CallbackQuery):
    lang = await _get_lang(call.from_user.id)
    svc_pk = int(call.data.split(":")[1])
    from business.models import Service, QueueType
    from ticket.models import StatusTypes, Ticket

    svc = await Service.objects.select_related('branch').aget(pk=svc_pk)
    waiting = await Ticket.objects.filter(service=svc, status=StatusTypes.WAITING).acount()
    price_str = f"{svc.price:,} so'm" if svc.price else t(lang, 'price_free')

    text = t(lang, 'svc_info',
             title=svc.title,
             branch=svc.branch.title,
             time=svc.estimated_time_minutes,
             price=price_str,
             waiting=waiting)

    if svc.queue_type in (QueueType.REALTIME, QueueType.BOTH):
        await call.message.edit_text(text, reply_markup=kb.take_ticket_confirm(svc_pk, lang))
    elif svc.queue_type == QueueType.APPOINTMENT:
        from django.utils import timezone
        from business.models import TimeSlot
        today = timezone.now().date()
        slots = [s async for s in TimeSlot.objects.filter(
            service=svc, date__gte=today, is_active=True
        ).order_by('date', 'start_time')[:10]]
        await call.message.edit_text(
            text,
            reply_markup=kb.timeslot_list(slots, svc_pk, lang),
        )
    else:
        await call.message.edit_text(text)


# ─── Take ticket ──────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("take:"))
async def take_ticket(call: CallbackQuery):
    lang = await _get_lang(call.from_user.id)
    svc_pk = int(call.data.split(":")[1])

    bu, web_user = await _require_user(call.from_user.id)
    if not bu or not bu.phone_number:
        await call.answer(t(lang, 'need_phone'), show_alert=True)
        return
    if not web_user:
        await call.answer(t(lang, 'need_register'), show_alert=True)
        return

    from business.models import Service
    from ticket.models import Ticket, StatusTypes
    from django.utils import timezone

    svc = await Service.objects.select_related('branch').aget(pk=svc_pk)
    today = timezone.now().date()

    existing = await Ticket.objects.filter(
        customer=web_user, service=svc,
        status__in=[StatusTypes.WAITING, StatusTypes.PROCESS],
        created_at__date=today,
    ).afirst()

    if existing:
        pos = existing.queue_position()
        await call.message.edit_text(
            t(lang, 'already_ticket', num=existing.number, pos=pos + 1)
        )
        return

    ticket = await Ticket.objects.acreate(service=svc, customer=web_user)
    pos = ticket.queue_position()
    await call.message.edit_text(
        t(lang, 'ticket_taken',
          num=ticket.number,
          svc=svc.title,
          branch=svc.branch.title,
          pos=pos + 1,
          wait=ticket.estimated_wait_minutes())
    )
    await call.answer()


# ─── Book appointment slot ────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("slot:"))
async def show_slot_confirm(call: CallbackQuery):
    lang = await _get_lang(call.from_user.id)
    slot_pk = int(call.data.split(":")[1])
    from business.models import TimeSlot
    slot = await TimeSlot.objects.select_related('service__branch').aget(pk=slot_pk)
    await call.message.edit_text(
        f"<b>Qabulni tasdiqlang</b>\n\n"
        f"📅 {slot.date.strftime('%d.%m.%Y')}\n"
        f"🕐 {slot.start_time.strftime('%H:%M')}–{slot.end_time.strftime('%H:%M')}\n"
        f"💼 {slot.service.title}\n"
        f"📍 {slot.service.branch.title}",
        reply_markup=kb.confirm_booking(slot_pk, lang),
    )


@router.callback_query(F.data.startswith("book:"))
async def book_slot(call: CallbackQuery):
    lang = await _get_lang(call.from_user.id)
    slot_pk = int(call.data.split(":")[1])

    bu, web_user = await _require_user(call.from_user.id)
    if not bu or not bu.phone_number:
        await call.answer(t(lang, 'need_phone'), show_alert=True)
        return
    if not web_user:
        await call.answer(t(lang, 'need_register'), show_alert=True)
        return

    from business.models import TimeSlot
    from ticket.models import Appointment, AppointmentStatus

    slot = await TimeSlot.objects.select_related('service__branch').aget(pk=slot_pk)
    if slot.is_full:
        await call.answer("Kechirasiz, bu vaqt band bo'ldi.", show_alert=True)
        return

    existing = await Appointment.objects.filter(time_slot=slot, customer=web_user).afirst()
    if existing:
        await call.answer("Siz bu vaqtga allaqachon yozilgansiz.", show_alert=True)
        return

    await Appointment.objects.acreate(
        time_slot=slot, customer=web_user,
        status=AppointmentStatus.CONFIRMED,
    )
    await call.message.edit_text(
        f"✅ <b>Qabul muvaffaqiyatli yozildi!</b>\n\n"
        f"📅 {slot.date.strftime('%d.%m.%Y')}\n"
        f"🕐 {slot.start_time.strftime('%H:%M')}–{slot.end_time.strftime('%H:%M')}\n"
        f"💼 {slot.service.title}\n📍 {slot.service.branch.title}"
    )
    await call.answer()


# ─── Cancel / back ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "cancel")
async def cancel_action(call: CallbackQuery):
    lang = await _get_lang(call.from_user.id)
    await call.message.edit_text(t(lang, 'cancelled'))
    await call.answer()
