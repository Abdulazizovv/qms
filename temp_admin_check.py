import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()
from django.contrib import admin
from ticket.models import Session
print('Session registered:', Session in admin.site._registry)
print('Registered models:', [m._meta.label for m in admin.site._registry])
