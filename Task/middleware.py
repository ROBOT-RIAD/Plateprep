from channels.middleware import BaseMiddleware
from accounts.models import User
from asgiref.sync import sync_to_async
from rest_framework_simplejwt.tokens import AccessToken

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        headers = dict(scope["headers"])
        token = None
        selected_protocol = None

        if b'sec-websocket-protocol' in headers:
            protocols = headers[b'sec-websocket-protocol'].decode().split(",")
            for protocol in protocols:
                protocol = protocol.strip()
                if protocol.startswith("Bearer "):
                    token = protocol.split("Bearer ")[1]
                    selected_protocol = f"Bearer {token}"
                    break

        if token:
            try:
                access_token = AccessToken(token)
                user = await sync_to_async(User.objects.get)(id=access_token["user_id"])
                scope["user"] = user
            except Exception:
                scope["user"] = None
        else:
            scope["user"] = None

        scope["subprotocol"] = selected_protocol
        return await super().__call__(scope, receive, send)

class ProtocolAcceptMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        async def wrapped_send(message):
            if message["type"] == "websocket.accept" and "subprotocol" in scope and scope["subprotocol"]:
                message["subprotocol"] = scope["subprotocol"]
            await send(message)

        return await self.app(scope, receive, wrapped_send)
