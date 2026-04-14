from django.urls import path
from botapp import views

app_name = 'client'

urlpatterns = [
    path('', views.client_home, name='home'),
]
