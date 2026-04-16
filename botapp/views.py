from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, F
from business.models import Business, Branch, Service
from ticket.models import Session, SessionStatus, Ticket
from user.models import UserTypes


def client_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.user_type != UserTypes.CLIENT:
            messages.error(request, "Siz mijoz paneliga kira olmaysiz.")
            if request.user.user_type == UserTypes.OPERATOR:
                return redirect("business:operator_panel")
            return redirect("dashboard:index")
        return view_func(request, *args, **kwargs)
    return wrapper


@client_required
def client_home(request):
    return redirect("client:business_list")


@client_required
def business_list(request):
    businesses = Business.objects.all().order_by("title")
    return render(request, "client/business_list.html", {"businesses": businesses})


@client_required
def branch_list(request, biz_pk):
    business = get_object_or_404(Business, pk=biz_pk)
    branches = Branch.objects.filter(business=business, is_active=True).order_by("title")
    return render(request, "client/branch_list.html", {
        "business": business,
        "branches": branches,
    })


@client_required
def service_list(request, branch_pk):
    branch = get_object_or_404(Branch, pk=branch_pk, is_active=True)
    services = Service.objects.filter(branch=branch, status="active").order_by("title")

    if request.method == "POST":
        service_id = request.POST.get("service_id")
        service = get_object_or_404(Service, pk=service_id, branch=branch)

        active_session = (
            Session.objects.filter(service=service, status=SessionStatus.ACTIVE)
            .select_related("operator")
            .first()
        )
        if not active_session:
            messages.error(request, "Ushbu xizmat hozir faol emas. Boshqa xizmatni tanlang.")
            return redirect("client:service_list", branch_pk=branch.pk)

        ticket = Ticket.objects.create(
            session=active_session,
            customer=request.user,
        )
        messages.success(request, f"Sizning navbatingiz: {ticket.number}")
        return redirect("client:ticket_detail", ticket_pk=ticket.pk)

    return render(request, "client/service_list.html", {
        "branch": branch,
        "business": branch.business,
        "services": services,
    })


@client_required
def ticket_detail(request, ticket_pk):
    ticket = get_object_or_404(Ticket, pk=ticket_pk, customer=request.user)
    return render(request, "client/ticket_detail.html", {
        "ticket": ticket,
        "status_partial_url": "client:ticket_status_partial",
    })


@client_required
def ticket_status_partial(request, ticket_pk):
    ticket = get_object_or_404(Ticket, pk=ticket_pk, customer=request.user)
    waiting_ahead = 0
    if ticket.status == "waiting":
        waiting_ahead = Ticket.objects.filter(
            session=ticket.session,
            status="waiting",
            created_at__lt=ticket.created_at,
        ).count()

    # Calculate estimated wait time
    avg_service_time = Ticket.objects.filter(
        session__service=ticket.session.service,
        status="done"
    ).aggregate(
        avg_time=Avg(F('finished_at') - F('called_at'))
    )['avg_time']
    
    estimated_wait_minutes = waiting_ahead * (avg_service_time.total_seconds() / 60 if avg_service_time else 10)

    return render(request, "client/partials/ticket_status.html", {
        "ticket": ticket,
        "waiting_ahead": waiting_ahead,
        "estimated_wait_minutes": int(estimated_wait_minutes),
    })
