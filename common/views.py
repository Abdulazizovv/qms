from django.shortcuts import get_object_or_404, render
from django.utils import timezone


def home(request):
    return render(request, 'advert/base_home.html')


def team_page(request):
    return render(request, 'about/team.html')


def queue_display(request, branch_pk):
    """Large-screen display for a branch's live queue. No authentication required."""
    from business.models import Branch
    from ticket.models import Session, SessionStatus, StatusTypes, Ticket

    branch = get_object_or_404(Branch, pk=branch_pk, is_active=True)
    today  = timezone.now().date()

    sessions = (
        Session.objects
        .filter(service__branch=branch, status=SessionStatus.ACTIVE, date=today)
        .select_related('service', 'operator')
    )

    serving = []
    for s in sessions:
        current = s.get_current_ticket()
        if current:
            serving.append({
                'ticket':  current,
                'service': s.service,
                'desk':    s.operator.desk_number,
            })

    waiting = (
        Ticket.objects
        .filter(service__branch=branch, status=StatusTypes.WAITING)
        .select_related('service')
        .order_by('-is_vip', 'created_at')[:20]
    )

    return render(request, 'display/queue_display.html', {
        'branch':  branch,
        'serving': serving,
        'waiting': waiting,
    })