from django import forms
from django.contrib.auth import authenticate
from user.models import MyUser, UserTypes, PasswordResetCode


class LoginForm(forms.Form):
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'placeholder': '+998901234567'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Parolingiz'})
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        phone = cleaned.get('phone', '').strip().replace(' ', '')
        password = cleaned.get('password', '')

        if phone and password:
            user = authenticate(self.request, username=phone, password=password)
            if user is None:
                raise forms.ValidationError("Telefon raqam yoki parol noto'g'ri")
            if not user.is_active:
                raise forms.ValidationError("Hisob faol emas")
            cleaned['user'] = user
        return cleaned


class ForgotPasswordForm(forms.Form):
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'placeholder': '+998901234567'})
    )

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip().replace(' ', '')
        if not MyUser.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Bu telefon raqam ro'yxatdan o'tmagan")
        return phone


class VerifyResetCodeForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={'placeholder': '123456'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip()
        if not self.user:
            raise forms.ValidationError("Foydalanuvchi topilmadi")
        
        try:
            reset_code = PasswordResetCode.objects.get(
                user=self.user, 
                code=code, 
                is_used=False
            )
            if reset_code.is_expired():
                raise forms.ValidationError("Kod muddati tugagan")
        except PasswordResetCode.DoesNotExist:
            raise forms.ValidationError("Noto'g'ri kod")
        
        return code


class ResetPasswordForm(forms.Form):
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Yangi parol'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Parolni takrorlang'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('password1')
        password2 = cleaned.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Parollar mos kelmaydi")
        return cleaned


class RegisterForm(forms.Form):
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Ismingiz'})
    )
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'placeholder': '+998901234567'})
    )
    user_type = forms.ChoiceField(
        choices=[('owner', 'Biznes egasi'), ('client', 'Mijoz')],
        initial='owner'
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Parol'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Parolni takrorlang'})
    )

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip().replace(' ', '')
        if MyUser.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Bu telefon raqam allaqachon ro'yxatdan o'tgan")
        return phone

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1', '')
        p2 = cleaned.get('password2', '')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Parollar mos kelmadi")
        if p1 and len(p1) < 6:
            self.add_error('password1', "Parol kamida 6 ta belgidan iborat bo'lishi kerak")
        return cleaned

    def save(self):
        data = self.cleaned_data
        user = MyUser.objects.create_user(
            phone=data['phone'],
            password=data['password1'],
            first_name=data['first_name'],
            user_type=data['user_type'],
        )
        return user

    def save(self):
        data = self.cleaned_data
        user = MyUser.objects.create_user(
            phone=data['phone'],
            password=data['password1'],
            first_name=data['first_name'],
            user_type=data['user_type'],
        )
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = MyUser
        fields = [
            'first_name',
            'payment_method',
            'card_number',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Ismingiz', 'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'card_number': forms.TextInput(attrs={'placeholder': 'Plastik karta raqami', 'class': 'form-control'}),
        }

    def clean_card_number(self):
        method = self.cleaned_data.get('payment_method')
        number = self.cleaned_data.get('card_number')
        number = (number or '').strip()
        if method == 'card' and not number:
            raise forms.ValidationError("Plastik karta raqamini kiriting")
        if number and not number.replace(' ', '').isdigit():
            raise forms.ValidationError("Karta raqami faqat raqamlardan iborat bo'lishi kerak")
        return number


class LanguagePreferenceForm(forms.ModelForm):
    class Meta:
        model = MyUser
        fields = ['preferred_language']
        widgets = {
            'preferred_language': forms.Select(attrs={'class': 'form-control'}),
        }


class NotificationPreferencesForm(forms.ModelForm):
    notifications_enabled = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = MyUser
        fields = ['notifications_enabled']


class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Hozirgi parol', 'class': 'form-control'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Yangi parol', 'class': 'form-control'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Yangi parolni tasdiqlang', 'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        password = self.cleaned_data.get('current_password', '')
        if self.user and not self.user.check_password(password):
            raise forms.ValidationError("Hozirgi parol noto'g'ri")
        return password

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('password1')
        password2 = cleaned.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Yangi parollar mos kelmadi")
        if password1 and len(password1) < 6:
            raise forms.ValidationError("Parol kamida 6 ta belgidan iborat bo'lishi kerak")
        return cleaned


class DeleteAccountForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Parolingiz', 'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get('password', '')
        if self.user and not self.user.check_password(password):
            raise forms.ValidationError("Parol noto'g'ri")
        return password