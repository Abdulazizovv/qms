"""
Queue business logic — all state transitions happen here.
Fires WebSocket notifications (channel layer) and Celery tasks after each change.
"""
from asgiref.sync import async_to_sync
from django.db import transaction
from django.utils import timezone


def _push_queue_update(session):
    """Broadcast queue change to all connected operators for this session."""
    try:
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        if channel_layer is not None:
            async_to_sync(channel_layer.group_send)(
                f'queue_{session.id}',
                {'type': 'queue_update'},
            )
    except Exception:
        pass   # channels not available in some test/dev setups — silent fail


def _push_ticket_update(ticket_number: str):
    """Broadcast ticket status change to the client watching this ticket."""
    try:
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        if channel_layer is not None:
            async_to_sync(channel_layer.group_send)(
                f'ticket_{ticket_number}',
                {'type': 'ticket_status'},
            )
    except Exception:
        pass


# ─── Session management ───────────────────────────────────────────────────────

def close_session(session) -> None:
    """Close session; finish any in-progress ticket first."""
    from ticket.models import SessionStatus, StatusTypes
    current = session.get_current_ticket()
    if current:
        finish_ticket(current)
    session.status    = SessionStatus.CLOSED
    session.closed_at = timezone.now()
    session.save(update_fields=['status', 'closed_at', 'updated_at'])


# ─── Ticket transitions ───────────────────────────────────────────────────────

def get_next_ticket(session):
    """
    Atomically claim the next waiting ticket for this session.
    VIP tickets are always served first.
    Fires WebSocket + Celery notification after claiming.
    """
    from ticket.models import StatusTypes, Ticket
    from ticket.tasks import notify_ticket_called

    with transaction.atomic():
        ticket = (
            Ticket.objects
            .select_for_update()
            .filter(service=session.service, status=StatusTypes.WAITING)
            .order_by('-is_vip', 'created_at')
            .first()
        )
        if not ticket:
            return None

        ticket.session   = session
        ticket.status    = StatusTypes.PROCESS
        ticket.called_at = timezone.now()
        ticket.save(update_fields=['session', 'status', 'called_at', 'updated_at'])

    # Fire notifications outside the transaction
    _push_queue_update(session)
    _push_ticket_update(ticket.number)

    # Celery: send Telegram message to client
    try:
        notify_ticket_called.delay(ticket.id)
    except Exception:
        pass

    return ticket


def finish_ticket(ticket) -> None:
    ticket.status      = StatusTypes.DONE
    ticket.finished_at = timezone.now()
    ticket.save(update_fields=['status', 'finished_at', 'updated_at'])
    _push_ticket_update(ticket.number)
    if ticket.session:
        _push_queue_update(ticket.session)


def skip_ticket(ticket) -> None:
    from ticket.models import StatusTypes
    ticket.status = StatusTypes.SKIPPED
    ticket.save(update_fields=['status', 'updated_at'])
    _push_ticket_update(ticket.number)
    if ticket.session:
        _push_queue_update(ticket.session)


def cancel_ticket(ticket) -> None:
    from ticket.models import StatusTypes
    ticket.status = StatusTypes.CANCEL
    ticket.save(update_fields=['status', 'updated_at'])
    _push_ticket_update(ticket.number)


# ─── Stats ───────────────────────────────────────────────────────────────────

def get_queue_stats(service) -> dict:
    from ticket.models import StatusTypes, Ticket
    qs = Ticket.objects.filter(service=service)
    today = timezone.now().date()
    return {
        'waiting': qs.filter(status=StatusTypes.WAITING).count(),
        'process': qs.filter(status=StatusTypes.PROCESS).count(),
        'done':    qs.filter(status=StatusTypes.DONE,    created_at__date=today).count(),
        'skipped': qs.filter(status=StatusTypes.SKIPPED, created_at__date=today).count(),
    }


# ─── Appointment helpers ──────────────────────────────────────────────────────

def confirm_appointment(appointment) -> None:
    from ticket.models import AppointmentStatus
    from ticket.tasks import notify_appointment_confirmed
    appointment.status = AppointmentStatus.CONFIRMED
    appointment.save(update_fields=['status', 'updated_at'])
    try:
        notify_appointment_confirmed.delay(appointment.id)
    except Exception:
        pass


def cancel_appointment(appointment) -> None:
    from ticket.models import AppointmentStatus
    appointment.status = AppointmentStatus.CANCELLED
    appointment.save(update_fields=['status', 'updated_at'])
