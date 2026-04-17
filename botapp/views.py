from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from business.models import Branch, Business, Service, TimeSlot
from ticket.models import Appointment, AppointmentStatus, Feedback, StatusTypes, Ticket


# ─── Client: Business / Branch listing ────────────────────────────────────────

def client_home(request):
    businesses = (
        Business.objects
        .prefetch_related('branches')
        .order_by('title')
    )
    return render(request, 'client/home.html', {'businesses': businesses})


def branch_detail(request, branch_pk):
    branch   = get_object_or_404(Branch, pk=branch_pk, is_active=True)
    services = branch.services.filter(status='active')

    services_with_count = [
        {
            'service':       svc,
            'waiting_count': Ticket.objects.filter(
                service=svc, status=StatusTypes.WAITING
            ).count(),
        }
        for svc in services
    ]

    return render(request, 'client/branch_detail.html', {
        'branch':              branch,
        'services_with_count': services_with_count,
    })


# ─── Client: Take a ticket ────────────────────────────────────────────────────

@login_required
def ticket_take(request, branch_pk, service_pk):
    if request.method != 'POST':
        return redirect('client:branch_detail', branch_pk=branch_pk)

    branch  = get_object_or_404(Branch,  pk=branch_pk,  is_active=True)
    service = get_object_or_404(Service, pk=service_pk, branch=branch, status='active')

    # Prevent duplicate tickets for the same service today
    existing = Ticket.objects.filter(
        customer=request.user,
        service=service,
        status__in=[StatusTypes.WAITING, StatusTypes.PROCESS],
        created_at__date=timezone.now().date(),
    ).first()

    if existing:
        messages.warning(
            request,
            f"Sizda allaqachon {existing.number} raqamli faol chipta bor",
        )
        return redirect('client:my_ticket', number=existing.number)

    ticket = Ticket.objects.create(service=service, customer=request.user)
    request.session['last_ticket'] = ticket.number   # remember for nav
    messages.success(request, f"Chipta {ticket.number} muvaffaqiyatli olindi!")
    return redirect('client:my_ticket', number=ticket.number)


# ─── Client: Track ticket status ──────────────────────────────────────────────

def my_ticket(request, number):
    ticket    = get_object_or_404(Ticket, number=number)
    position  = 0
    wait_mins = 0

    if ticket.status == StatusTypes.WAITING:
        position  = ticket.queue_position()
        wait_mins = ticket.estimated_wait_minutes()

    has_feedback = hasattr(ticket, 'feedback')

    return render(request, 'client/my_ticket.html', {
        'ticket':       ticket,
        'position':     position,
        'wait_mins':    wait_mins,
        'has_feedback': has_feedback,
        'is_waiting':   ticket.status == StatusTypes.WAITING,
        'is_process':   ticket.status == StatusTypes.PROCESS,
        'is_done':      ticket.status == StatusTypes.DONE,
    })


# ─── Client: Feedback ─────────────────────────────────────────────────────────

@login_required
def ticket_feedback(request, ticket_id):
    if request.method != 'POST':
        return redirect('client:home')

    ticket = get_object_or_404(
        Ticket, pk=ticket_id,
        customer=request.user,
        status=StatusTypes.DONE,
    )

    if hasattr(ticket, 'feedback'):
        messages.info(request, "Siz allaqachon fikr bildirgan edingiz")
        return redirect('client:my_ticket', number=ticket.number)

    try:
        rating = int(request.POST.get('rating', 0))
    except (TypeError, ValueError):
        rating = 0

    if not 1 <= rating <= 5:
        messages.error(request, "Iltimos, 1–5 orasida baho bering")
        return redirect('client:my_ticket', number=ticket.number)

    comment = request.POST.get('comment', '').strip()
    Feedback.objects.create(ticket=ticket, rating=rating, comment=comment)
    messages.success(request, "Fikr-mulohazangiz uchun rahmat!")
    return redirect('client:my_ticket', number=ticket.number)


# ─── Client: Appointment / Time-slot booking ──────────────────────────────────

def service_slots(request, service_pk):
    """Show available time slots for a service."""
    service = get_object_or_404(Service, pk=service_pk, status='active')
    today   = timezone.now().date()
    slots   = (
        TimeSlot.objects
        .filter(service=service, date__gte=today, is_active=True)
        .order_by('date', 'start_time')
    )
    return render(request, 'client/service_slots.html', {
        'service': service,
        'slots':   slots,
    })


@login_required
def appointment_book(request, service_pk, slot_pk):
    """Book a specific time slot (POST only)."""
    if request.method != 'POST':
        return redirect('client:service_slots', service_pk=service_pk)

    service = get_object_or_404(Service, pk=service_pk, status='active')
    slot    = get_object_or_404(TimeSlot, pk=slot_pk, service=service, is_active=True)
    today   = timezone.now().date()

    if slot.date < today:
        messages.error(request, "Bu vaqt o'tib ketgan.")
        return redirect('client:service_slots', service_pk=service_pk)

    if slot.is_full:
        messages.error(request, "Kechirasiz, bu vaqt to'lgan.")
        return redirect('client:service_slots', service_pk=service_pk)

    existing = Appointment.objects.filter(
        time_slot=slot, customer=request.user
    ).first()
    if existing:
        messages.info(request, "Siz bu vaqtga allaqachon yozilgansiz.")
        return redirect('client:my_appointments')

    apt = Appointment.objects.create(
        time_slot=slot,
        customer=request.user,
        status=AppointmentStatus.CONFIRMED,
    )
    messages.success(request, f"Qabul {slot.date.strftime('%d.%m.%Y')} {slot.start_time.strftime('%H:%M')} ga muvaffaqiyatli yozildi!")
    return redirect('client:my_appointments')


@login_required
def my_appointments(request):
    """List current user's upcoming appointments."""
    today = timezone.now().date()
    appointments = (
        Appointment.objects
        .filter(
            customer=request.user,
            time_slot__date__gte=today,
            status__in=[AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED],
        )
        .select_related('time_slot__service__branch')
        .order_by('time_slot__date', 'time_slot__start_time')
    )
    return render(request, 'client/my_appointments.html', {
        'appointments': appointments,
    })


@login_required
def appointment_cancel(request, apt_pk):
    """Cancel an appointment (POST only)."""
    if request.method != 'POST':
        return redirect('client:my_appointments')

    apt = get_object_or_404(
        Appointment,
        pk=apt_pk,
        customer=request.user,
        status__in=[AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED],
    )
    apt.status = AppointmentStatus.CANCELLED
    apt.save(update_fields=['status'])
    messages.success(request, "Qabul bekor qilindi.")
    return redirect('client:my_appointments')
