from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Count, Avg, Max, Q
from business.models import Business, Branch, Service, Operator
from business.forms import BusinessForm, BranchForm, ServiceForm, OperatorCreateForm, OperatorEditForm
from ticket.models import Session, SessionStatus, Ticket, StatusTypes, Feedback
from django.utils import timezone


def owner_required(view_func):
    """Faqat owner tipidagi userlar uchun decorator"""
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.user_type != 'owner':
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
    tickets_today   = Ticket.objects.filter(service__branch__in=branches, created_at__date=today).count()
    active_sessions = Session.objects.filter(
        service__branch__in=branches, status=SessionStatus.ACTIVE, date=today
    ).count()

    ctx = {
        'businesses':     businesses,
        'business_count': businesses.count(),
        'branch_count':   branches.count(),
        'operator_count': operators.count(),
        'tickets_today':  tickets_today,
        'active_sessions': active_sessions,
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


# ─── Time Slots (appointment mode) ────────────────────────────────────────────

@owner_required
def timeslot_list(request, biz_pk, service_pk):
    business = get_object_or_404(Business, pk=biz_pk, owner=request.user)
    service  = get_object_or_404(Service, pk=service_pk, branch__business=business)
    today    = timezone.now().date()
    slots    = service.time_slots.filter(date__gte=today).order_by('date', 'start_time')
    return render(request, 'dashboard/timeslot_list.html', {
        'business': business, 'service': service, 'slots': slots,
    })


@owner_required
def timeslot_create(request, biz_pk, service_pk):
    from business.forms import TimeSlotForm
    business = get_object_or_404(Business, pk=biz_pk, owner=request.user)
    service  = get_object_or_404(Service, pk=service_pk, branch__business=business)

    form = TimeSlotForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        slot = form.save(commit=False)
        slot.service = service
        slot.save()
        messages.success(request, "Vaqt sloti qo'shildi!")
        return redirect('business:timeslot_list', biz_pk=biz_pk, service_pk=service_pk)
    return render(request, 'dashboard/timeslot_form.html', {
        'form': form, 'business': business, 'service': service, 'action': 'Yaratish',
    })


@owner_required
def timeslot_delete(request, biz_pk, service_pk, pk):
    business = get_object_or_404(Business, pk=biz_pk, owner=request.user)
    service  = get_object_or_404(Service, pk=service_pk, branch__business=business)
    slot     = get_object_or_404(service.time_slots, pk=pk)
    if request.method == 'POST':
        slot.delete()
        messages.success(request, "Vaqt sloti o'chirildi")
        return redirect('business:timeslot_list', biz_pk=biz_pk, service_pk=service_pk)
    return render(request, 'dashboard/confirm_delete.html', {
        'obj': slot, 'type': 'vaqt sloti', 'business': business,
    })


# ─── Sessions analytics ────────────────────────────────────────────────────────

@owner_required
def sessions_analytics(request):
    businesses = Business.objects.filter(owner=request.user)
    branches   = Branch.objects.filter(business__in=businesses)

    sessions_qs = Session.objects.filter(
        service__branch__in=branches
    ).select_related(
        'operator__user', 'service', 'service__branch', 'service__branch__business'
    ).annotate(
        total_tickets=Count('tickets'),
        done_tickets=Count('tickets', filter=Q(tickets__status=StatusTypes.DONE)),
    )

    biz_pk     = request.GET.get('business')
    branch_pk  = request.GET.get('branch')
    date_from  = request.GET.get('date_from')
    date_to    = request.GET.get('date_to')
    status_f   = request.GET.get('status')
    order      = request.GET.get('order', '-date')

    if biz_pk:
        sessions_qs = sessions_qs.filter(service__branch__business__pk=biz_pk)
    if branch_pk:
        sessions_qs = sessions_qs.filter(service__branch__pk=branch_pk)
    if date_from:
        sessions_qs = sessions_qs.filter(date__gte=date_from)
    if date_to:
        sessions_qs = sessions_qs.filter(date__lte=date_to)
    if status_f:
        sessions_qs = sessions_qs.filter(status=status_f)

    allowed_orders = {'date', '-date', 'total_tickets', '-total_tickets', 'done_tickets', '-done_tickets'}
    if order not in allowed_orders:
        order = '-date'
    sessions_qs = sessions_qs.order_by(order)

    today = timezone.now().date()
    active_count = sessions_qs.filter(status=SessionStatus.ACTIVE, date=today).count()
    total_tickets_sum = sessions_qs.aggregate(s=Count('tickets'))['s'] or 0

    return render(request, 'dashboard/sessions.html', {
        'sessions':          sessions_qs,
        'businesses':        businesses,
        'branches':          branches,
        'active_count':      active_count,
        'total_tickets_sum': total_tickets_sum,
        'total_sessions':    sessions_qs.count(),
        'filters': {
            'business': biz_pk, 'branch': branch_pk,
            'date_from': date_from, 'date_to': date_to,
            'status': status_f, 'order': order,
        },
    })


# ─── Customers list ────────────────────────────────────────────────────────────

@owner_required
def customers_list(request):
    businesses = Business.objects.filter(owner=request.user)
    branches   = Branch.objects.filter(business__in=businesses)

    search   = request.GET.get('q', '').strip()
    biz_pk   = request.GET.get('business')
    order    = request.GET.get('order', '-last_visit')

    tickets_qs = Ticket.objects.filter(
        service__branch__in=branches, customer__isnull=False
    )
    if biz_pk:
        tickets_qs = tickets_qs.filter(service__branch__business__pk=biz_pk)

    customers = tickets_qs.values(
        'customer__id', 'customer__first_name', 'customer__phone'
    ).annotate(
        ticket_count=Count('id'),
        last_visit=Max('created_at'),
        done_count=Count('id', filter=Q(status=StatusTypes.DONE)),
    )

    if search:
        customers = customers.filter(
            Q(customer__first_name__icontains=search) |
            Q(customer__phone__icontains=search)
        )

    allowed_orders = {'-last_visit', 'last_visit', '-ticket_count', 'ticket_count'}
    if order not in allowed_orders:
        order = '-last_visit'
    customers = customers.order_by(order)

    return render(request, 'dashboard/customers.html', {
        'customers':   customers,
        'businesses':  businesses,
        'total':       customers.count(),
        'search':      search,
        'filters': {'business': biz_pk, 'order': order, 'q': search},
    })


# ─── Feedbacks list ────────────────────────────────────────────────────────────

@owner_required
def feedbacks_list(request):
    businesses = Business.objects.filter(owner=request.user)
    branches   = Branch.objects.filter(business__in=businesses)

    biz_pk = request.GET.get('business')
    rating = request.GET.get('rating')
    order  = request.GET.get('order', '-created_at')

    feedbacks_qs = Feedback.objects.filter(
        ticket__service__branch__in=branches
    ).select_related(
        'ticket', 'ticket__customer', 'ticket__service', 'ticket__service__branch'
    )

    if biz_pk:
        feedbacks_qs = feedbacks_qs.filter(ticket__service__branch__business__pk=biz_pk)
    if rating:
        feedbacks_qs = feedbacks_qs.filter(rating=rating)

    allowed_orders = {'-created_at', 'created_at', '-rating', 'rating'}
    if order not in allowed_orders:
        order = '-created_at'
    feedbacks_qs = feedbacks_qs.order_by(order)

    avg_rating   = feedbacks_qs.aggregate(avg=Avg('rating'))['avg'] or 0
    rating_dist  = list(feedbacks_qs.values('rating').annotate(count=Count('id')).order_by('rating'))

    return render(request, 'dashboard/feedbacks.html', {
        'feedbacks':   feedbacks_qs,
        'businesses':  businesses,
        'avg_rating':  round(avg_rating, 1),
        'total':       feedbacks_qs.count(),
        'rating_dist': rating_dist,
        'filters': {'business': biz_pk, 'rating': rating, 'order': order},
    })


@owner_required
def display_select(request):
    """Let the owner choose which branch to show on the big screen."""
    businesses = Business.objects.filter(owner=request.user).prefetch_related('branches')
    return render(request, 'dashboard/display_select.html', {'businesses': businesses})


# ─── Queue management ─────────────────────────────────────────────────────────

@owner_required
def queue_management(request):
    businesses = Business.objects.filter(owner=request.user)
    branches   = Branch.objects.filter(business__in=businesses)
    today      = timezone.now().date()

    biz_pk = request.GET.get('business')

    active_sessions = Session.objects.filter(
        service__branch__in=branches,
        status=SessionStatus.ACTIVE,
        date=today,
    ).select_related('operator__user', 'service', 'service__branch').annotate(
        waiting_count=Count('tickets', filter=Q(tickets__status=StatusTypes.WAITING)),
        done_count=Count('tickets', filter=Q(tickets__status=StatusTypes.DONE)),
    )

    waiting_tickets = Ticket.objects.filter(
        service__branch__in=branches,
        status=StatusTypes.WAITING,
    ).select_related('service', 'service__branch', 'service__branch__business', 'customer').order_by('-is_vip', 'created_at')

    if biz_pk:
        active_sessions = active_sessions.filter(service__branch__business__pk=biz_pk)
        waiting_tickets = waiting_tickets.filter(service__branch__business__pk=biz_pk)

    if request.method == 'POST' and request.POST.get('action') == 'cancel_ticket':
        ticket_pk = request.POST.get('ticket_pk')
        ticket = get_object_or_404(Ticket, pk=ticket_pk, service__branch__in=branches)
        ticket.status = StatusTypes.CANCEL
        ticket.save(update_fields=['status'])
        messages.success(request, f"Chipta #{ticket.number} bekor qilindi")
        return redirect(request.get_full_path())

    return render(request, 'dashboard/queue_management.html', {
        'active_sessions': active_sessions,
        'waiting_tickets': waiting_tickets,
        'businesses':      businesses,
        'today':           today,
        'total_waiting':   waiting_tickets.count(),
        'filters': {'business': biz_pk},
    })