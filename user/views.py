from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from user.forms import (
    LoginForm,
    RegisterForm,
    ForgotPasswordForm,
    VerifyResetCodeForm,
    ResetPasswordForm,
    ProfileForm,
    LanguagePreferenceForm,
    NotificationPreferencesForm,
    PasswordChangeForm,
    DeleteAccountForm,
)
from user.models import MyUser, PasswordResetCode
import random


def login_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    form = LoginForm(request.POST or None, request=request)

    if request.method == 'POST' and form.is_valid():
        user = form.cleaned_data['user']
        login(request, user)
        request.session['preferred_language'] = user.preferred_language
        request.session.modified = True
        messages.success(request, f"Xush kelibsiz, {user.first_name or user.phone}!")
        return _redirect_by_role(user)

    return render(request, 'auth/login.html', {'form': form})


def forgot_password_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    form = ForgotPasswordForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        phone = form.cleaned_data['phone']
        user = MyUser.objects.get(phone=phone)
        
        # Generate 6-digit code
        code = str(random.randint(100000, 999999))
        
        # Save code to database
        PasswordResetCode.objects.filter(user=user, is_used=False).update(is_used=True)  # Invalidate old codes
        PasswordResetCode.objects.create(user=user, code=code)
        
        # TODO: Send SMS with code (for now just show in message)
        messages.success(request, f"SMS yuborildi! Kod: {code} (demo uchun)")
        
        # Redirect to code verification
        request.session['reset_phone'] = phone
        return redirect('auth:verify_reset_code')

    return render(request, 'auth/forgot_password.html', {'form': form})


def verify_reset_code_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    phone = request.session.get('reset_phone')
    if not phone:
        messages.error(request, "Avval telefon raqamingizni kiriting")
        return redirect('auth:forgot_password')

    try:
        user = MyUser.objects.get(phone=phone)
    except MyUser.DoesNotExist:
        messages.error(request, "Foydalanuvchi topilmadi")
        return redirect('auth:forgot_password')

    form = VerifyResetCodeForm(request.POST or None, user=user)

    if request.method == 'POST' and form.is_valid():
        code = form.cleaned_data['code']
        reset_code = PasswordResetCode.objects.get(user=user, code=code, is_used=False)
        reset_code.is_used = True
        reset_code.save()
        
        # Store user id in session for password reset
        request.session['reset_user_id'] = user.id
        return redirect('auth:reset_password')

    return render(request, 'auth/verify_reset_code.html', {'form': form, 'phone': phone})


def reset_password_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    user_id = request.session.get('reset_user_id')
    if not user_id:
        messages.error(request, "Avval kodni tasdiqlang")
        return redirect('auth:forgot_password')

    try:
        user = MyUser.objects.get(id=user_id)
    except MyUser.DoesNotExist:
        messages.error(request, "Foydalanuvchi topilmadi")
        return redirect('auth:forgot_password')

    form = ResetPasswordForm(request.POST or None, user=user)

    if request.method == 'POST' and form.is_valid():
        password = form.cleaned_data['password1']
        user.set_password(password)
        user.save()
        
        # Clear session
        del request.session['reset_phone']
        del request.session['reset_user_id']
        
        messages.success(request, "Parol muvaffaqiyatli o'zgartirildi! Endi kirishingiz mumkin.")
        return redirect('auth:login')

    return render(request, 'auth/reset_password.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    form = RegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        request.session['preferred_language'] = user.preferred_language
        request.session.modified = True
        messages.success(request, "Hisob muvaffaqiyatli yaratildi!")
        return _redirect_by_role(user)

    return render(request, 'auth/register.html', {'form': form})


@login_required
def profile_view(request):
    if not request.user.is_authenticated:
        return redirect('auth:login')

    profile_form = ProfileForm(request.POST or None, instance=request.user)
    notifications_form = NotificationPreferencesForm(request.POST or None, instance=request.user)
    language_form = LanguagePreferenceForm(request.POST or None, instance=request.user)
    password_form = PasswordChangeForm(request.POST or None, user=request.user, prefix='pw')
    delete_form = DeleteAccountForm(request.POST or None, user=request.user, prefix='del')
    active_section = request.POST.get('active_section', 'payment')

    if request.method == 'POST':
        section = request.POST.get('profile_section')
        if section == 'payment' and profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Profil sozlamalari saqlandi")
            return redirect('auth:profile')
        elif section == 'notifications' and notifications_form.is_valid():
            notifications_form.save()
            messages.success(request, "Bildirishnoma sozlamalari saqlandi")
            return redirect('auth:profile')
        elif section == 'language' and language_form.is_valid():
            language_form.save()
            request.session['preferred_language'] = request.user.preferred_language
            request.session.modified = True
            messages.success(request, "Profil sozlamalari saqlandi")
            return redirect('auth:profile')
        elif 'change_password' in request.POST and password_form.is_valid():
            request.user.set_password(password_form.cleaned_data['password1'])
            request.user.save()
            messages.success(request, "Parol muvaffaqiyatli yangilandi")
            return redirect('auth:profile')
        elif 'delete_account' in request.POST and delete_form.is_valid():
            logout(request)
            request.user.delete()
            messages.success(request, "Hisobingiz o'chirildi")
            return redirect('auth:login')

    return render(request, 'auth/profile.html', {
        'profile_form': profile_form,
        'notifications_form': notifications_form,
        'language_form': language_form,
        'password_form': password_form,
        'delete_form': delete_form,
        'active_section': active_section,
    })


def logout_view(request):
    logout(request)
    messages.success(request, "Tizimdan muvaffaqiyatli chiqdingiz")
    return redirect('auth:login')


def _redirect_by_role(user):
    """User roliga qarab yo'naltirish"""
    if user.user_type == 'owner':
        return redirect('dashboard:index')
    elif user.user_type == 'operator':
        return redirect('business:operator_panel')
    else:
        return redirect('client:home')