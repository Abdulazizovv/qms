from django.urls import re_path
from ticket import consumers

websocket_urlpatterns = [
    # Operator panel: real-time queue updates for a session
    re_path(r'^ws/queue/(?P<session_id>\d+)/$', consumers.QueueConsumer.as_asgi()),

    # Client ticket page: live status updates for a ticket
    re_path(r'^ws/ticket/(?P<number>[A-Z0-9]+)/$', consumers.TicketConsumer.as_asgi()),
]
