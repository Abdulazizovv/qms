from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.utils import timezone

def phone_validator(value: str):
    if not value.replace(" ", '').replace("+", "").isdigit():
        raise ValidationError("Telefon raqam formati noto'g'ri")

    if len(value) < 7 or len(value) > 14:
        raise ValidationError("Telefon raqam uzunligi noto'g'ri")



class MyUserManager(BaseUserManager):
    def create_user(self, phone, password, **kwargs):
        if not phone:
            raise ValidationError("Telefon raqam majburiy")
        
        normalized = str(phone).strip().replace(" ", "")
        user = self.model(phone=normalized, **kwargs)

        user.set_password(password)
        user.save()
        return user
    
    def create_superuser(self, phone, password, **kwargs):
        user = self.create_user(phone, password, **kwargs)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return user


class UserTypes(models.TextChoices):
    CLIENT = "client", "Mijoz"
    OWNER = "owner", "Biznes egasi"
    OPERATOR = "operator", "Boshqaruvchi"


LANGUAGE_CHOICES = [
    ("uz", "O‘zbekcha"),
    ("ru", "Русский"),
    ("en", "English"),
]

PAYMENT_METHODS = [
    ("cash", "Naqd"),
    ("card", "Plastik"),
]


class MyUser(AbstractUser):
    username = None

    phone = models.CharField(max_length=15, validators=[phone_validator], unique=True)
    preferred_language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default="uz")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default="cash")
    card_number = models.CharField(max_length=19, null=True, blank=True)
    notifications_enabled = models.BooleanField(default=True)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    user_type = models.CharField(max_length=20, choices=UserTypes.choices, default=UserTypes.CLIENT)

    objects = MyUserManager()

    def __str__(self):
        return self.phone


class PasswordResetCode(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=10)

    class Meta:
        verbose_name = "Parol tiklash kodi"
        verbose_name_plural = "Parol tiklash kodlari"