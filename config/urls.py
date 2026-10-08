"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""
URL configuration for config project.
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include  # <-- 1. Tambahkan include di sini
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from dashboard.views import DashboardView
from rooms.views import RoomDetailView, RoomListView


def health_check(request):
    """Endpoint ringan untuk monitor/uptime checker. Selalu 200 OK."""
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('', DashboardView.as_view(), name='home'),
    path('health/', health_check, name='health'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('rooms/', RoomListView.as_view(), name='room_list'),
    path('rooms/<int:room_id>/', RoomDetailView.as_view(), name='room_detail'),
    path('reservations/', include('reservations.urls')),
    path('room-service/', include('chatbot.urls')),
]

#Supaya foto bukti transfer pembayaran bisa dibuka saat testing lokal
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)