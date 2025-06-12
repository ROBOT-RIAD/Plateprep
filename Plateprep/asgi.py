import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from Task.middleware import JWTAuthMiddleware, ProtocolAcceptMiddleware
from Task.routing import websocket_urlpatterns
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Plateprep.settings')



application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": ProtocolAcceptMiddleware(
        JWTAuthMiddleware(
            AuthMiddlewareStack(
                URLRouter(websocket_urlpatterns)
            )
        )
    ),
})