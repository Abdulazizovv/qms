from django.urls import path
from business import views
from .views import home

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_index, name='index'),
    path('home/', home, name='home')
]
