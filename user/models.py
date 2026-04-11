from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError

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


class MyUser(AbstractUser):
    username = None

    phone = models.CharField(max_length=15, validators=[phone_validator], unique=True)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    user_type = models.CharField(max_length=20, choices=UserTypes.choices, default=UserTypes.CLIENT)

    objects = MyUserManager()

    def __str__(self):
        return self.phone