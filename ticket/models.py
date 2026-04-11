from django.db import models
from business.models import Operator, Service, BaseModel


class StatusTypes(models.TextChoices):
    WAITING = 'waiting', 'Kutilmoqda'
    PROCESS = 'process', 'Jarayonda'
    DONE = 'done', 'Bajarildi'
    CANCEL = 'cancel', 'Bekor qilindi'
    SKIPPED = 'skipped', 'O\'tkazib yuborildi'


class Session(BaseModel):
    operator = models.ForeignKey(Operator, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    #status = models.CharField(max_length=10, choices=StatusTypes, default=StatusTypes.WAITING)


class Ticket(BaseModel):
    number = models.CharField(max_length=8)
    session = models.ForeignKey(Session, on_delete=models.RESTRICT)
    status = models.CharField(max_length=10, choices=StatusTypes, default=StatusTypes.WAITING)