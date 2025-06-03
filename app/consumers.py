import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

class ESP32Consumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("esp32_data", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("esp32_data", self.channel_name)

    async def receive(self, text_data):
        pass

    async def esp32_message(self, event):
        # Import model tại đây để tránh lỗi AppRegistryNotReady
        from app.models import CardEvent, CardUser
        await self.send(text_data=json.dumps(event["data"]))
        # Nếu cần truy cập model, làm ở đây