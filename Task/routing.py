from django.urls import path
from .consumers import  TaskConsumer

websocket_urlpatterns = [
    path("ws/tasks/<int:user_id>/", TaskConsumer.as_asgi()),
]