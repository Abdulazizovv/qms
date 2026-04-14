from django.urls import path
from business import views

app_name = 'business'

urlpatterns = [
    path('', views.business_list, name='list'),
]
