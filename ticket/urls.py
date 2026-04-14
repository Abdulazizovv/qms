from django.urls import path
from ticket import views

app_name = 'operator'

urlpatterns = [
    path('', views.operator_panel, name='panel'),
]
