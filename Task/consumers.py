from channels.generic.websocket import AsyncWebsocketConsumer
import json
from accounts.models import User
from channels.db import database_sync_to_async

class TaskConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.email = self.scope["url_route"]["kwargs"]["email"]
        try:
            user = await self.get_user_by_email(self.email)
            self.user_id = user.id
            self.group_name = f"user_{self.user_id}"

            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        except User.DoesNotExist:
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def task_status_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "status_update",
            "task_id": event["task_id"],
            "new_status": event["new_status"]
        }))

    async def new_task_assigned(self, event):
        await self.send(text_data=json.dumps({
            "type": "new_task",
            "task_id": event["task_id"],
            "task_name": event["task_name"],
            "assigned_by": event["assigned_by"],
            "date": event["date"],
            "duration": event["duration"],
            "status": event["status"]
        }))

    @database_sync_to_async
    def get_user_by_email(self, email):
        return User.objects.get(email=email)