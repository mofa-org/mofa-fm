"""
WebSocket consumer for real-time debate/conference streaming.
Based on mofa-studio's conference-controller logic.
"""
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class DebateConsumer(AsyncWebsocketConsumer):
    """
    Real-time debate WebSocket consumer.

    Features:
    - Stream dialogue entries to clients in real-time
    - Handle human interrupt (user messages)
    - Track round numbers and participant statistics
    """

    async def connect(self):
        self.episode_id = self.scope['url_route']['kwargs']['episode_id']
        self.room_group_name = f"debate_{self.episode_id}"
        self.user = self.scope.get('user')

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Send initial status
        await self.send(text_data=json.dumps({
            'type': 'connected',
            'episode_id': self.episode_id,
            'message': 'Connected to debate stream'
        }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Handle incoming messages from client.
        Supports:
        - human_message: User interruption to add a message
        - ping: Keep connection alive
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'unknown')

            if message_type == 'human_message':
                # Handle human interrupt
                content = data.get('content', '').strip()
                if content:
                    await self.handle_human_message(content)

            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))

    async def handle_human_message(self, content):
        """
        Handle human interrupt - user sends a message during the debate.
        This will:
        1. Add user message to dialogue
        2. Trigger AI follow-up generation
        """
        from .tasks import generate_debate_followup_task

        # Add user message to dialogue immediately
        await self.add_human_message(content)

        # Broadcast to all clients
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'dialogue_entry',
                'entry': {
                    'participant': 'human',
                    'role': '你',
                    'content': content,
                    'timestamp': timezone.now().isoformat(),
                    'is_human': True
                }
            }
        )

        # Trigger AI follow-up (async task)
        # This will stream responses back via group_send
        await self.trigger_ai_followup()

    @database_sync_to_async
    def add_human_message(self, content):
        """Add human message to episode dialogue in database."""
        from .models import Episode

        try:
            episode = Episode.objects.get(id=self.episode_id)
            dialogue = list(episode.dialogue or [])
            dialogue.append({
                'participant': 'human',
                'content': content,
                'timestamp': timezone.now().isoformat()
            })
            episode.dialogue = dialogue
            episode.save(update_fields=['dialogue', 'updated_at'])
        except Episode.DoesNotExist:
            pass

    async def trigger_ai_followup(self):
        """Trigger async task to generate AI response."""
        # The task will stream responses via channel_layer
        from .tasks import stream_debate_response

        # Use asyncio to not block
        asyncio.create_task(
            stream_debate_response(self.episode_id, self.room_group_name)
        )

    # Group message handlers

    async def dialogue_entry(self, event):
        """
        Handle dialogue_entry message from channel layer.
        Broadcast dialogue entry to WebSocket client.
        """
        await self.send(text_data=json.dumps({
            'type': 'dialogue_entry',
            'entry': event['entry']
        }))

    async def dialogue_chunk(self, event):
        """
        Handle streaming chunk from channel layer.
        Used for real-time streaming of AI responses.
        """
        await self.send(text_data=json.dumps({
            'type': 'dialogue_chunk',
            'participant': event.get('participant'),
            'content': event.get('content'),
            'is_complete': event.get('is_complete', False)
        }))

    async def status_update(self, event):
        """Handle status updates (e.g., generation started/completed)."""
        await self.send(text_data=json.dumps({
            'type': 'status',
            'status': event.get('status'),
            'message': event.get('message', '')
        }))
