from django.conf import settings
from django.db import models


class ServiceOrder(models.Model):
    SERVICE_CHOICES = [
        ('FOOD', 'Pesan Makanan & Minuman'),
        ('AMENITIES', 'Request Amenities'),
        ('EXTRA_BED', 'Request Extra Bed'),
        ('LAUNDRY', 'Laundry'),
        ('RECEPTION', 'Chat dengan Resepsionis'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Menunggu Diproses'),
        ('CONFIRMED', 'Dikonfirmasi'),
        ('DELIVERED', 'Diantar / Selesai'),
        ('CANCELLED', 'Dibatalkan'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='service_orders'
    )
    booking = models.ForeignKey(
        'reservations.Booking', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='service_orders',
    )
    service_type = models.CharField(max_length=20, choices=SERVICE_CHOICES, default='FOOD')
    detail = models.TextField(blank=True, help_text='Contoh: Nasi Goreng x1, Mie Goreng x2')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'service_orders'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_service_type_display()} - {self.user} ({self.status})'
