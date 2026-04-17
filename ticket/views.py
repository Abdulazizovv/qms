from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from business.models import Operator
from ticket import services
from ticket.models import Session, SessionStatus, StatusTypes, Ticket


# ─── Decorators ───────────────────────────────────────────────────────────────

def operator_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.user_type != 'operator':
            return HttpResponseForbidden("Ruxsat yo'q")
        try:
            request.operator = request.user.operator
        except Operator.DoesNotExist:
            return HttpResponseForbidden("Operator profili topilmadi")
        return view_func(request, *args, **kwargs)
    return wrapper


def _get_active_session(operator):
    return Session.objects.filter(
        operator=operator,
        status=SessionStatus.ACTIVE,
        date=timezone.now().date(),
    ).select_related('service').first()


# ─── Main panel ───────────────────────────────────────────────────────────────

@operator_required
def operator_panel(request):
    operator = request.operator
    session  = _get_active_session(operator)

    current_ticket  = None
    waiting_tickets = []
    waiting_count   = 0
    stats           = {}

    if session:
        current_ticket  = session.get_current_ticket()
        waiting_tickets = (
            Ticket.objects
            .filter(service=session.service, status=StatusTypes.WAITING)
            .order_by('-is_vip', 'created_at')[:20]
        )
        waiting_count = Ticket.objects.filter(
            service=session.service, status=StatusTypes.WAITING
        ).count()
        stats = services.get_queue_stats(session.service)

    available_services = operator.services.filter(status='active')

    return render(request, 'operator/panel.html', {
        'session':          session,
        'current_ticket':   current_ticket,
        'waiting_tickets':  waiting_tickets,
        'waiting_count':    waiting_count,
        'stats':            stats,
        'available_services': available_services,
        'operator':         operator,
    })


# ─── Session management ───────────────────────────────────────────────────────

@operator_required
def session_start(request):
    if request.method != 'POST':
        return redirect('operator:panel')

    operator   = request.operator
    service_id = request.POST.get('service_id')
    service    = get_object_or_404(operator.services, pk=service_id)

    if _get_active_session(operator):
        messages.error(request, "Allaqachon faol sessiya mavjud")
        return redirect('operator:panel')

    Session.objects.create(operator=operator, service=service)
    messages.success(request, f"'{service.title}' uchun sessiya boshlandi")
    return redirect('operator:panel')


@operator_required
def session_close(request, session_id):
    if request.method != 'POST':
        return redirect('operator:panel')

    session = get_object_or_404(Session, pk=session_id, operator=request.operator)
    services.close_session(session)
    messages.success(request, "Ish kuni yakunlandi")
    return redirect('operator:panel')


# ─── Ticket actions ───────────────────────────────────────────────────────────

@operator_required
def ticket_call_next(request, session_id):
    if request.method != 'POST':
        return redirect('operator:panel')

    session = get_object_or_404(
        Session, pk=session_id,
        operator=request.operator,
        status=SessionStatus.ACTIVE,
    )

    if session.get_current_ticket():
        messages.warning(request, "Avval joriy chiptani yakunlang yoki o'tkazing")
        return redirect('operator:panel')

    ticket = services.get_next_ticket(session)
    if ticket:
        messages.success(request, f"Chipta {ticket.number} chaqirildi")
    else:
        messages.info(request, "Navbatda chipta yo'q")

    return redirect('operator:panel')


@operator_required
def ticket_finish(request, ticket_id):
    if request.method != 'POST':
        return redirect('operator:panel')

    ticket = get_object_or_404(
        Ticket, pk=ticket_id,
        session__operator=request.operator,
        status=StatusTypes.PROCESS,
    )
    services.finish_ticket(ticket)
    messages.success(request, f"Chipta {ticket.number} muvaffaqiyatli yakunlandi")
    return redirect('operator:panel')


@operator_required
def ticket_skip(request, ticket_id):
    if request.method != 'POST':
        return redirect('operator:panel')

    ticket = get_object_or_404(
        Ticket, pk=ticket_id,
        session__operator=request.operator,
        status=StatusTypes.PROCESS,
    )
    services.skip_ticket(ticket)
    messages.warning(request, f"Chipta {ticket.number} o'tkazib yuborildi")
    return redirect('operator:panel')


# ─── HTMX fragment ────────────────────────────────────────────────────────────

@operator_required
def queue_fragment(request, session_id):
    """Lightweight endpoint polled by HTMX every 5 s to refresh the queue."""
    session = get_object_or_404(Session, pk=session_id, operator=request.operator)

    current_ticket  = session.get_current_ticket()
    waiting_tickets = (
        Ticket.objects
        .filter(service=session.service, status=StatusTypes.WAITING)
        .order_by('-is_vip', 'created_at')[:20]
    )
    waiting_count = Ticket.objects.filter(
        service=session.service, status=StatusTypes.WAITING
    ).count()

    return render(request, 'operator/queue_fragment.html', {
        'session':         session,
        'current_ticket':  current_ticket,
        'waiting_tickets': waiting_tickets,
        'waiting_count':   waiting_count,
    })
