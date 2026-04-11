from django.db import models
from user.models import MyUser
from common.models import BaseModel



class Business(BaseModel):
    owner = models.ForeignKey(MyUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="businesses")
    title = models.CharField(max_length=255)
    about = models.TextField(null=True, blank=True)
    logo = models.ImageField(upload_to="business_logos/", null=True, blank=True)
    
    
class Branch(BaseModel):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, null=True, blank=True, related_name="branches")
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    working_days = models.CharField(max_length=255)
    open_time = models.TimeField()
    break_time = models.TimeField()




class Service(BaseModel):
    status_choices = [
        ("working", "Ishlamoqda"),
        ("break", "Tanaffus vaqtida"),
        ("inactive","Xizmat vaqtincha faol emas")
    ]
    
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="services")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    requirements = models.TextField(blank=True, null=True)
    estimated_time = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=status_choices, default="working")
    
    unicode = models.CharField(max_length=10, default="A")
    
    
    
class Operator(BaseModel):
    user = models.OneToOneField(MyUser, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="operators")
    
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    operator_number = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    
    

    
