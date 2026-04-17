from django.db import models
from common.models import BaseModel

class BotUser(BaseModel):
    user_id = models.CharField(max_length=100, unique=True)
    full_name = models.CharField(max_length=525, null=True, blank=True)
    username = models.CharField(max_length=255, null=True, blank=True)

    phone_number = models.CharField(max_length=15, null=True, blank=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.full_name
    