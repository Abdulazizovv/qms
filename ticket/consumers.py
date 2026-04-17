"""
WebSocket consumers — replace HTMX polling.
Groups:
  queue_{session_id}    → operator panel receives queue updates
  ticket_{number}       → client ticket page receives status updates
"""
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from ticket.models import Session, StatusTypes, Ticket


class QueueConsumer(AsyncWebsocketConsumer):
    """Operator panel: live queue data for a session."""

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.group     = f'queue_{self.session_id}'

        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

        # Push initial state immediately on connect
        await self.send(text_data=json.dumps(await self._build_payload()))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive(self, text_data):
        pass   # operator panel only reads, never writes

    # Called by channel layer when any service code calls group_send
    async def queue_update(self, event):
        await self.send(text_data=json.dumps(await self._build_payload()))

    @database_sync_to_async
    def _build_payload(self):
        try:
            session = Session.objects.select_related('service').get(pk=self.session_id)
        except Session.DoesNotExist:
            return {'type': 'error', 'message': 'Session not found'}

        current = session.get_current_ticket()
        waiting_qs = (
            Ticket.objects
            .filter(service=session.service, status=StatusTypes.WAITING)
            .order_by('-is_vip', 'created_at')[:20]
        )

        return {
            'type':           'queue_update',
            'waiting_count':  Ticket.objects.filter(
                service=session.service, status=StatusTypes.WAITING
            ).count(),
            'current_ticket': {
                'id':     current.id,
                'number': current.number,
                'is_vip': current.is_vip,
            } if current else None,
            'waiting': [
                {
                    'number':     t.number,
                    'is_vip':     t.is_vip,
                    'created_at': t.created_at.strftime('%H:%M'),
                }
                for t in waiting_qs
            ],
        }


class TicketConsumer(AsyncWebsocketConsumer):
    """Client ticket page: live status update for a single ticket."""

    async def connect(self):
        self.number = self.scope['url_route']['kwargs']['number']
        self.group  = f'ticket_{self.number}'

        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps(await self._build_payload()))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive(self, text_data):
        pass

    async def ticket_status(self, event):
        await self.send(text_data=json.dumps(await self._build_payload()))

    @database_sync_to_async
    def _build_payload(self):
        try:
            ticket = Ticket.objects.select_related('service__branch').get(number=self.number)
        except Ticket.DoesNotExist:
            return {'type': 'error', 'message': 'Ticket not found'}

        position  = ticket.queue_position()     if ticket.status == StatusTypes.WAITING else 0
        wait_mins = ticket.estimated_wait_minutes() if ticket.status == StatusTypes.WAITING else 0

        return {
            'type':           'ticket_status',
            'number':         ticket.number,
            'status':         ticket.status,
            'status_display': ticket.get_status_display(),
            'position':       position,
            'wait_mins':      wait_mins,
            'service':        ticket.service.title,
            'branch':         ticket.service.branch.title,
        }
