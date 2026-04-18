from django.urls import path
from botapp import views

app_name = 'client'

urlpatterns = [
    path('',                                                views.client_home,           name='home'),
    path('b/<int:branch_pk>/',                              views.branch_detail,         name='branch_detail'),
    path('b/<int:branch_pk>/take/<int:service_pk>/',        views.ticket_take,           name='ticket_take'),
    path('svc/<int:service_pk>/',                           views.service_detail,        name='service_detail'),
    path('t/<str:number>/',                                 views.my_ticket,             name='my_ticket'),
    path('t/fb/<int:ticket_id>/',                           views.ticket_feedback,       name='ticket_feedback'),
    path('t/cancel/<int:ticket_pk>/',                       views.ticket_cancel,         name='ticket_cancel'),

    # New main pages
    path('tickets/',                                        views.my_tickets_list,       name='my_tickets'),
    path('profile/',                                        views.profile_view,          name='profile'),
    path('help/',                                           views.help_view,             name='help'),

    # Appointments
    path('svc/<int:service_pk>/slots/',                     views.service_slots,         name='service_slots'),
    path('svc/<int:service_pk>/slots/<int:slot_pk>/book/',  views.appointment_book,      name='appointment_book'),
    path('appointments/',                                   views.my_appointments,       name='my_appointments'),
    path('appointments/<int:apt_pk>/cancel/',               views.appointment_cancel,    name='appointment_cancel'),
]
