from django.db import models
from common.models import BaseModel


class BotUser(BaseModel):
    LANG_CHOICES = [('uz', "O'zbek"), ('ru', 'Русский'), ('en', 'English')]

    user_id      = models.CharField(max_length=100, unique=True)
    full_name    = models.CharField(max_length=525, null=True, blank=True)
    username     = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=15,  null=True, blank=True)
    language     = models.CharField(max_length=5, choices=LANG_CHOICES, default='uz')
    is_active    = models.BooleanField(default=True)

    def __str__(self):
        return self.full_name or self.user_id
    