from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from business.models import Business, Branch, Service, Operator
from business.forms import BusinessForm, BranchForm, ServiceForm, OperatorCreateForm, OperatorEditForm
from ticket.models import Session, SessionStatus, Ticket
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