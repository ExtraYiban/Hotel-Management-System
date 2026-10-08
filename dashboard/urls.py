from django.urls import path

from .views import ReportView


urlpatterns = [
    path('laporan/', ReportView.as_view(), name='report'),
]