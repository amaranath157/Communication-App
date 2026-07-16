import json
import uuid
import time
from datetime import datetime
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .redis_helpers import (
    set_user_online, remove_user_online, get_user_channel,
    add_to_waiting_queue, remove_from_waiting_queue, get_waiting_user,
    create_active_room, get_active_room, delete_active_room
)
from .models import CallHistory

class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user')
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
            
        self.user_id = str(self.user.id)
        
        # Accept the connection
        await self.accept()
        
        # Store user in Redis online list
        set_user_online(self.user_id, self.channel_name)

    async def disconnect(self, close_code):
        if hasattr(self, 'user_id'):
            remove_user_online(self.user_id)
            remove_from_waiting_queue(self.user_id)
            # Active rooms cleanup logic can be added if needed
            # For WebRTC, the disconnected peer will break the connection and the other will send end_call

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data.get('type')

        if event_type == 'start_call':
            await self.handle_start_call()
        elif event_type in ['offer', 'answer', 'ice_candidate']:
            await self.handle_signaling(data)
        elif event_type == 'end_call':
            await self.handle_end_call(data)

    async def handle_start_call(self):
        # Check waiting queue
        partner_id = get_waiting_user(exclude_user_id=self.user_id)
        
        if partner_id:
            # Match found
            room_id = str(uuid.uuid4())
            create_active_room(room_id, self.user_id, partner_id)
            
            # Send 'matched' to current user
            await self.send(text_data=json.dumps({
                "type": "matched",
                "room_id": room_id,
                "partner_id": int(partner_id)
            }))
            
            # Send 'matched' to partner
            partner_channel = get_user_channel(partner_id)
            if partner_channel:
                await self.channel_layer.send(
                    partner_channel,
                    {
                        "type": "send_match",
                        "room_id": room_id,
                        "partner_id": int(self.user_id)
                    }
                )
        else:
            # No user waiting, add to queue
            add_to_waiting_queue(self.user_id)
            await self.send(text_data=json.dumps({
                "type": "waiting",
                "message": "Searching for user"
            }))

    async def send_match(self, event):
        """Handler for 'send_match' type message from channel layer."""
        await self.send(text_data=json.dumps({
            "type": "matched",
            "room_id": event["room_id"],
            "partner_id": event["partner_id"]
        }))

    async def handle_signaling(self, data):
        room_id = data.get("room_id")
        room_data = get_active_room(room_id)
        if not room_data:
            return
            
        # Determine who is the partner
        user1 = str(room_data["user1"])
        user2 = str(room_data["user2"])
        
        partner_id = user2 if self.user_id == user1 else user1
        
        # Forward message to partner
        partner_channel = get_user_channel(partner_id)
        if partner_channel:
            await self.channel_layer.send(
                partner_channel,
                {
                    "type": "forward_signaling",
                    "data": data
                }
            )

    async def forward_signaling(self, event):
        """Handler for 'forward_signaling' type message from channel layer."""
        await self.send(text_data=json.dumps(event["data"]))

    async def handle_end_call(self, data):
        room_id = data.get("room_id")
        room_data = get_active_room(room_id)
        if not room_data:
            return

        user1 = str(room_data["user1"])
        user2 = str(room_data["user2"])
        start_time_ts = room_data.get("start_time")
        
        # Delete room from Redis
        delete_active_room(room_id)
        
        partner_id = user2 if self.user_id == user1 else user1
        
        # Notify partner
        partner_channel = get_user_channel(partner_id)
        if partner_channel:
            await self.channel_layer.send(
                partner_channel,
                {
                    "type": "forward_signaling",
                    "data": {
                        "type": "end_call",
                        "room_id": room_id
                    }
                }
            )
            
        # Save call history in MySQL
        await self.save_call_history(user1, user2, start_time_ts)

    @database_sync_to_async
    def save_call_history(self, user1_id, user2_id, start_time_ts):
        try:
            duration = 0
            start_dt = timezone.now()
            if start_time_ts:
                duration = int(time.time() - start_time_ts)
                start_dt = timezone.datetime.fromtimestamp(start_time_ts, tz=timezone.utc)
                
            CallHistory.objects.create(
                user1_id=int(user1_id),
                user2_id=int(user2_id),
                start_time=start_dt,
                end_time=timezone.now(),
                duration=duration
            )
        except Exception as e:
            print(f"Error saving call history: {e}")
