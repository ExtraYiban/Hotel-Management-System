from django.urls import path
from .views import BookingCreateView, BookingDetailView, BookingLatestView, BookingListView, PaymentCreateView

urlpatterns = [
    path('buat/', BookingCreateView.as_view(), name='booking_create'),
    path('riwayat/', BookingListView.as_view(), name='booking_list'),
    path('terakhir/', BookingLatestView.as_view(), name='booking_latest'),
    path('<int:pk>/', BookingDetailView.as_view(), name='booking_detail'),
    path('<int:booking_id>/bayar/', PaymentCreateView.as_view(), name='payment_create'),
]