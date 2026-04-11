from django.db import models
from django.utils.crypto import get_random_string
from business.models import Operator, Service
from common.models import BaseModel
from user.models import MyUser
from django.db import transaction


class SessionStatus(models.TextChoices):
    PENDING = 'pending', 'Kutilmoqda'      # yaratildi, boshlanmagan
    ACTIVE  = 'active',  'Faol'            # operator ishlayapti
    PAUSED  = 'paused',  'Tanaffusda'      # vaqtincha to'xtatildi
    CLOSED  = 'closed',  'Yopildi'         # ish kuni tugadi

class StatusTypes(models.TextChoices):
    WAITING = 'waiting', 'Kutilmoqda'
    PROCESS = 'process', 'Jarayonda'
    DONE    = 'done',    'Bajarildi'
    CANCEL  = 'cancel',  'Bekor qilindi'
    SKIPPED = 'skipped', "O'tkazib yuborildi"


class Session(BaseModel):
    operator = models.ForeignKey(
        Operator, on_delete=models.CASCADE, related_name="sessions"
    )
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="sessions"
    )
    status = models.CharField(
        max_length=10, choices=SessionStatus, default=SessionStatus.PENDING
    )
    date = models.DateField(auto_now_add=True)
    current_ticket = models.OneToOneField(
        "Ticket", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="active_session"
    )

    # Sessiya vaqt kuzatuvi
    started_at = models.DateTimeField(null=True, blank=True)
    closed_at  = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Session {self.id} — {self.operator} ({self.date})"

    class Meta:
        unique_together = ("operator", "date")


class Ticket(BaseModel):
    session = models.ForeignKey(
        Session, on_delete=models.RESTRICT, related_name="tickets"
    )
    customer = models.ForeignKey(
        MyUser, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="tickets"
    )
    number = models.CharField(max_length=8, unique=True, editable=False)
    status = models.CharField(
        max_length=10, choices=StatusTypes, default=StatusTypes.WAITING
    )
    is_vip = models.BooleanField(default=False)

    # Vaqt kuzatuvi
    called_at  = models.DateTimeField(null=True, blank=True)
    served_at  = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.number:
            with transaction.atomic():
                prefix = self.session.service.ticket_prefix
                last = (
                    Ticket.objects
                    .select_for_update()          # qatorni lock qiladi
                    .filter(session=self.session)
                    .order_by('-created_at')
                    .first()
                )
                if last and last.number[len(prefix):].isdigit():
                    next_num = int(last.number[len(prefix):]) + 1
                else:
                    next_num = 1
                self.number = f"{prefix}{next_num:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ticket {self.number} — {self.get_status_display()}"

    class Meta:
        ordering = ["-is_vip", "created_at"]   # VIP birinchi