from channels.generic.websocket import AsyncJsonWebsocketConsumer


class EchoConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send_json({"type": "welcome", "message": "WebSocket connected"})

    async def receive_json(self, content, **kwargs):
        await self.send_json({"type": "echo", "payload": content})

    async def disconnect(self, code):
        pass
