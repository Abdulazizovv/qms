from django.db import models, transaction
from django.utils import timezone
from business.models import Operator, Service
from common.models import BaseModel
from user.models import MyUser


class SessionStatus(models.TextChoices):
    ACTIVE = 'active', 'Faol'
    PAUSED = 'paused', 'Tanaffusda'
    CLOSED = 'closed', 'Yopildi'


class StatusTypes(models.TextChoices):
    WAITING = 'waiting', 'Kutilmoqda'
    PROCESS = 'process', 'Jarayonda'
    DONE    = 'done',    'Bajarildi'
    CANCEL  = 'cancel',  'Bekor qilindi'
    SKIPPED = 'skipped', "O'tkazib yuborildi"


class Session(BaseModel):
    operator   = models.ForeignKey(Operator, on_delete=models.CASCADE, related_name='sessions')
    service    = models.ForeignKey(Service,  on_delete=models.CASCADE, related_name='sessions')
    status     = models.CharField(max_length=10, choices=SessionStatus, default=SessionStatus.ACTIVE)
    date       = models.DateField(auto_now_add=True)
    started_at = models.DateTimeField(auto_now_add=True)
    closed_at  = models.DateTimeField(null=True, blank=True)

    def get_current_ticket(self):
        return self.tickets.filter(status=StatusTypes.PROCESS).first()

    def __str__(self):
        return f"Sessiya #{self.id} — {self.operator} ({self.date})"

    class Meta:
        ordering = ['-created_at']


class Ticket(BaseModel):
    service  = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name='tickets'
    )
    session  = models.ForeignKey(
        Session, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tickets'
    )
    customer = models.ForeignKey(
        MyUser, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tickets'
    )
    number      = models.CharField(max_length=10, editable=False)
    status      = models.CharField(max_length=10, choices=StatusTypes, default=StatusTypes.WAITING)
    is_vip      = models.BooleanField(default=False)
    called_at   = models.DateTimeField(null=True, blank=True)
    served_at   = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.number:
            with transaction.atomic():
                prefix = self.service.ticket_prefix
                last = (
                    Ticket.objects
                    .select_for_update()
                    .filter(service=self.service)
                    .order_by('-created_at')
                    .first()
                )
                if last and last.number[len(prefix):].isdigit():
                    next_num = int(last.number[len(prefix):]) + 1
                else:
                    next_num = 1
                self.number = f"{prefix}{next_num:03d}"
        super().save(*args, **kwargs)

    def queue_position(self):
        """Tickets ahead of this one in the waiting queue."""
        qs = Ticket.objects.filter(service=self.service, status=StatusTypes.WAITING)
        if self.is_vip:
            return qs.filter(is_vip=True, created_at__lt=self.created_at).count()
        return (
            qs.filter(is_vip=True).count() +
            qs.filter(is_vip=False, created_at__lt=self.created_at).count()
        )

    def estimated_wait_minutes(self):
        return self.queue_position() * self.service.estimated_time_minutes

    def __str__(self):
        return f"Chipta {self.number} — {self.get_status_display()}"

    class Meta:
        ordering = ['-is_vip', 'created_at']
        unique_together = [('service', 'number')]


class Feedback(BaseModel):
    ticket  = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name='feedback')
    rating  = models.PositiveSmallIntegerField()   # 1–5
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"Baho: {self.ticket.number} — {self.rating}★"


# ─── Appointment (time-slot booking) ──────────────────────────────────────────

class AppointmentStatus(models.TextChoices):
    PENDING   = 'pending',   'Kutilmoqda'
    CONFIRMED = 'confirmed', 'Tasdiqlangan'
    CANCELLED = 'cancelled', 'Bekor qilindi'
    COMPLETED = 'completed', 'Bajarildi'
    NO_SHOW   = 'no_show',   'Kelmadi'


class Appointment(BaseModel):
    """Client booking for a specific time slot (doctor / barbershop style)."""
    from business.models import TimeSlot   # local import to avoid circular

    time_slot          = models.ForeignKey(
        'business.TimeSlot', on_delete=models.CASCADE, related_name='appointments'
    )
    customer           = models.ForeignKey(
        MyUser, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='appointments'
    )
    status             = models.CharField(
        max_length=15, choices=AppointmentStatus, default=AppointmentStatus.PENDING
    )
    notes              = models.TextField(blank=True)
    telegram_notified  = models.BooleanField(default=False)

    def __str__(self):
        return f"Qabul #{self.id} — {self.time_slot} [{self.status}]"

    class Meta:
        unique_together    = [('time_slot', 'customer')]
        ordering           = ['time_slot__date', 'time_slot__start_time']
        verbose_name       = 'Qabul'
        verbose_name_plural = 'Qabullar'
