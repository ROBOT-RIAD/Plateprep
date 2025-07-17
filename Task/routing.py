from django.urls import path
from .consumers import  TaskConsumer

websocket_urlpatterns = [
    path("ws/tasks/<str:email>/", TaskConsumer.as_asgi()),
]