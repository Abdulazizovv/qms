from django.urls import path
from botapp import views

app_name = 'client'

urlpatterns = [
    path('', views.client_home, name='home'),
    path('businesses/', views.business_list, name='business_list'),
    path('business/<int:biz_pk>/branches/', views.branch_list, name='branch_list'),
    path('branch/<int:branch_pk>/services/', views.service_list, name='service_list'),
    path('ticket/<int:ticket_pk>/', views.ticket_detail, name='ticket_detail'),
    path('ticket/<int:ticket_pk>/status/', views.ticket_status_partial, name='ticket_status_partial'),
]
