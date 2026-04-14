from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from business.models import Business, Service, Branch
from ticket.models import Ticket, SessionStatus, StatusTypes
from django.http import HttpRequest



def overview(request: HttpRequest):
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    active_branches = Branch.objects.filter(is_active=True).count()
    monthly_visitors = Ticket.objects.filter(created_at__gte=month_start).count()
    monthly_revenue = (
        Ticket.objects.filter(
            created_at__gte=month_start,
            status=StatusTypes.DONE,
        ).aggregate(total=Sum("session__service__price"))["total"]
        or 0
    )

    top_branches = (
        Branch.objects.annotate(
            visitors=Count(
                "services__sessions__tickets",
                filter=Q(services__sessions__tickets__created_at__gte=month_start),
                distinct=True,
            ),
            revenue=Sum(
                "services__sessions__tickets__session__service__price",
                filter=Q(services__sessions__tickets__created_at__gte=month_start),
            ),
        )
        .order_by("-visitors")[:5]
    )

    top_services = (
        Service.objects.annotate(
            usage=Count(
                "sessions__tickets",
                filter=Q(sessions__tickets__created_at__gte=month_start),
                distinct=True,
            ),
            revenue=Sum(
                "sessions__tickets__session__service__price",
                filter=Q(sessions__tickets__created_at__gte=month_start),
            ),
        )
        .order_by("-usage")[:6]
    )

    context = {
        "active_branches": active_branches,
        "monthly_visitors": monthly_visitors,
        "monthly_revenue": monthly_revenue,
        "avg_satisfaction": None,
        "top_branches": top_branches,
        "top_services": top_services,
    }

    return render(request, "overview.html", context)


# Create your views here.
def business_detail(request, pk):
    business = get_object_or_404(Business, id=pk)
    services = Service.objects.filter(branch__business=business)
    tickets = Ticket.objects.filter(
        session__service__branch__business=business,
        status=StatusTypes.WAITING,
    )

    if request.method == "POST":
        service_id = request.POST.get("service")
        service = get_object_or_404(Service, id=service_id, branch__business=business)
        session = (
            service.sessions.filter(status__in=[SessionStatus.ACTIVE, SessionStatus.PENDING])
            .order_by("-created_at")
            .first()
        )
        if not session:
            messages.error(request, "Hozircha aktiv sessiya topilmadi.")
        else:
            ticket = Ticket.objects.create(
                session=session,
                customer=request.user if request.user.is_authenticated else None,
            )
            messages.success(request, f"Ticket yaratildi: {ticket.number}")
            return redirect("business_detail", pk=business.id)

    return render(request, "business_detail.html", {
        "business": business,
        "services": services,
        "tickets": tickets
    })
    
    
