from django.contrib import admin
from .models import TemporaryRoom, PromoVoucher, Booking, Payment

admin.site.register(TemporaryRoom)
admin.site.register(PromoVoucher)
admin.site.register(Booking)
admin.site.register(Payment)