from django.urls import path

from .views import ChatApiView, RoomServiceChatView

urlpatterns = [
    path('', RoomServiceChatView.as_view(), name='room_service_chat'),
    path('api/chat/', ChatApiView.as_view(), name='chatbot_api'),
]
