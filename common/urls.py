from django.urls import path
from business import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_index, name='index'),
]
