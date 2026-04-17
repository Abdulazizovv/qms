from django.urls import path
from ticket import views

app_name = 'operator'

urlpatterns = [
    path('',                                 views.operator_panel,    name='panel'),
    path('session/start/',                   views.session_start,     name='session_start'),
    path('session/<int:session_id>/close/',  views.session_close,     name='session_close'),
    path('session/<int:session_id>/next/',   views.ticket_call_next,  name='ticket_call_next'),
    path('session/<int:session_id>/queue/',  views.queue_fragment,    name='queue_fragment'),
    path('ticket/<int:ticket_id>/finish/',   views.ticket_finish,     name='ticket_finish'),
    path('ticket/<int:ticket_id>/skip/',     views.ticket_skip,       name='ticket_skip'),
]
