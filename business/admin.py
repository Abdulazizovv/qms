from django.contrib import admin
from .models import Business, Branch, Operator, Service


admin.site.register(Branch)
admin.site.register(Business)
admin.site.register(Operator)
admin.site.register(Service)