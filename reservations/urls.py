from django.urls import path
from .views import BookingCreateView, BookingDetailView, PaymentCreateView

urlpatterns = [
    path('buat/', BookingCreateView.as_view(), name='booking_create'),
    path('<int:pk>/', BookingDetailView.as_view(), name='booking_detail'),
    path('<int:booking_id>/bayar/', PaymentCreateView.as_view(), name='payment_create'),
]