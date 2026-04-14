from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db import transaction
from business.models import Business, Branch, Service, Operator
from business.forms import BusinessForm, BranchForm, ServiceForm, OperatorCreateForm, OperatorEditForm
from ticket.models import Ticket, Session, SessionStatus, StatusTypes
from user.models import UserTypes
from django.utils import timezone


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
