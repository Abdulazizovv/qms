from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from user.forms import LoginForm, RegisterForm


def login_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user, request)

    form = LoginForm(request.POST or None, request=request)

    if request.method == 'POST' and form.is_valid():
        user = form.cleaned_data['user']
        login(request, user)
        messages.success(request, f"Xush kelibsiz, {user.first_name or user.phone}!")
        return _redirect_by_role(user, request)

    return render(request, 'auth/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user, request)

    form = RegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Hisob muvaffaqiyatli yaratildi!")
        return _redirect_by_role(user, request)

    return render(request, 'auth/register.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Tizimdan muvaffaqiyatli chiqdingiz")
    return redirect('/')


def _redirect_by_role(user, request=None):
    """User roliga qarab yo'naltirish. 'next' parametri faqat client uchun ishlatiladi."""
    if user.user_type == 'owner':
        return redirect('dashboard:index')
    if user.user_type == 'operator':
        return redirect('operator:panel')
    # Client: respect 'next' param if safe
    if request:
        next_url = request.GET.get('next') or request.POST.get('next', '')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
    return redirect('client:home')