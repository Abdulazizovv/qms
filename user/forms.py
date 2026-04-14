from django import forms
from django.contrib.auth import authenticate
from user.models import MyUser, UserTypes


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