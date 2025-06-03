import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from app.models import CardEvent, CardUser

class ESP32Consumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("esp32_data", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("esp32_data", self.channel_name)

    async def receive(self, text_data):
        pass

    async def esp32_message(self, event):
        # Gửi dữ liệu về client
        await self.send(text_data=json.dumps(event["data"]))

        # Lưu vào database (nếu muốn)
        await self.save_event(event["data"])

    @sync_to_async
    def save_event(self, data):
        card_id = data.get("card_id")
        if card_id:
            try:
                card_user = CardUser.objects.select_related('user').get(card_id=card_id)
                CardEvent.objects.create(card_id=card_id, user=card_user.user)
            except Exception as e:
                print(f"Lỗi lưu CardEvent: {e}")