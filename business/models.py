from django.db import models
from user.models import MyUser
from common.models import BaseModel



class Business(BaseModel):
    owner = models.ForeignKey(
        MyUser, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="businesses"
    )
    title = models.CharField(max_length=255)
    about = models.TextField(null=True, blank=True)
    logo = models.ImageField(upload_to="business_logos/", null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Business"
        verbose_name_plural = "Businesses"
    
    
class Branch(BaseModel):
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE,
        related_name="branches"           # null/blank olib tashlandi
    )
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.business.title} — {self.title}"

    class Meta:
        verbose_name = "Branch"
        verbose_name_plural = "Branches"


class WorkingDay(BaseModel):
    """working_days CharField o'rniga alohida model."""
    DAYS = [
        (0, "Dushanba"), (1, "Seshanba"), (2, "Chorshanba"),
        (3, "Payshanba"), (4, "Juma"), (5, "Shanba"), (6, "Yakshanba"),
    ]
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="working_days"
    )
    day = models.IntegerField(choices=DAYS)
    open_time = models.TimeField()
    close_time = models.TimeField()
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.branch.title} — {self.get_day_display()}"

    class Meta:
        unique_together = ("branch", "day")
        ordering = ["day"]




class QueueType(models.TextChoices):
    REALTIME    = 'realtime',    'Real-time navbat'
    APPOINTMENT = 'appointment', 'Qabulga yozilish'
    BOTH        = 'both',        'Ikkalasi ham'


class Service(BaseModel):
    STATUS_CHOICES = [
        ('active',   'Ishlamoqda'),
        ('break',    'Tanaffus vaqtida'),
        ('inactive', 'Xizmat vaqtincha faol emas'),
    ]

    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name='services'
    )
    title                  = models.CharField(max_length=255)
    description            = models.TextField(blank=True, null=True)
    requirements           = models.TextField(blank=True, null=True)
    estimated_time_minutes = models.PositiveIntegerField()
    status                 = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    price                  = models.PositiveBigIntegerField(default=0)
    ticket_prefix          = models.CharField(max_length=5, default='A')
    queue_type             = models.CharField(max_length=15, choices=QueueType, default=QueueType.REALTIME)

    def __str__(self):
        return f"{self.branch.title} — {self.title}"


class TimeSlot(BaseModel):
    """Available appointment slots set by the business owner."""
    service      = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='time_slots')
    date         = models.DateField()
    start_time   = models.TimeField()
    end_time     = models.TimeField()
    max_capacity = models.PositiveIntegerField(default=1)
    is_active    = models.BooleanField(default=True)

    @property
    def booked_count(self):
        return self.appointments.filter(status__in=['pending', 'confirmed']).count()

    @property
    def available_count(self):
        return max(0, self.max_capacity - self.booked_count)

    @property
    def is_full(self):
        return self.available_count == 0

    def __str__(self):
        return f"{self.service.title} | {self.date} {self.start_time:%H:%M}–{self.end_time:%H:%M}"

    class Meta:
        ordering           = ['date', 'start_time']
        unique_together    = [('service', 'date', 'start_time')]
        verbose_name       = 'Vaqt sloti'
        verbose_name_plural = 'Vaqt slotlari'
    
    
    
class Operator(BaseModel):
    user = models.OneToOneField(MyUser, on_delete=models.CASCADE)
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="operators"
    )
    services = models.ManyToManyField(         # ForeignKey → ManyToMany
        Service, related_name="operators", blank=True
    )
    desk_number = models.CharField(max_length=20)   # "operator_number" → "desk_number"
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user} — stol {self.desk_number}"
    
    

    
