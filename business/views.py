from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db import transaction
from django.db.models import Avg, F
from business.models import Business, Branch, Service, Operator
from business.forms import BusinessForm, BranchForm, ServiceForm, OperatorCreateForm, OperatorEditForm
from ticket.models import Ticket, Session, SessionStatus, StatusTypes
from user.models import UserTypes, MyUser
from django.utils import timezone



from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def owner_required(view_func):
    """Faqat owner tipidagi userlar uchun decorator"""
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.user_type != 'owner':
            return HttpResponseForbidden("Ruxsat yo'q")
        return view_func(request, *args, **kwargs)
    return wrapper


def operator_required(view_func):
    """Faqat operator tipidagi userlar uchun decorator"""
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.user_type != UserTypes.OPERATOR:
            return HttpResponseForbidden("Ruxsat yo'q")
        return view_func(request, *args, **kwargs)
    return wrapper


# ─── Dashboard ────────────────────────────────────────────────────────────────

@owner_required
def dashboard_index(request):
    businesses = Business.objects.filter(owner=request.user)
    branches   = Branch.objects.filter(business__in=businesses)
    operators  = Operator.objects.filter(branch__in=branches)
    today      = timezone.now().date()
    tickets_today = Ticket.objects.filter(session__service__branch__in=branches, created_at__date=today).count()

    ctx = {
        'businesses':    businesses,
        'business_count': businesses.count(),
        'branch_count':  branches.count(),
        'operator_count': operators.count(),
        'tickets_today': tickets_today,
    }
    return render(request, 'dashboard/index.html', ctx)


# ─── Business ─────────────────────────────────────────────────────────────────

@owner_required
def business_list(request):
    businesses = Business.objects.filter(owner=request.user).prefetch_related('branches')
    return render(request, 'dashboard/business_list.html', {'businesses': businesses})


@owner_required
def business_create(request):
    form = BusinessForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        biz = form.save(commit=False)
        biz.owner = request.user
        biz.save()
        messages.success(request, f"'{biz.title}' biznes yaratildi!")
        return redirect('business:detail', pk=biz.pk)
    return render(request, 'dashboard/business_form.html', {'form': form, 'action': 'Yaratish'})


@owner_required
def business_detail(request, pk):
    business = get_object_or_404(Business, pk=pk, owner=request.user)
    branches = business.branches.prefetch_related('services', 'operators')
    operators = Operator.objects.filter(branch__business=business).select_related('user', 'branch')
    return render(request, 'dashboard/business_detail.html', {
        'business': business,
        'branches': branches,
        'operators': operators,
    })


@owner_required
def business_edit(request, pk):
    business = get_object_or_404(Business, pk=pk, owner=request.user)
    form = BusinessForm(request.POST or None, request.FILES or None, instance=business)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Biznes ma'lumotlari yangilandi!")
        return redirect('business:detail', pk=pk)
    return render(request, 'dashboard/business_form.html', {'form': form, 'action': 'Tahrirlash', 'business': business})


@owner_required
def business_analytics(request, pk):
    business = get_object_or_404(Business, pk=pk, owner=request.user)
    branches = Branch.objects.filter(business=business)
    
    # Get date range from request or default to last 30 days
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    if not from_date or not to_date:
        to_date = timezone.now().date()
        from_date = to_date - timezone.timedelta(days=30)
    else:
        from_date = timezone.datetime.strptime(from_date, '%Y-%m-%d').date()
        to_date = timezone.datetime.strptime(to_date, '%Y-%m-%d').date()
    
    # Statistics calculations
    total_tickets = Ticket.objects.filter(
        session__service__branch__in=branches,
        created_at__date__range=[from_date, to_date]
    ).count()
    
    completed_tickets = Ticket.objects.filter(
        session__service__branch__in=branches,
        status=StatusTypes.DONE,
        created_at__date__range=[from_date, to_date]
    ).count()
    
    avg_wait_time = Ticket.objects.filter(
        session__service__branch__in=branches,
        status=StatusTypes.DONE,
        created_at__date__range=[from_date, to_date]
    ).exclude(
        called_at__isnull=True
    ).aggregate(
        avg_wait=Avg(F('called_at') - F('created_at'))
    )['avg_wait']
    
    avg_service_time = Ticket.objects.filter(
        session__service__branch__in=branches,
        status=StatusTypes.DONE,
        created_at__date__range=[from_date, to_date]
    ).exclude(
        finished_at__isnull=True
    ).aggregate(
        avg_service=Avg(F('finished_at') - F('called_at'))
    )['avg_service']
    
    # Daily statistics
    daily_stats = []
    current_date = from_date
    while current_date <= to_date:
        day_tickets = Ticket.objects.filter(
            session__service__branch__in=branches,
            created_at__date=current_date
        ).count()
        
        day_completed = Ticket.objects.filter(
            session__service__branch__in=branches,
            status=StatusTypes.DONE,
            created_at__date=current_date
        ).count()
        
        daily_stats.append({
            'date': current_date,
            'total': day_tickets,
            'completed': day_completed,
            'completion_rate': (day_completed / day_tickets * 100) if day_tickets > 0 else 0
        })
        current_date += timezone.timedelta(days=1)
    
    # Service performance
    service_stats = []
    for branch in branches:
        services = Service.objects.filter(branch=branch)
        for service in services:
            svc_tickets = Ticket.objects.filter(
                session__service=service,
                created_at__date__range=[from_date, to_date]
            ).count()
            
            svc_completed = Ticket.objects.filter(
                session__service=service,
                status=StatusTypes.DONE,
                created_at__date__range=[from_date, to_date]
            ).count()
            
            service_stats.append({
                'service': service,
                'branch': branch,
                'total': svc_tickets,
                'completed': svc_completed,
                'completion_rate': (svc_completed / svc_tickets * 100) if svc_tickets > 0 else 0
            })
    
    context = {
        'business': business,
        'from_date': from_date,
        'to_date': to_date,
        'total_tickets': total_tickets,
        'completed_tickets': completed_tickets,
        'completion_rate': (completed_tickets / total_tickets * 100) if total_tickets > 0 else 0,
        'avg_wait_time': avg_wait_time,
        'avg_service_time': avg_service_time,
        'daily_stats': daily_stats,
        'service_stats': service_stats,
    }
    
    return render(request, 'dashboard/analytics.html', context)


@owner_required
def business_delete(request, pk):
    business = get_object_or_404(Business, pk=pk, owner=request.user)
    if request.method == 'POST':
        title = business.title
        business.delete()
        messages.success(request, f"'{title}' o'chirildi")
        return redirect('business:list')
    return render(request, 'dashboard/confirm_delete.html', {'obj': business, 'type': 'biznes'})


# ─── Branch ───────────────────────────────────────────────────────────────────

@owner_required
def branch_create(request, biz_pk):
    business = get_object_or_404(Business, pk=biz_pk, owner=request.user)
    form = BranchForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        branch = form.save(commit=False)
        branch.business = business
        branch.save()
        messages.success(request, f"'{branch.title}' filiali yaratildi!")
        return redirect('business:detail', pk=biz_pk)
    return render(request, 'dashboard/branch_form.html', {'form': form, 'business': business, 'action': 'Yaratish'})


@owner_required
def branch_edit(request, biz_pk, pk):
    business = get_object_or_404(Business, pk=biz_pk, owner=request.user)
    branch   = get_object_or_404(Branch, pk=pk, business=business)
    form = BranchForm(request.POST or None, instance=branch)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Filial yangilandi!")
        return redirect('business:detail', pk=biz_pk)
    return render(request, 'dashboard/branch_form.html', {'form': form, 'business': business, 'action': 'Tahrirlash', 'branch': branch})


@owner_required
def branch_delete(request, biz_pk, pk):
    business = get_object_or_404(Business, pk=biz_pk, owner=request.user)
    branch   = get_object_or_404(Branch, pk=pk, business=business)
    if request.method == 'POST':
        branch.delete()
        messages.success(request, "Filial o'chirildi")
        return redirect('business:detail', pk=biz_pk)
    return render(request, 'dashboard/confirm_delete.html', {'obj': branch, 'type': 'filial', 'business': business})


# ─── Service ──────────────────────────────────────────────────────────────────

@owner_required
def service_create(request, biz_pk, branch_pk):
    business = get_object_or_404(Business, pk=biz_pk, owner=request.user)
    branch   = get_object_or_404(Branch, pk=branch_pk, business=business)
    form = ServiceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        service = form.save(commit=False)
        service.branch = branch
        service.save()
        messages.success(request, f"'{service.title}' xizmati yaratildi!")
        return redirect('business:detail', pk=biz_pk)
    return render(request, 'dashboard/service_form.html', {'form': form, 'business': business, 'branch': branch, 'action': 'Yaratish'})


@owner_required
def service_edit(request, biz_pk, pk):
    business = get_object_or_404(Business, pk=biz_pk, owner=request.user)
    service  = get_object_or_404(Service, pk=pk, branch__business=business)
    form = ServiceForm(request.POST or None, instance=service)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Xizmat yangilandi!")
        return redirect('business:detail', pk=biz_pk)
    return render(request, 'dashboard/service_form.html', {'form': form, 'business': business, 'branch': service.branch, 'action': 'Tahrirlash', 'service': service})


@owner_required
def service_delete(request, biz_pk, pk):
    business = get_object_or_404(Business, pk=biz_pk, owner=request.user)
    service  = get_object_or_404(Service, pk=pk, branch__business=business)
    if request.method == 'POST':
        service.delete()
        messages.success(request, "Xizmat o'chirildi")
        return redirect('business:detail', pk=biz_pk)
    return render(request, 'dashboard/confirm_delete.html', {'obj': service, 'type': 'xizmat', 'business': business})


# ─── Operator ─────────────────────────────────────────────────────────────────

@owner_required
def operator_list(request, biz_pk):
    business  = get_object_or_404(Business, pk=biz_pk, owner=request.user)
    operators = Operator.objects.filter(branch__business=business).select_related('user', 'branch')
    return render(request, 'dashboard/operator_list.html', {'business': business, 'operators': operators})


@owner_required
def operator_create(request, biz_pk):
    business = get_object_or_404(Business, pk=biz_pk, owner=request.user)
    form = OperatorCreateForm(request.POST or None, business=business)
    if request.method == 'POST' and form.is_valid():
        op = form.save(business=business)
        messages.success(request, f"Operator '{op.user.first_name}' qo'shildi!")
        return redirect('business:detail', pk=biz_pk)
    return render(request, 'dashboard/operator_form.html', {'form': form, 'business': business, 'action': 'Qo\'shish'})


@owner_required
def operator_edit(request, biz_pk, pk):
    business = get_object_or_404(Business, pk=biz_pk, owner=request.user)
    operator = get_object_or_404(Operator, pk=pk, branch__business=business)
    form = OperatorEditForm(request.POST or None, instance=operator, business=business)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Operator ma'lumotlari yangilandi!")
        return redirect('business:detail', pk=biz_pk)
    return render(request, 'dashboard/operator_form.html', {'form': form, 'business': business, 'operator': operator, 'action': 'Tahrirlash'})


@owner_required
def operator_delete(request, biz_pk, pk):
    business = get_object_or_404(Business, pk=biz_pk, owner=request.user)
    operator = get_object_or_404(Operator, pk=pk, branch__business=business)
    if request.method == 'POST':
        user = operator.user
        operator.delete()
        user.delete()
        messages.success(request, "Operator o'chirildi")
        return redirect('business:detail', pk=biz_pk)
    return render(request, 'dashboard/confirm_delete.html', {'obj': operator, 'type': 'operator', 'business': business})


@operator_required
def operator_settings(request):
    operator = get_object_or_404(Operator, user=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action', 'profile')
        
        if action == 'profile':
            # Profil ma'lumotlarini o'zgartirish
            first_name = request.POST.get('first_name', '').strip()
            desk_number = request.POST.get('desk_number', '').strip()
            
            if not first_name:
                messages.error(request, "Ism bo'sh bo'lishi mumkin emas")
            else:
                operator.user.first_name = first_name
                if desk_number:
                    operator.desk_number = desk_number
                
                operator.user.save()
                operator.save()
                messages.success(request, "✓ Profil ma'lumotlari muvaffaqiyatli yangilandi!")
                return redirect('business:operator_settings')
        
        elif action == 'password':
            # Parolni o'zgartirish
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            if not current_password:
                messages.error(request, "Hozirgi parolni kiriting")
            elif not operator.user.check_password(current_password):
                messages.error(request, "Hozirgi parol noto'g'ri")
            elif not new_password:
                messages.error(request, "Yangi parol bo'sh bo'lishi mumkin emas")
            elif len(new_password) < 6:
                messages.error(request, "Parol kamida 6 ta belgidan iborat bo'lishi kerak")
            elif new_password != confirm_password:
                messages.error(request, "Parollar mos kelmadi")
            elif new_password == current_password:
                messages.error(request, "Yangi parol eski parol bilan bir xil bo'lishi mumkin emas")
            else:
                operator.user.set_password(new_password)
                operator.user.save()
                messages.success(request, "✓ Parol muvaffaqiyatli o'zgartirildi!")
                # Foydalanuvchini qayta login qilishga majbur etish
                return redirect('auth:login')
    
    return render(request, 'operator/settings.html', {'operator': operator})


@operator_required
def operator_panel(request):
    operator = get_object_or_404(Operator, user=request.user)
    is_htmx = request.headers.get("HX-Request") == "true"

    def _get_services():
        assigned = operator.services.all()
        return assigned if assigned.exists() else Service.objects.filter(branch=operator.branch)

    def _get_active_session():
        return (
            Session.objects.filter(
                operator=operator,
                status__in=[SessionStatus.ACTIVE, SessionStatus.PAUSED, SessionStatus.PENDING],
            )
            .select_related("service")
            .order_by("-created_at")
            .first()
        )

    def _start_session(active_session, service, now, target_day):
        if active_session:
            if active_session.service_id != service.id:
                messages.warning(
                    request,
                    "Sizda aktiv sessiya bor. Avval shu sessiyani tugating yoki davom ettiring.",
                )
            else:
                if active_session.status == SessionStatus.PENDING:
                    active_session.status = SessionStatus.ACTIVE
                    active_session.started_at = active_session.started_at or now
                    active_session.save(update_fields=["status", "started_at"])
                messages.info(request, "Mavjud sessiya davom ettirildi.")
            return active_session

        existing_today = Session.objects.filter(operator=operator, date=target_day).first()
        if existing_today:
            if existing_today.service_id != service.id:
                messages.warning(
                    request,
                    "Bugun boshqa xizmat bo'yicha sessiya mavjud. Yangi sessiya yaratib bo'lmaydi.",
                )
                return None
            existing_today.status = SessionStatus.ACTIVE
            existing_today.started_at = existing_today.started_at or now
            existing_today.closed_at = None
            existing_today.save(update_fields=["status", "started_at", "closed_at"])
            messages.success(request, "Sessiya qayta faollashtirildi.")
            return existing_today

        new_session = Session.objects.create(
            operator=operator,
            service=service,
            status=SessionStatus.ACTIVE,
            started_at=now,
        )
        messages.success(request, "Yangi sessiya yaratildi.")
        return new_session

    def _resume_session(active_session, now):
        active_session.status = SessionStatus.ACTIVE
        active_session.started_at = active_session.started_at or now
        active_session.save(update_fields=["status", "started_at"])
        messages.success(request, "Sessiya davom ettirildi.")

    def _pause_session(active_session):
        active_session.status = SessionStatus.PAUSED
        active_session.save(update_fields=["status"])
        messages.info(request, "Sessiya tanaffusga qo'yildi.")

    def _close_session(active_session, now):
        active_session.status = SessionStatus.CLOSED
        active_session.closed_at = now
        active_session.current_ticket = None
        active_session.save(update_fields=["status", "closed_at", "current_ticket"])
        messages.success(request, "Sessiya yopildi.")

    def _next_ticket(active_session, now):
        if active_session.current_ticket and active_session.current_ticket.status == StatusTypes.PROCESS:
            messages.warning(request, "Avval joriy ticketni yakunlang.")
            return

        next_ticket = (
            active_session.tickets.filter(status=StatusTypes.WAITING)
            .order_by("-is_vip", "created_at")
            .first()
        )
        if not next_ticket:
            messages.info(request, "Kutilayotgan ticketlar yo'q.")
            return

        with transaction.atomic():
            next_ticket.status = StatusTypes.PROCESS
            next_ticket.called_at = now
            next_ticket.save(update_fields=["status", "called_at"])
            active_session.current_ticket = next_ticket
            active_session.status = SessionStatus.ACTIVE
            active_session.save(update_fields=["current_ticket", "status"])
        messages.success(request, f"Ticket chaqirildi: {next_ticket.number}")

    def _finish_ticket(active_session, action, now):
        current = active_session.current_ticket
        if not current:
            messages.warning(request, "Joriy ticket topilmadi.")
            return

        with transaction.atomic():
            if action == "done_ticket":
                current.status = StatusTypes.DONE
                msg = "Ticket yakunlandi."
            elif action == "skip_ticket":
                current.status = StatusTypes.SKIPPED
                msg = "Ticket o'tkazib yuborildi."
            else:
                current.status = StatusTypes.CANCEL
                msg = "Ticket bekor qilindi."
            current.finished_at = now
            current.save(update_fields=["status", "finished_at"])
            active_session.current_ticket = None
            active_session.save(update_fields=["current_ticket"])
        messages.success(request, msg)

    services = _get_services()
    today = timezone.now().date()
    active_session = _get_active_session()

    def _build_context():
        waiting_tickets = []
        processing_ticket = None
        done_tickets = []
        if active_session:
            waiting_tickets = active_session.tickets.filter(status=StatusTypes.WAITING).order_by(
                "-is_vip", "created_at"
            )
            processing_ticket = active_session.current_ticket
            done_tickets = active_session.tickets.filter(status=StatusTypes.DONE).order_by("-finished_at")[:5]
        return {
            "operator": operator,
            "services": services,
            "active_session": active_session,
            "waiting_tickets": waiting_tickets,
            "processing_ticket": processing_ticket,
            "done_tickets": done_tickets,
        }

    if request.method == "POST":
        action = request.POST.get("action")
        now = timezone.now()

        if action == "start_session":
            service_id = request.POST.get("service_id")
            service = get_object_or_404(Service, id=service_id)
            if service not in services:
                messages.error(request, "Bu xizmat sizga biriktirilmagan.")
            else:
                active_session = _start_session(active_session, service, now, today)

        elif action == "resume_session" and active_session:
            _resume_session(active_session, now)

        elif action == "pause_session" and active_session:
            _pause_session(active_session)

        elif action == "close_session" and active_session:
            _close_session(active_session, now)
            active_session = None

        elif action == "next_ticket" and active_session:
            _next_ticket(active_session, now)

        elif action in {"done_ticket", "skip_ticket", "cancel_ticket"} and active_session:
            _finish_ticket(active_session, action, now)

        if is_htmx:
            return render(request, "operator/partials/panel_content.html", _build_context())
        return redirect("business:operator_panel")
    if is_htmx:
        return render(request, "operator/partials/panel_content.html", _build_context())

    return render(request, "operator/panel.html", _build_context())
