from django.urls import path, include

urlpatterns = [
    path('rooms/', include('rooms.urls')),
]